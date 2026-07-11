"""ValidationRunner — backend-agnostic check execution (spec §6).

Execution mechanics (OutcomeProjection): the raw rule result is projected
as a temporary column via with_columns — never a bare filter, so boolean
NULLs cannot vanish as filter-mask drops. Non-terminal ternary expressions
reach the backend as raw -1/0/1 sentinels because the relation visitor's
compile_expression() applies no booleanization; boolean expressions keep
their NULLs. The outcome column ('pass'|'fail'|'unknown') is derived from
the raw column, counts aggregate through the relation API on the source
backend, and only small results materialise to Polars.
"""
from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, Sequence

import polars as pl

from mountainash.expressions.core.expression_nodes import ScalarFunctionNode
from mountainash.validation.checks import VERDICT_PASSING, check_kind
from mountainash.validation.errors import UnknownCheckTypeError
from mountainash.validation.identity import RowIdentity, validate_keyed_identity
from mountainash.validation.result import (
    CheckSummary,
    ValidationResult,
    combine_failure_frames,
    interpolate_message,
    is_blocking,
    passes_from_summaries,
    summaries_frame,
)

if TYPE_CHECKING:
    from mountainash.relations import Relation

_RAW = "__ma_raw__"
_OUTCOME = "__ma_outcome__"
#: Diagnostic ordinal column (row_number tier) — assigned to the source
#: before any rule is evaluated; never used to join back to the source.
ROW_ORDINAL = "__ma_row_number__"

_ALL_OUTCOMES = frozenset({"pass", "fail", "unknown"})


def _is_non_terminal_ternary(expr: Any) -> bool:
    node = expr._node
    return isinstance(node, ScalarFunctionNode) and node.is_ternary_non_terminal


def _outcome_expr(expr: Any) -> Any:
    """Outcome column from the raw rule projection (spec §6.2 table)."""
    import mountainash as ma

    raw = ma.col(_RAW)
    if _is_non_terminal_ternary(expr):
        # raw sentinels: 1 -> pass, 0 -> unknown, -1 -> fail
        return (
            ma.when(raw.eq(ma.lit(1)))
            .then(ma.lit("pass"))
            .otherwise(
                ma.when(raw.eq(ma.lit(0)))
                .then(ma.lit("unknown"))
                .otherwise(ma.lit("fail"))
            )
        )
    # boolean context (incl. terminal ternary): True/False/NULL
    return (
        ma.when(raw.is_null())
        .then(ma.lit("unknown"))
        .otherwise(ma.when(raw).then(ma.lit("pass")).otherwise(ma.lit("fail")))
    )


