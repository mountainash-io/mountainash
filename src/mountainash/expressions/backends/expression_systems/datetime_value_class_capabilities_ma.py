"""Import-safe DURATION_MULTIPLIER value-class capability declarations (MA ops).

Reinstates integer unit multipliers >= 2 (e.g. "2d", "3h", "12mo") on the four
Mountainash datetime rounding ops (truncate / round_dt / ceil_dt / floor_dt).
PR-C registered only *exact* single-unit facts ("1d", ...); a multiplier value
has no exact fact, so without a value-CLASS fact it would reach the backend
un-gated (silent-wrong / raw error). This module declares the class per the
controller's Task-5 semantic agreement probe (see
`.superpowers/sdd/vc-probe-matrix.md`).

Probe matrix — DURATION_MULTIPLIER ("2d"/"3h"/"12mo"), all-fixtures:

| op        | polars  | ibis (ibis-duckdb) | narwhals-polars | narwhals-pandas |
|-----------|---------|--------------------|-----------------|-----------------|
| truncate  | honored | RAISED             | honored         | honored         |
| floor_dt  | honored | RAISED             | honored         | honored         |
| round_dt  | honored | RAISED             | SILENTLY-WRONG  | SILENTLY-WRONG  |
| ceil_dt   | honored | RAISED             | SILENTLY-WRONG  | SILENTLY-WRONG  |

- ibis raises for EVERY multiplier on ALL four ops: `TimestampTruncate` rejects
  the Polars-style "<n><unit>" duration form (SignatureValidationError) — the
  ibis impls pass the raw duration to `x.truncate(...)`.
- narwhals HONORS multipliers on truncate/floor_dt (native `dt.truncate` accepts
  the duration) but SILENTLY TRUNCATES on round_dt/ceil_dt (no native datetime
  round/ceil -> falls back to truncate, so "2d" rounds DOWN instead of to the
  nearest 2-day boundary — a wrong value).
- polars honors every multiplier on all four ops -> NO fact.

A value-class gates soundly here because the api-builder validates `unit` to
exactly the DURATION_MULTIPLIER predicate's domain (gate-domain ==
production-domain, spec Section 3.2): `validate_ma_option` admits a value only
when it is a finite canonical unit OR matches DURATION_MULTIPLIER.

Family / dialect discipline (mirrors PR-C `datetime_option_capabilities`):
  - ibis: family-default (dialect=None) fact AND ibis-duckdb fact — the
    dialect=None default protects every other ibis dialect from silently
    re-accepting a multiplier the family cannot honor.
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


_IBIS_FACTS = tuple(
    _mult_fact(op, CONST_BACKEND.IBIS, dialect, _IBIS_MSG)
    for op in _IBIS_MULTIPLIER_OPS
    for dialect in (None, "ibis-duckdb")  # family default + duckdb
)
_NARWHALS_FACTS = tuple(
    _mult_fact(op, CONST_BACKEND.NARWHALS, dialect, _NARWHALS_ROUND_CEIL_MSG)
    for op in _NARWHALS_MULTIPLIER_OPS
    for dialect in ("narwhals-polars", "narwhals-pandas")  # per-dialect only
)

CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, _IBIS_FACTS)
CapabilityRegistry.register_backend(CONST_BACKEND.NARWHALS, _NARWHALS_FACTS)
