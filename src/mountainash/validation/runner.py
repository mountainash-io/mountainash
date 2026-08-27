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

import functools
import operator
import time
from typing import TYPE_CHECKING, Any, Sequence

import polars as pl

from mountainash.core.transit import BoundaryKey, transit_call
from mountainash.expressions.core.expression_nodes import ScalarFunctionNode
from mountainash.validation.checks import VERDICT_PASSING, check_kind
from mountainash.validation.errors import IdentityInvalidError, UnknownCheckTypeError
from mountainash.validation.identity import RowIdentity, validate_keyed_identity
from mountainash.validation.result import (
    CheckSummary,
    DAGValidationResult,
    ValidationResult,
    combine_failure_frames,
    interpolate_message,
    is_blocking,
    passes_from_summaries,
    rows_as_struct_failures,
    summaries_frame,
)

if TYPE_CHECKING:
    from mountainash.relations import Relation
    from mountainash.validation.prepared import PreparedValidationInput

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
        fk_resolver: Any = None,
    ) -> ValidationResult:
        """Prepare *relation* exactly once, then run *checks* against it.

        Compiles the plan and materializes it with the dedicated
        ``VALIDATION_SOURCE`` purpose (spec section 6) inside one
        ``MaterializationScope``, owning it for the run's duration -- so
        every per-check executor below runs against the SAME materialized
        source instead of re-collecting the whole plan (including a
        full-contract conform) once per check (item 56).

        A plan-level failure here (most commonly a conform cast failure)
        must honour the same isolation contract as a per-check executor
        failure (spec section 6.5, ``_guarded``): it degrades to
        ``status="error"`` for every check and still returns a
        ``ValidationResult`` -- it must not raise out of the runner.
        ``check_kind`` is evaluated per check first (inside
        ``_validate_prepared_relation``), so a genuine declaration error
        (``UnknownCheckTypeError``) still raises, ahead of the data-phase
        failure.
        """
        from mountainash.relations.core.materialization import MaterializationScope
        from mountainash.validation.prepared import prepare_validation_input

        identity = identity or RowIdentity("none")
        scope = MaterializationScope()
        try:
            prepared = prepare_validation_input(relation, backend=backend, scope=scope)
        except Exception as exc:  # noqa: BLE001 — isolation is the contract
            scope.close()
            summaries = [
                self._error_summary(check, check_kind(check), exc) for check in checks
            ]
            return ValidationResult(
                passes=passes_from_summaries(summaries),
                validator_name=validator_name,
                datacontract_name=datacontract_name,
                context=dict(context or {}),
                check_summaries=summaries_frame(summaries),
                failure_cases=combine_failure_frames([], identity),
                identity=identity,
                identity_diagnostics={},
            )
        try:
            return self._validate_prepared_relation(
                prepared,
                checks,
                identity=identity,
                allow_imperfect_key=allow_imperfect_key,
                context=context,
                fail_fast=fail_fast,
                failure_sample=failure_sample,
                validator_name=validator_name,
                datacontract_name=datacontract_name,
                fk_resolver=fk_resolver,
            )
        finally:
            scope.close()

    def _validate_prepared_relation(
        self,
        prepared: "PreparedValidationInput",
        checks: Sequence[Any],
        *,
        identity: RowIdentity,
        allow_imperfect_key: bool,
        context: dict[str, Any] | None,
        fail_fast: bool,
        failure_sample: int | None,
        validator_name: str,
        datacontract_name: str | None,
        fk_resolver: Any,
    ) -> ValidationResult:
        """Run *checks* against an already-prepared, already-materialized
        source (spec section 6). Rule queries stay native on
        ``prepared.relation``; only small counts and selected failure rows
        convert to Polars per check (spec section 6.2's outcome model)."""
        rel = prepared.relation
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
            executor = self._executor_for(kind, fk_resolver)  # ditto
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

    def _executor_for(self, kind: str, fk_resolver: Any = None) -> Any:
        executors = {
            "row": self._run_row_rule,
            "scalar": self._run_scalar_rule,
            "relation": self._run_relation_rule,
            "foreign_key": functools.partial(
                self._run_foreign_key_rule, fk_resolver=fk_resolver
            ),
        }
        try:
            return executors[kind]
        except KeyError:
            raise UnknownCheckTypeError(
                f"check kind {kind!r} has no executor"
            ) from None

    @staticmethod
    def _error_summary(check: Any, kind: "str | None", exc: BaseException) -> CheckSummary:
        """Isolation summary (spec §6.5): an execution exception — per check
        or, up front, the one-shot materialisation — becomes status='error'."""
        return CheckSummary(
            check_id=check.id,
            check_kind=kind,
            status="error",
            severity=getattr(check, "severity", "blocking"),
            error=f"{type(exc).__name__}: {exc}",
        )

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
            summary = self._error_summary(check, kind, exc)
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

        chain = projected.group_by(_OUTCOME).agg(ma.count_records().alias("__ma_n__"))
        counts_pl = transit_call(BoundaryKey.RELATION_TO_POLARS_TERMINAL, chain.to_polars)
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

        fail_pl = transit_call(
            BoundaryKey.RELATION_TO_POLARS_TERMINAL, failing.select(*select_cols, _OUTCOME).to_polars
        )

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

    # -- RelationRule ---------------------------------------------------------

    def _run_relation_rule(
        self, rel: "Relation", check: Any, identity: RowIdentity,
        failure_sample: int | None,
    ) -> "tuple[CheckSummary, pl.DataFrame]":
        failing = check.plan(rel)
        fail_count = failing.count_rows()
        status = "passed" if fail_count == 0 else "failed"

        failures = pl.DataFrame()
        if fail_count:
            sampled = failing.head(failure_sample) if failure_sample is not None else failing
            failures = rows_as_struct_failures(
                transit_call(BoundaryKey.RELATION_TO_POLARS_TERMINAL, sampled.to_polars),
                check_id=check.id, check_kind="relation",
            )

        summary = CheckSummary(
            check_id=check.id, check_kind="relation", status=status,
            severity=check.severity, fail_count=fail_count,
        )
        return summary, failures

    # -- ForeignKeyRule -------------------------------------------------------

    def _run_foreign_key_rule(
        self, rel: "Relation", check: Any, identity: RowIdentity,
        failure_sample: int | None, *, fk_resolver: Any = None,
    ) -> "tuple[CheckSummary, pl.DataFrame]":
        import mountainash as ma

        if fk_resolver is None:
            # Captured by the isolation guard -> CheckSummary(status="error"),
            # per spec §10: FK problems are error summaries, never raised mid-run.
            raise RuntimeError(
                f"ForeignKeyRule {check.id!r} requires DAG context "
                "(no resolver for child/parent names)"
            )

        child = fk_resolver(check.child)
        parent = fk_resolver(check.parent)

        target = child
        if check.exclude_null_child:
            # SQL MATCH SIMPLE: any-null component excludes the row.
            all_non_null = functools.reduce(
                operator.and_, (ma.col(f).is_not_null() for f in check.child_fields)
            )
            target = child.filter(all_non_null)

        orphans = target.join(
            parent.select(*check.parent_fields).unique(),
            left_on=check.child_fields,
            right_on=check.parent_fields,
            how="anti",
        )
        orphan_count = orphans.count_rows()
        status = "passed" if orphan_count == 0 else "failed"

        failures = pl.DataFrame()
        if orphan_count:
            sampled = orphans.head(failure_sample) if failure_sample is not None else orphans
            failures = rows_as_struct_failures(
                transit_call(BoundaryKey.RELATION_TO_POLARS_TERMINAL, sampled.to_polars),
                check_id=check.id, check_kind="foreign_key",
            )

        summary = CheckSummary(
            check_id=check.id,
            check_kind="foreign_key",
            status=status,
            fail_count=orphan_count,
            severity=check.severity,
            diagnostic=str(orphan_count),
        )
        return summary, failures

    # -- DAG orchestration ----------------------------------------------------

    def validate_dag(
        self,
        dag: Any,
        checks_by_resource: "dict[str, list[Any]]",
        *,
        identity_by_resource: "dict[str, RowIdentity] | None" = None,
        context: "dict[str, Any] | None" = None,
        fail_fast: bool = False,
        failure_sample: int | None = None,
        backend: str | None = None,
        fk_error_summaries: "list[CheckSummary] | None" = None,
        allow_imperfect_key: bool = False,
    ) -> "DAGValidationResult":
        """Validate every resource in *checks_by_resource*, then every
        foreign-key rule, through ONE shared
        :class:`~mountainash.relations.dag.materialization.DAGMaterializationSession`
        (spec section 10/18): a resource referenced as both a planned
        (spec'd) resource and a dependency or foreign-key parent of
        another compiles exactly once, shared across every consumer.
        """
        from mountainash.relations import relation as as_relation
        from mountainash.relations.dag.materialization import DAGMaterializationSession
        from mountainash.validation.checks import ForeignKeyRule
        from mountainash.validation.prepared import prepare_validation_input_from_session

        session = DAGMaterializationSession(dag, backend=backend, isolate_failures=True)
        prepared_by_name: "dict[str, PreparedValidationInput]" = {}

        def _prepare(name: str) -> "PreparedValidationInput":
            if name not in prepared_by_name:
                prepared_by_name[name] = prepare_validation_input_from_session(session, name)
            return prepared_by_name[name]

        def _resolver(name: str) -> Any:
            # A planned (spec'd) resource reuses its own PreparedValidationInput's
            # relation; an execution-only dependency (Unit D's "identity
            # transform") is compiled plainly through the session -- no
            # PreparedValidationInput wrapper, since it was never itself
            # validated.
            prepared = prepared_by_name.get(name)
            if prepared is not None:
                return prepared.relation
            native, _visitor = session.compile_registered(name)
            return as_relation(native.value)

        identity_by_resource = identity_by_resource or {}
        results: dict[str, ValidationResult] = {}
        fk_rules: list[Any] = []

        try:
            for name, checks in checks_by_resource.items():
                intra = [c for c in checks if not isinstance(c, ForeignKeyRule)]
                fk_rules.extend(c for c in checks if isinstance(c, ForeignKeyRule))
                resource_identity = identity_by_resource.get(name) or RowIdentity("none")
                try:
                    prepared = _prepare(name)
                except Exception as exc:  # noqa: BLE001 — isolation is the contract
                    # A resource's own preparation failure (most commonly a
                    # conform cast failure) isolates to that resource's own
                    # failing result, same as validate_relation()'s
                    # equivalent plan-level isolation (Task 6) — it must not
                    # abort unrelated resources in this batch.
                    summaries = [
                        self._error_summary(c, check_kind(c), exc) for c in checks
                    ]
                    result = ValidationResult(
                        passes=passes_from_summaries(summaries),
                        validator_name=name,
                        datacontract_name=None,
                        context=dict(context or {}),
                        check_summaries=summaries_frame(summaries),
                        failure_cases=combine_failure_frames([], resource_identity),
                        identity=resource_identity,
                        identity_diagnostics={},
                    )
                    results[name] = result
                    if fail_fast and not result.passes:
                        return DAGValidationResult(
                            passes=False,
                            results=results,
                            fk_result=ValidationResult(
                                passes=True, validator_name="__fk__", context=dict(context or {})
                            ),
                        )
                    continue

                try:
                    result = self._validate_prepared_relation(
                        prepared,
                        intra,
                        identity=resource_identity,
                        allow_imperfect_key=allow_imperfect_key,
                        context=context,
                        fail_fast=fail_fast,
                        failure_sample=failure_sample,
                        validator_name=name,
                        datacontract_name=None,
                        fk_resolver=_resolver,
                    )
                except IdentityInvalidError as exc:
                    # spec item 8j §3.2: a resource's invalid keyed identity never
                    # aborts the batch — isolate it into that resource's own failing
                    # result, same as a preparation failure above. "__identity__"
                    # mirrors the existing "__fk__" synthetic-result naming.
                    summary = CheckSummary(
                        check_id="__identity__",
                        check_kind=None,
                        status="error",
                        severity="blocking",
                        error=f"{type(exc).__name__}: {exc}",
                    )
                    result = ValidationResult(
                        passes=False,
                        validator_name=name,
                        datacontract_name=None,
                        context=dict(context or {}),
                        check_summaries=summaries_frame([summary]),
                        failure_cases=combine_failure_frames([], resource_identity),
                        identity=resource_identity,
                        identity_diagnostics={},
                    )
                results[name] = result
                if fail_fast and not result.passes:
                    return DAGValidationResult(
                        passes=False,
                        results=results,
                        fk_result=ValidationResult(
                            passes=True, validator_name="__fk__", context=dict(context or {})
                        ),
                    )


            identity = RowIdentity("none")
            fk_summaries: list[CheckSummary] = list(fk_error_summaries or [])
            fk_frames: list[pl.DataFrame] = []
            for fk in fk_rules:
                summary, failures = self._guarded(
                    functools.partial(self._run_foreign_key_rule, fk_resolver=_resolver),
                    None, fk, "foreign_key", identity, failure_sample,
                )
                fk_summaries.append(summary)
                if failures.height:
                    fk_frames.append(failures)
                if fail_fast and is_blocking(summary):
                    break  # same definition passes_from_summaries penalises (spec §8)

            fk_result = ValidationResult(
                passes=passes_from_summaries(fk_summaries),
                validator_name="__fk__",
                context=dict(context or {}),
                check_summaries=summaries_frame(fk_summaries),
                failure_cases=combine_failure_frames(fk_frames, identity),
                identity=identity,
            )
            passes = all(r.passes for r in results.values()) and fk_result.passes
            return DAGValidationResult(passes=passes, results=results, fk_result=fk_result)
        finally:
            session.close(release_owned=True)
