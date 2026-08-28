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
import time
from typing import TYPE_CHECKING, Any, Mapping, Sequence

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
        checks: Sequence[Any] = (),
        *,
        plan: Any = None,
        apply_value_transforms: bool = True,
        conform_contract: "str | Mapping[str, str] | None" = None,
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
        from mountainash.relations import Relation
        from mountainash.relations import relation as as_relation
        from mountainash.relations.core.materialization import MaterializationScope
        from mountainash.validation.prepared import prepare_validation_input

        rel = relation if isinstance(relation, Relation) else as_relation(relation)
        if plan is not None:
            from mountainash.validation.fk import build_standalone_fk_checks
            from mountainash.validation.plan import thaw_typespec

            rel = rel.conform(
                thaw_typespec(plan),
                contract=conform_contract,
                apply_value_transforms=apply_value_transforms,
            )
            standalone_rules = (
                build_standalone_fk_checks(plan, resource_name=validator_name or "__standalone__")
                if fk_resolver is None
                else ()
            )
            checks = (*plan.checks, *checks, *standalone_rules)
            if fk_resolver is None:
                def fk_resolver(_name: str) -> Any:
                    return prepared

        identity = identity or RowIdentity("none")
        scope = MaterializationScope()
        try:
            prepared = prepare_validation_input(rel, backend=backend, scope=scope)
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
        from mountainash.relations.core.logical_snapshot import resolved_snapshot_to_polars

        materialized_source = resolved_snapshot_to_polars(prepared.logical_snapshot)
        self._materialized_value_frame = materialized_source
        self._logical_snapshot = prepared.logical_snapshot
        self._structured_field_plans = prepared.structured_field_plans
        identity_diagnostics: dict[str, Any] = {}
        if identity.kind == "keyed":
            identity_diagnostics = validate_keyed_identity(
                prepared.logical_snapshot, identity, allow_imperfect_key=allow_imperfect_key
            )
        elif identity.kind == "row_number":
            rel = rel.with_row_index(name=ROW_ORDINAL)
            if self._materialized_value_frame is not None:
                self._materialized_value_frame = self._materialized_value_frame.with_row_index(
                    name=ROW_ORDINAL
                )

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
            _materialized_source=materialized_source,
        )

    # -- dispatch -----------------------------------------------------------

    def _executor_for(self, kind: str, fk_resolver: Any = None) -> Any:
        executors = {
            "row": self._run_row_rule,
            "scalar": self._run_scalar_rule,
            "relation": self._run_relation_rule,
            "value": self._run_value_rule,
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
        if (
            check.metadata.get("standard_constraint") == "required"
            and check.metadata.get("field") in self._structured_field_plans
        ):
            return self._run_transported_required_rule(check, identity, failure_sample)

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

    def _run_transported_required_rule(
        self, check: Any, identity: RowIdentity, failure_sample: int | None,
    ) -> "tuple[CheckSummary, pl.DataFrame]":
        """Compute a ``required`` outcome from the resolved logical snapshot
        for a transport-plan-covered field (spec Task 6 step 7): the
        physical value can be a non-null malformed string that still
        decodes to a logical null (``discard_value``) -- a native
        ``.is_not_null()`` expression on the physical column would see it
        as present and pass incorrectly. Row universe and ordinals match
        every other structured-aware check: the shared discard-row keep
        set already applied when the logical snapshot was resolved."""
        field = check.metadata["field"]
        frame = self._materialized_value_frame
        values = self._logical_snapshot.logical_columns[field]
        failed_mask = [value is None for value in values]
        total = len(values)
        fail_count = sum(failed_mask)
        pass_count = total - fail_count
        status = (
            "passed"
            if total == 0
            or (
                pass_count / total >= check.mostly
                if check.mostly is not None
                else fail_count == 0
            )
            else "failed"
        )
        failures = pl.DataFrame()
        if fail_count and frame is not None:
            failures = self._collect_transported_required_failures(
                frame, failed_mask, check, identity, failure_sample
            )
        summary = CheckSummary(
            check_id=check.id,
            check_kind="row",
            status=status,
            pass_count=pass_count,
            fail_count=fail_count,
            unknown_count=0,
            total_rows=total,
            mostly=check.mostly,
            severity=check.severity,
        )
        return summary, failures

    @staticmethod
    def _collect_transported_required_failures(
        frame: pl.DataFrame,
        failed_mask: "list[bool]",
        check: Any,
        identity: RowIdentity,
        failure_sample: int | None,
    ) -> pl.DataFrame:
        field = check.metadata["field"]
        failing = frame.filter(pl.Series(failed_mask))
        if failure_sample is not None:
            failing = failing.head(failure_sample)

        struct_fields = list(check.fields or [])
        select_cols: list[str] = []
        if identity.kind == "keyed":
            select_cols.extend(identity.key_fields)
        elif identity.kind == "row_number":
            select_cols.append(ROW_ORDINAL)
        for name in struct_fields:
            if name not in select_cols:
                select_cols.append(name)
        if field not in select_cols:
            select_cols.append(field)

        out = failing.select(select_cols)
        if identity.kind == "row_number":
            out = out.rename({ROW_ORDINAL: "row_number"})
        out = out.with_columns(
            pl.lit("fail").alias("outcome"),
            pl.lit(None, dtype=pl.String).alias("value"),
            pl.lit(None, dtype=pl.String).alias("message"),
            pl.lit(check.id).alias("check_id"),
            pl.lit("row").alias("check_kind"),
            pl.lit(field, dtype=pl.String).alias("column"),
        )
        if struct_fields:
            from mountainash.validation.result import _struct_safe_columns

            row_struct = _struct_safe_columns(out.select(struct_fields)).select(
                pl.struct(pl.all()).alias("row")
            )
            out = out.with_columns(row_struct.to_series())
        keep = ["check_id", "check_kind", "column", "outcome", "value", "message"]
        keep.extend(k for k in identity.key_fields if k in out.columns)
        if "row_number" in out.columns:
            keep.append("row_number")
        if "row" in out.columns:
            keep.append("row")
        return out.select(keep)

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

    # -- ValueRule ----------------------------------------------------------

    def _run_value_rule(
        self,
        rel: "Relation",
        check: Any,
        identity: RowIdentity,
        failure_sample: int | None,
    ) -> "tuple[CheckSummary, pl.DataFrame]":
        from mountainash.validation.result import rows_as_struct_failures
        from mountainash.validation.value import (
            INVALID_VALUE,
            VALUE_RULE_REGISTRY,
            structured_value_diagnostics,
        )

        if not check.fields:
            raise ValueError(f"{check.validator.name.lower()} rules require one or more fields")
        frame = (
            self._materialized_value_frame
            if self._materialized_value_frame is not None
            else rel.to_polars()
        )
        missing_fields = set(check.fields) - set(frame.columns)
        if missing_fields:
            raise ValueError(
                f"declared fields {sorted(missing_fields)!r} are absent from materialized data"
            )
        entry = VALUE_RULE_REGISTRY[check.validator]
        values: list[Any] | None = None
        diagnostics_by_source: list[Sequence[Any]] | None = None
        if check.validator.name == "UNIQUE":
            outcomes = self._unique_value_outcomes(frame, check.fields)
        elif len(check.fields) == 1:
            values = frame[check.fields[0]].to_list()
            if check.validator.name in {
                "JSON_SCHEMA",
                "GEOJSON",
                "GEOJSON_WINDING",
                "TOPOJSON",
            }:
                diagnostics_by_source = [
                    structured_value_diagnostics(check.validator, value, check.options)
                    for value in values
                ]
                outcomes = [
                    None
                    if value is INVALID_VALUE
                    else True
                    if value is None
                    else not diagnostics
                    for value, diagnostics in zip(
                        values, diagnostics_by_source, strict=True
                    )
                ]
            else:
                outcomes = [entry.execute(value, check.options) for value in values]
        else:
            raise ValueError(f"{check.validator.name.lower()} rules require exactly one field")
        failed_indices = [index for index, outcome in enumerate(outcomes) if outcome is False]
        failed = [outcome is False for outcome in outcomes]
        diagnostics = (
            [
                (
                    diagnostics_by_source[index]
                    if diagnostics_by_source is not None
                    else structured_value_diagnostics(
                        check.validator, values[index], check.options
                    )
                )
                for index in failed_indices
            ]
            if values is not None
            else [()] * len(failed_indices)
        )
        failures = frame.filter(pl.Series(failed))
        if failure_sample is not None:
            failures = failures.head(failure_sample)
            diagnostics = diagnostics[:failure_sample]
        failure_frame = rows_as_struct_failures(
            failures,
            check_id=check.id,
            check_kind="value",
        )
        if failure_frame.height and identity.kind == "keyed":
            failure_frame = failure_frame.with_columns(
                [pl.Series(name, failures[name]) for name in identity.key_fields]
            )
        elif failure_frame.height and identity.kind == "row_number":
            failure_frame = failure_frame.with_columns(
                pl.Series("row_number", failures[ROW_ORDINAL])
            )
        if failure_frame.height:
            failure_frame = self._attach_value_diagnostics(failure_frame, diagnostics)
        fail_count = sum(failed)
        unknown_count = sum(outcome is None for outcome in outcomes)
        total = frame.height
        pass_count = total - fail_count - unknown_count
        passing_count = pass_count + unknown_count
        status = (
            "passed"
            if total == 0
            or (
                passing_count / total >= check.mostly
                if check.mostly is not None
                else fail_count == 0 and unknown_count == 0
            )
            else "failed"
        )
        return (
            CheckSummary(
                check_id=check.id,
                check_kind="value",
                status=status,
                pass_count=pass_count,
                fail_count=fail_count,
                unknown_count=unknown_count,
                total_rows=total,
                mostly=check.mostly,
                severity=check.severity,
            ),
            failure_frame,
        )

    @staticmethod
    def _attach_value_diagnostics(
        failure_frame: pl.DataFrame, diagnostics: Sequence[Sequence[Any]]
    ) -> pl.DataFrame:
        """Expand nested diagnostics without changing per-source row counts."""
        records: list[dict[str, Any]] = []
        for record, row_diagnostics in zip(
            failure_frame.to_dicts(), diagnostics, strict=True
        ):
            if not row_diagnostics:
                records.append(record)
                continue
            for diagnostic in row_diagnostics:
                diagnostic_record = dict(record)
                diagnostic_record.update(
                    instance_path=diagnostic.instance_path,
                    schema_path=diagnostic.schema_path,
                    validator=diagnostic.validator,
                    message=diagnostic.message,
                )
                records.append(diagnostic_record)
        return pl.DataFrame(records, schema=failure_frame.schema)

    @staticmethod
    def _unique_value_outcomes(frame: pl.DataFrame, fields: Sequence[str]) -> list[bool | None]:
        """Return one logical uniqueness outcome per source row.

        Null tuples pass under Frictionless field-unique semantics. A repeated
        non-null key marks every member of that duplicate group as failed.
        """
        from mountainash.validation.value import INVALID_VALUE, canonical_value_key

        outcomes: list[bool | None] = [True] * frame.height
        first_index_by_key: dict[tuple[Any, ...], int] = {}
        values_by_field = [frame[field].to_list() for field in fields]
        for row_index, values in enumerate(zip(*values_by_field, strict=True)):
            if any(value is INVALID_VALUE for value in values):
                outcomes[row_index] = None
                continue
            if any(value is None for value in values):
                continue
            key = tuple(canonical_value_key(value) for value in values)
            first_index = first_index_by_key.get(key)
            if first_index is None:
                first_index_by_key[key] = row_index
            else:
                outcomes[first_index] = False
                outcomes[row_index] = False
        return outcomes

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
        """Compare canonical logical keys (spec 15.2, Task 9) -- never a
        backend join. A JSON-text/opaque carrier's raw bytes cannot define
        logical equality (whitespace, object-name order); every foreign
        key uses the same `canonical_value_key()` algebra as identity and
        uniqueness, over each side's prepared logical snapshot.
        """
        from mountainash.relations.core.logical_snapshot import resolved_snapshot_to_polars
        from mountainash.validation.fk import _canonical_key_rows

        if fk_resolver is None:
            # Captured by the isolation guard -> CheckSummary(status="error"),
            # per spec §10: FK problems are error summaries, never raised mid-run.
            raise RuntimeError(
                f"ForeignKeyRule {check.id!r} requires DAG context "
                "(no resolver for child/parent names)"
            )

        child_prepared = fk_resolver(check.child)
        parent_prepared = fk_resolver(check.parent)

        child_rows = _canonical_key_rows(child_prepared, check.child_fields, child=True)
        parent_rows = _canonical_key_rows(parent_prepared, check.parent_fields, child=False)
        parent_keys = {row.key for row in parent_rows.rows if row.outcome == "candidate"}

        failing_ordinals: list[int] = []
        unknown_count = 0
        for row in child_rows.rows:
            if row.outcome == "excluded_null":
                # SQL MATCH SIMPLE (default): any-null component excludes
                # the row from evaluation entirely. Disabled: a null
                # component can never truthfully equal a parent value
                # (three-valued NULL semantics), so it is a guaranteed
                # orphan, not an unknown.
                if not check.exclude_null_child:
                    failing_ordinals.append(row.ordinal)
                continue
            if row.outcome == "unknown":
                unknown_count += 1
                continue
            if row.key not in parent_keys:
                failing_ordinals.append(row.ordinal)

        fail_count = len(failing_ordinals)
        status = "passed" if fail_count == 0 else "failed"

        failures = pl.DataFrame()
        if fail_count:
            failing_set = frozenset(failing_ordinals)
            child_frame = resolved_snapshot_to_polars(child_prepared.logical_snapshot)
            mask = [o in failing_set for o in child_prepared.logical_snapshot.keep_ordinals]
            orphans = child_frame.filter(pl.Series(mask))
            if failure_sample is not None:
                orphans = orphans.head(failure_sample)
            failures = rows_as_struct_failures(
                orphans, check_id=check.id, check_kind="foreign_key",
            )

        summary = CheckSummary(
            check_id=check.id,
            check_kind="foreign_key",
            status=status,
            fail_count=fail_count,
            unknown_count=unknown_count,
            total_rows=len(child_rows.rows),
            severity=check.severity,
            diagnostic=str(fail_count),
        )
        return summary, failures

    # -- DAG orchestration ----------------------------------------------------

    def validate_dag(
        self,
        dag: Any,
        checks_by_resource: "dict[str, list[Any]]",
        *,
        identity_by_resource: "dict[str, RowIdentity] | None" = None,
        plans_by_resource: "dict[str, Any] | None" = None,
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
        from mountainash.relations.dag.materialization import (
            DAGMaterializationSession,
            SessionMode,
        )
        from mountainash.relations.dag.validation_context import DAGValidationContext
        from mountainash.validation.checks import ForeignKeyRule
        from mountainash.validation.plan import thaw_typespec

        identity_by_resource = identity_by_resource or {}
        plans_by_resource = plans_by_resource or {}

        def _plan_transform(plan: Any) -> Any:
            def transform(rel: Any) -> Any:
                return rel.conform(thaw_typespec(plan))

            return transform

        session = DAGMaterializationSession(
            dag,
            backend=backend,
            isolate_failures=True,
            node_transforms={
                name: _plan_transform(plan) for name, plan in plans_by_resource.items()
            },
            mode=SessionMode.VALIDATION,
        )
        validation_context = DAGValidationContext(session)

        def _resolver(name: str) -> Any:
            # Task 9: the FK resolver needs the full PreparedValidationInput
            # (its logical snapshot) for canonical key comparison, never a
            # backend join -- `context.prepare()` works for any
            # DAG-registered name, whether or not it also has its own
            # declared checks in this run.
            return validation_context.prepare(name)

        results: dict[str, ValidationResult] = {}
        fk_rules: list[Any] = []

        try:
            for name, checks in checks_by_resource.items():
                plan = plans_by_resource.get(name)
                local_checks = [
                    *(plan.checks if plan is not None else ()),
                    *checks,
                ]
                intra = [c for c in local_checks if not isinstance(c, ForeignKeyRule)]
                fk_rules.extend(c for c in local_checks if isinstance(c, ForeignKeyRule))
                resource_identity = identity_by_resource.get(name) or RowIdentity("none")
                try:
                    prepared = validation_context.prepare(name)
                except Exception as exc:  # noqa: BLE001 — isolation is the contract
                    # A resource's own preparation failure (most commonly a
                    # conform cast failure) isolates to that resource's own
                    # failing result, same as validate_relation()'s
                    # equivalent plan-level isolation (Task 6) — it must not
                    # abort unrelated resources in this batch.
                    summaries = [
                        self._error_summary(c, check_kind(c), exc) for c in local_checks
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