class ValidationRunner:
    """Executes validation checks against relations, cross-backend."""

    def validate_relation(
        self,
        relation: "Relation | Any",
        checks: Sequence[Any],
        *,
        identity: RowIdentity | None = None,
        allow_imperfect_key: bool = False,
        context: dict[str, Any] | None = None,
        fail_fast: bool = False,
        failure_sample: int | None = None,
        backend: str | None = None,
        validator_name: str = "",
        datacontract_name: str | None = None,
    ) -> ValidationResult:
        from mountainash.relations import Relation
        from mountainash.relations import relation as as_relation

        rel = relation if isinstance(relation, Relation) else as_relation(relation)
        if backend is not None:
            # _compile_and_execute_with_visitor returns (result, visitor) —
            # unpack; wrapping the tuple would corrupt the run.
            native, _visitor = rel._compile_and_execute_with_visitor(backend=backend)
            rel = as_relation(native)

        identity = identity or RowIdentity("none")
        identity_diagnostics: dict[str, Any] = {}
        if identity.kind == "keyed":
            identity_diagnostics = validate_keyed_identity(
                rel, identity, allow_imperfect_key=allow_imperfect_key
            )
        elif identity.kind == "row_number":
            rel = rel.with_row_index(name=ROW_ORDINAL)

        summaries: list[CheckSummary] = []
        failure_frames: list[pl.DataFrame] = []
        for check in checks:
            kind = check_kind(check)  # raises UnknownCheckTypeError (declaration phase)
            executor = self._executor_for(kind)  # ditto
            summary, failures = self._guarded(executor, rel, check, kind, identity, failure_sample)
            summaries.append(summary)
            if failures.height:
                failure_frames.append(failures)
            if fail_fast and is_blocking(summary):
                break  # same definition passes_from_summaries penalises (spec §8:
                       # error always blocks; failed blocks only at blocking severity)

        return ValidationResult(
            passes=passes_from_summaries(summaries),
            validator_name=validator_name,
            datacontract_name=datacontract_name,
            context=dict(context or {}),
            check_summaries=summaries_frame(summaries),
            failure_cases=combine_failure_frames(failure_frames, identity),
            identity=identity,
            identity_diagnostics=identity_diagnostics,
        )

    # -- dispatch -----------------------------------------------------------

    def _executor_for(self, kind: str) -> Any:
        executors = {
            "row": self._run_row_rule,
            "scalar": self._run_scalar_rule,
        }
        try:
            return executors[kind]
        except KeyError:
            raise UnknownCheckTypeError(
                f"check kind {kind!r} has no executor"
            ) from None

    def _guarded(
        self, executor: Any, rel: "Relation", check: Any, kind: str,
        identity: RowIdentity, failure_sample: int | None,
    ) -> "tuple[CheckSummary, pl.DataFrame]":
        """Isolation (spec §6.5): execution exceptions become
        CheckSummary(status='error'); siblings keep running."""
        start = time.perf_counter()
        try:
            summary, failures = executor(rel, check, identity, failure_sample)
        except Exception as exc:  # noqa: BLE001 — isolation is the contract
            summary = CheckSummary(
                check_id=check.id,
                check_kind=kind,
                status="error",
                severity=getattr(check, "severity", "blocking"),
                error=f"{type(exc).__name__}: {exc}",
            )
            failures = pl.DataFrame()
        summary.elapsed = time.perf_counter() - start
        return summary, failures

    # -- RowRule ------------------------------------------------------------

    def _run_row_rule(
        self, rel: "Relation", check: Any, identity: RowIdentity,
        failure_sample: int | None,
    ) -> "tuple[CheckSummary, pl.DataFrame]":
        import mountainash as ma

        passing = VERDICT_PASSING[check.booleanizer or "t_is_true"]

        projected = rel.with_columns(check.expr.alias(_RAW)).with_columns(
            _outcome_expr(check.expr).alias(_OUTCOME)
        )

        counts_pl = (
            projected.group_by(_OUTCOME)
            .agg(ma.count_records().alias("__ma_n__"))
            .to_polars()
        )
        counts = dict(zip(counts_pl[_OUTCOME].to_list(), counts_pl["__ma_n__"].to_list()))
        pass_count = int(counts.get("pass", 0))
        fail_count = int(counts.get("fail", 0))
        unknown_count = int(counts.get("unknown", 0))
        total = pass_count + fail_count + unknown_count
        passing_count = sum(int(counts.get(o, 0)) for o in passing)

        if total == 0:
            status = "passed"  # vacuous (spec §6.2); emptiness is a ScalarRule concern
        elif check.mostly is None:
            status = "passed" if passing_count == total else "failed"
        else:
            status = "passed" if (passing_count / total) >= check.mostly else "failed"

        failures = pl.DataFrame()
        if total - passing_count > 0:
            failures = self._collect_row_failures(
                projected, check, identity, passing, failure_sample
            )

        summary = CheckSummary(
            check_id=check.id,
            check_kind="row",
            status=status,
            pass_count=pass_count,
            fail_count=fail_count,
            unknown_count=unknown_count,
            total_rows=total,
            mostly=check.mostly,
            severity=check.severity,
        )
        return summary, failures

    def _collect_row_failures(
        self, projected: "Relation", check: Any, identity: RowIdentity,
        passing: "frozenset[str]", failure_sample: int | None,
    ) -> pl.DataFrame:
        import mountainash as ma

        non_passing = sorted(_ALL_OUTCOMES - passing)
        failing = projected.filter(ma.col(_OUTCOME).is_in(non_passing))
        if failure_sample is not None:
            failing = failing.head(failure_sample)

        value_column = (
            check.fields[0] if check.fields and len(check.fields) == 1 else None
        )
        # spec §8: declared fields -> failing rows carry a `row` struct with the
        # fields' values (any identity tier; makes cross-column failures
        # self-describing without a source join)
        struct_fields = list(check.fields or [])
        interpolating = bool(check.error_message) and identity.kind == "keyed"
        interp_fields = list(struct_fields) if interpolating else []

        select_cols: list[str] = []
        if identity.kind == "keyed":
            select_cols.extend(identity.key_fields)
        elif identity.kind == "row_number":
            select_cols.append(ROW_ORDINAL)
        for name in struct_fields:
            if name not in select_cols:
                select_cols.append(name)
        if value_column and value_column not in select_cols:
            select_cols.append(value_column)

        fail_pl = failing.select(*select_cols, _OUTCOME).to_polars()

        out = fail_pl.rename({_OUTCOME: "outcome"})
        if identity.kind == "row_number":
            out = out.rename({ROW_ORDINAL: "row_number"})
        if value_column is not None:
            out = out.with_columns(pl.col(value_column).cast(pl.String).alias("value"))
        else:
            out = out.with_columns(pl.lit(None, dtype=pl.String).alias("value"))
        if interpolating:
            out = interpolate_message(out, check.error_message, interp_fields)
        else:
            out = out.with_columns(pl.lit(None, dtype=pl.String).alias("message"))
        out = out.with_columns(
            pl.lit(check.id).alias("check_id"),
            pl.lit("row").alias("check_kind"),
            pl.lit(value_column, dtype=pl.String).alias("column"),
        )
        if struct_fields:
            out = out.with_columns(
                pl.struct([pl.col(f) for f in struct_fields]).alias("row")
            )

        keep = ["check_id", "check_kind", "column", "outcome", "value", "message"]
        keep.extend(k for k in identity.key_fields if k in out.columns)
        if "row_number" in out.columns:
            keep.append("row_number")
        if "row" in out.columns:
            keep.append("row")
        return out.select(keep)

    # -- ScalarRule ---------------------------------------------------------

    def _run_scalar_rule(
        self, rel: "Relation", check: Any, identity: RowIdentity,
        failure_sample: int | None,
    ) -> "tuple[CheckSummary, pl.DataFrame]":
        value = rel._scalar_aggregate(check.expr)
        if value is None:
            status = "failed"  # NULL scalar -> unknown verdict; not-passing (spec §6.3)
            diagnostic = "null (unknown verdict)"
        else:
            status = "passed" if bool(value) else "failed"
            diagnostic = str(value)
        summary = CheckSummary(
            check_id=check.id, check_kind="scalar", status=status,
            severity=check.severity, diagnostic=diagnostic,
        )
        return summary, pl.DataFrame()
