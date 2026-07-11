"""Result model: CheckSummary, ValidationResult, DAGValidationResult and the
failure-case schema (spec §8). Designed fresh — NOT Pandera's five columns.

Check *execution* is cross-backend; result *containers* standardise on
Polars like the rest of the reporting stack.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import polars as pl

from mountainash.validation.checks import SEVERITIES
from mountainash.validation.identity import RowIdentity

CHECK_SUMMARY_SCHEMA: dict[str, Any] = {
    "check_id": pl.String,
    "check_kind": pl.String,
    "status": pl.String,
    "pass_count": pl.Int64,
    "fail_count": pl.Int64,
    "unknown_count": pl.Int64,
    "total_rows": pl.Int64,
    "mostly": pl.Float64,
    "severity": pl.String,  # blocking | warning (spec §8 third amendment)
    "diagnostic": pl.String,
    "error": pl.String,
    "elapsed": pl.Float64,
}

#: Failure-case columns before identity columns are appended.
FAILURE_CASE_BASE_SCHEMA: dict[str, Any] = {
    "check_id": pl.String,
    "check_kind": pl.String,
    "column": pl.String,
    "outcome": pl.String,  # fail | unknown
    "value": pl.String,
    "message": pl.String,
}


def failure_case_schema(identity: RowIdentity) -> dict[str, Any]:
    """The declared failure-case schema for this identity tier.

    Key-field dtypes are pl.Null in the *empty* frame (their native dtypes
    are only knowable from data); `row` is pl.Null until a relation/FK check
    contributes struct rows — combine_failure_frames relaxes dtypes.
    """
    schema: dict[str, Any] = dict(FAILURE_CASE_BASE_SCHEMA)
    for key in identity.key_fields:
        schema[key] = pl.Null
    schema["row_number"] = pl.Int64  # always present; null outside the row_number tier
    schema["row"] = pl.Null          # struct: relation/FK failing source row, or the
                                     # declared `fields` values for row rules (spec §8)
    return schema


#: Closed status vocabulary (spec §8) — validated at construction so a typo'd
#: status can never be silently non-blocking. `failed`/`error` are the two
#: potentially-blocking statuses; is_blocking() composes them with severity.
VALID_STATUSES = frozenset({"passed", "failed", "error", "skipped"})
BLOCKING_STATUSES = frozenset({"failed", "error"})
# SEVERITIES imports from mountainash.validation.checks at the top of this
# file — one definition (spec §5); checks.py has no import back into result.py


@dataclass
class CheckSummary:
    """One check's execution record (one row of ValidationResult.check_summaries)."""

    check_id: str
    check_kind: "str | None"        # row | scalar | relation | foreign_key; None on skipped summaries
    status: str                     # passed | failed | error | skipped
    pass_count: int | None = None
    fail_count: int | None = None
    unknown_count: int | None = None
    total_rows: int | None = None
    mostly: float | None = None
    severity: str = "blocking"      # blocking | warning; carried from the check declaration
    diagnostic: str | None = None
    error: str | None = None
    elapsed: float = 0.0

    def __post_init__(self) -> None:
        if self.status not in VALID_STATUSES:
            raise ValueError(
                f"CheckSummary status {self.status!r} not in {sorted(VALID_STATUSES)}"
            )
        if self.severity not in SEVERITIES:
            raise ValueError(
                f"CheckSummary severity {self.severity!r} not in {sorted(SEVERITIES)}"
            )


def is_blocking(summary: "CheckSummary") -> bool:
    """Single owner of blocking semantics (spec §8 third amendment).

    An errored check always blocks — a check that could not execute is an
    engineering failure, not an advisory outcome. A failed check blocks only
    at "blocking" severity; a failed warning stays status="failed" (audit
    output truthful) without blocking. Consumed by passes_from_summaries(),
    the runner's fail_fast, and the processor's passed()/passed_for_rule().
    """
    if summary.status == "error":
        return True
    return summary.status == "failed" and summary.severity == "blocking"


def summaries_frame(summaries: "list[CheckSummary]") -> pl.DataFrame:
    if not summaries:
        return pl.DataFrame(schema=CHECK_SUMMARY_SCHEMA)
    rows = [
        {name: getattr(s, name) for name in CHECK_SUMMARY_SCHEMA}
        for s in summaries
    ]
    return pl.DataFrame(rows, schema=CHECK_SUMMARY_SCHEMA)


def empty_failure_frame(identity: RowIdentity) -> pl.DataFrame:
    return pl.DataFrame(schema=failure_case_schema(identity))


