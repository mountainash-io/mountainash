"""Import-safe value-class capability declarations (MA ops).

Reinstates integer unit multipliers >= 2 (e.g. "2d", "3h", "12mo") on the four
Mountainash datetime rounding ops (truncate / round_dt / ceil_dt / floor_dt),
and declares to_timezone unsupported on ibis.

Probe matrix — DURATION_MULTIPLIER and IANA_TIMEZONE, all-fixtures:

| op          | polars  | ibis (ibis-duckdb) | narwhals-polars | narwhals-pandas |
|-------------|---------|--------------------|-----------------|-----------------|
| truncate    | honored | RAISED             | honored         | honored         |
| floor_dt    | honored | RAISED             | honored         | honored         |
| round_dt    | honored | RAISED             | SILENTLY-WRONG  | SILENTLY-WRONG  |
| ceil_dt     | honored | RAISED             | SILENTLY-WRONG  | SILENTLY-WRONG  |
| to_timezone | honored | UNCOMPOSABLE       | honored         | honored         |

- ibis raises for EVERY multiplier on ALL four rounding ops: `TimestampTruncate` rejects
  the Polars-style "<n><unit>" duration form (SignatureValidationError) — the
  ibis impls pass the raw duration to `x.truncate(...)`.
- narwhals HONORS multipliers on truncate/floor_dt (native `dt.truncate` accepts
  the duration) but SILENTLY TRUNCATES on round_dt/ceil_dt (no native datetime
  round/ceil -> falls back to truncate, so "2d" rounds DOWN instead of to the
  nearest 2-day boundary — a wrong value).
- polars honors every multiplier on all four ops -> NO fact.
- to_timezone on ibis is correct ONLY at the result-materialization boundary (the
  target zone lives in the ibis output dtype, but SQL is a bare CAST AS TIMESTAMPTZ),
  so any expression composed on the result raises UnsupportedOperationError (UNCOMPOSABLE).
  Declared UNSUPPORTED so the capability gate raises BackendCapabilityError.

A value-class gates soundly here because the api-builder validates parameters to
their respective value-class domains (spec Section 3.2).

Family / dialect discipline (mirrors PR-C `datetime_option_capabilities`):
  - ibis: family-default (dialect=None) fact AND ibis-duckdb fact — the
    dialect=None default protects every other ibis dialect from silently
    re-accepting an operation/multiplier the family cannot honor.
  - narwhals: per-dialect facts ONLY (narwhals-polars AND narwhals-pandas) —
    never a dialect=None narwhals family default.
"""
from __future__ import annotations

from mountainash.core.capabilities import (
    CapabilityFact,
    CapabilityLevel,
    CapabilityRegistry,
    ValueClass,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_DATETIME as FK_DT,
)

_SINCE = "2026-07-25"

# op-name -> FKEY, for the four unit-rounding ops.
_ALL_ROUNDING = {
    "truncate": FK_DT.TRUNCATE,
    "round_dt": FK_DT.ROUND,
    "ceil_dt": FK_DT.CEIL,
    "floor_dt": FK_DT.FLOOR,
}

# ibis raises on multipliers for ALL four rounding ops.
_IBIS_MULTIPLIER_OPS = ("truncate", "round_dt", "ceil_dt", "floor_dt")
# narwhals only diverges (silent truncate) on round/ceil; truncate/floor honor.
_NARWHALS_MULTIPLIER_OPS = ("round_dt", "ceil_dt")

_IBIS_MSG = (
    "ibis TimestampTruncate rejects Polars-style multiplier duration units "
    "(e.g. '2d', '3h', '12mo'); only single bare units are accepted"
)
_NARWHALS_ROUND_CEIL_MSG = (
    "narwhals has no native datetime round/ceil; a multiplier value silently "
    "falls back to truncate and returns a wrong (down-rounded) result"
)
_TO_TIMEZONE_MSG = (
    "to_timezone is correct only at the materialization boundary -- the "
    "target zone lives in the ibis output dtype, not in the engine (SQL is a "
    "bare CAST AS TIMESTAMPTZ), so any expression composed on the result "
    "raises UnsupportedOperationError (verified 2026-07-29, ibis 12.0.0/duckdb)"
)


def _mult_fact(op: str, backend, dialect: str | None, message: str) -> CapabilityFact:
    return CapabilityFact(
        operation_key=_ALL_ROUNDING[op],
        param="unit",
        value_class=ValueClass.DURATION_MULTIPLIER,
        level=CapabilityLevel.UNSUPPORTED,
        backend=backend,
        dialect=dialect,
        message=message,
        since=_SINCE,
    )


def _tz_fact(backend, dialect: str | None, message: str) -> CapabilityFact:
    return CapabilityFact(
        operation_key=FK_DT.TO_TIMEZONE,
        param="timezone",
        value_class=ValueClass.IANA_TIMEZONE,
        level=CapabilityLevel.UNSUPPORTED,
        backend=backend,
        dialect=dialect,
        message=message,
        since="2026-07-29",
    )


_IBIS_FACTS = tuple(
    _mult_fact(op, CONST_BACKEND.IBIS, dialect, _IBIS_MSG)
    for op in _IBIS_MULTIPLIER_OPS
    for dialect in (None, "ibis-duckdb")  # family default + duckdb
) + tuple(
    _tz_fact(CONST_BACKEND.IBIS, dialect, _TO_TIMEZONE_MSG)
    for dialect in (None, "ibis-duckdb")
)
_NARWHALS_FACTS = tuple(
    _mult_fact(op, CONST_BACKEND.NARWHALS, dialect, _NARWHALS_ROUND_CEIL_MSG)
    for op in _NARWHALS_MULTIPLIER_OPS
    for dialect in ("narwhals-polars", "narwhals-pandas")  # per-dialect only
)

CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, _IBIS_FACTS)
CapabilityRegistry.register_backend(CONST_BACKEND.NARWHALS, _NARWHALS_FACTS)