def _unify_row_structs(frames: "list[pl.DataFrame]") -> "list[pl.DataFrame]":
    """Normalise heterogeneous `row` structs to their field union (spec §8).

    Different checks contribute structs with different field sets; bare
    diagonal concat of mismatched struct dtypes is undefined behaviour we do
    not rely on. Every struct-bearing frame is rewritten to the union struct
    (missing fields null, first-seen dtype per name); a dtype conflict on a
    shared name is left to the relaxed-supertype concat that follows.
    """
    union: "dict[str, pl.DataType]" = {}
    for frame in frames:
        dtype = frame.schema.get("row")
        if isinstance(dtype, pl.Struct):
            for fld in dtype.fields:
                union.setdefault(fld.name, fld.dtype)
    if not union:
        return frames

    normalised: "list[pl.DataFrame]" = []
    for frame in frames:
        dtype = frame.schema.get("row")
        if not isinstance(dtype, pl.Struct):
            normalised.append(frame)
            continue
        present = {fld.name for fld in dtype.fields}
        frame = frame.with_columns(
            pl.struct(
                [
                    (
                        pl.col("row").struct.field(name)
                        if name in present
                        else pl.lit(None, dtype=field_dtype)
                    ).alias(name)
                    for name, field_dtype in union.items()
                ]
            ).alias("row")
        )
        normalised.append(frame)
    return normalised


def combine_failure_frames(
    frames: "list[pl.DataFrame]", identity: RowIdentity
) -> pl.DataFrame:
    """Combine per-check failure frames; always returns the declared schema
    (empty typed frame when nothing failed). `row` structs are normalised to
    their field union first (spec §8); diagonal_relaxed then reconciles
    key-field dtypes and any remaining supertype differences."""
    non_empty = [f for f in frames if f.height > 0]
    if not non_empty:
        return empty_failure_frame(identity)
    non_empty = _unify_row_structs(non_empty)
    combined = pl.concat(
        [empty_failure_frame(identity), *non_empty], how="diagonal_relaxed"
    )
    ordered = list(failure_case_schema(identity))
    return combined.select(ordered)


def interpolate_message(
    frame: pl.DataFrame, template: str, fields: "list[str]"
) -> pl.DataFrame:
    """Add a `message` column: `template` with {field} placeholders replaced
    by each row's values (keyed-tier capability)."""
    # Seed at frame length (not pl.lit, which is length-1): str.replace does not
    # broadcast a length-1 subject against a length-N replacement expression
    # (Polars 1.42 raises), so the running message must already be column-length.
    message = pl.repeat(template, pl.len(), dtype=pl.String)
    for name in fields:
        if name not in frame.columns:
            continue
        message = message.str.replace(
            "{" + name + "}", pl.col(name).cast(pl.String), literal=True
        )
    return frame.with_columns(message.alias("message"))


def passes_from_summaries(summaries: "list[CheckSummary]") -> bool:
    """Single owner of the pass semantics (spec §8): a run passes when no
    summary is blocking per is_blocking() — 'error' always blocks; 'failed'
    blocks only at 'blocking' severity. 'skipped' (context-excluded, spec
    §9.6) and failed warnings never block — visibility, not a verdict. The
    runner's fail_fast stop condition uses the same is_blocking(): one
    definition, two consumers."""
    return not any(is_blocking(s) for s in summaries)


def _empty_summaries() -> pl.DataFrame:
    return pl.DataFrame(schema=CHECK_SUMMARY_SCHEMA)


def _empty_failures() -> pl.DataFrame:
    return empty_failure_frame(RowIdentity("none"))


@dataclass
class ValidationResult:
    """Outcome of a validation run (spec §8)."""

    passes: bool
    validator_name: str
    datacontract_name: str | None = None
    context: dict[str, Any] = field(default_factory=dict)
    check_summaries: pl.DataFrame = field(default_factory=_empty_summaries)
    failure_cases: pl.DataFrame = field(default_factory=_empty_failures)
    identity: RowIdentity = RowIdentity("none")
    identity_diagnostics: dict[str, Any] = field(default_factory=dict)
    diagnostics: dict[str, Any] = field(default_factory=dict)
    processor: Any = None  # ValidationResultProcessor; typed Any (dependency direction)

    @property
    def key_fields(self) -> "tuple[str, ...]":
        return self.identity.key_fields


@dataclass
class DAGValidationResult:
    """Outcome of a DAG validation run: per-resource results + FK phase."""

    passes: bool
    results: dict[str, ValidationResult] = field(default_factory=dict)
    fk_result: ValidationResult = field(
        default_factory=lambda: ValidationResult(passes=True, validator_name="__fk__")
    )
