"""Import-safe datetime option capability declarations.

Disposition matrix (verified by the controller Step-0 probe of all four
fixtures, post-Task-3a — authoritative):

| op          | polars | ibis (ibis-duckdb)         | narwhals (each dialect)    |
|-------------|--------|----------------------------|----------------------------|
| truncate    | ALL    | honor core+1w; declare 1q  | honor core+1q; declare 1w  |
| floor_dt    | ALL    | honor core+1w; declare 1q  | honor core+1q; declare 1w  |
| round_dt    | ALL    | declare EVERY value        | declare EVERY value        |
| ceil_dt     | ALL    | declare EVERY value        | declare EVERY value        |

Portable core = {1y, 1mo, 1d, 1h, 1m, 1s, 1ms, 1us}. 1ns was dropped in Task 3a
(divisor-by-zero panic in polars). Honored cells carry NO fact — the cell
disposition is ``honored``. Declared cells carry a value-scoped UNSUPPORTED
fact; the visitor raises ``BackendCapabilityError`` BEFORE calling the
backend (enforce_capabilities=True by default), so the silent
narwhals-truncate fallback and the raw ibis error are both replaced by a
clean error path. Backend round/ceil/floor impls are NOT edited — the
capability facts are the only honesty mechanism.

Friendly aliases (year, quarter, month, week, day, hour, minute, second,
millisecond, microsecond) are normalized to their canonical duration form
by the api builder BEFORE the visitor sees the value, so the visitor's
gating fact lookup uses the normalized form. To satisfy the integrity
guard's ``declared cells ↔ facts`` equality, the disposition matrix
enumerates BOTH the duration forms and the friendly aliases; the
declarations here mirror that with paired facts (one per (op, value,
backend, dialect)). The friendly-alias facts are lookup-equivalent to
the canonical-form facts — the visitor never resolves the alias form
because the api builder already normalized it — but the integrity guard
counts them as separate cells, so they must be separately declared.

Family / dialect separation (mirrors the string ``padding`` slice):
  - ibis declared: family-default (dialect=None) fact AND ibis-duckdb fact;
    ibis-duckdb-specific, but a dialect=None family default protects every
    other ibis dialect (ibis-sqlite, ibis-bigquery, ...) from silently
    re-accepting a value the family cannot honor.
  - narwhals declared: per-dialect facts only (narwhals-polars AND
    narwhals-pandas) — design-review I-1; NEVER a single dialect=None
    narwhals family fact, which would conflate the two dialects.
"""
from __future__ import annotations

from mountainash.core.capabilities import (
    CapabilityFact,
    CapabilityLevel,
    CapabilityRegistry,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_DATETIME as FK_DT,
)


_SINCE = "2026-07-24"

# Domain spelling must match MA_OPTION_DOMAINS — the test-side guard cross-references
# them. Post-Task-3a: 1ns/nanosecond were dropped; 1q (quarter) and 1w (week) remain
# in the friendly input set but are declared per-backend by capability facts.
_ALL_UNIT_VALUES = ("1y", "1mo", "1d", "1h", "1m", "1s", "1ms", "1us", "1w", "1q")
_FRIENDLY_ALIASES: dict[str, str] = {
    "year": "1y", "quarter": "1q", "month": "1mo", "week": "1w",
    "day": "1d", "hour": "1h", "minute": "1m", "second": "1s",
    "millisecond": "1ms", "microsecond": "1us",
}
# Every value the disposition matrix enumerates: duration forms + friendly
# aliases. Both forms share the same per-backend disposition (the api
# builder normalizes aliases to the canonical form, so the backend only
# sees one or the other).
_ALL_VALUES_WITH_ALIASES: tuple[str, ...] = (
    _ALL_UNIT_VALUES + tuple(_FRIENDLY_ALIASES)
)

# Each (op, fkey) maps to the unit value set the visitor must gate. truncate
# and floor_dt share semantics (floor == truncate) per Task 3a; both honor
# core+1w on ibis (1q is not in ibis TimestampTruncate) and core+1q on
# narwhals (1w is not a supported narwhals truncate unit). round_dt and
# ceil_dt have NO native datetime impl on ibis/narwhals (silent
# truncate-fallback is an anti-pattern) — declared UNSUPPORTED for EVERY
# unit value on ibis and both narwhals dialects.
_UNIT_OP_FKEYS: dict[str, object] = {
    "truncate": FK_DT.TRUNCATE,
    "round_dt": FK_DT.ROUND,
    "ceil_dt": FK_DT.CEIL,
    "floor_dt": FK_DT.FLOOR,
}

# (op, value) pairs ibis-duckdb DECLARES UNSUPPORTED. (truncate and floor_dt:
# only 1q is undeclared on ibis; 1w is honored. round_dt and ceil_dt: ALL
# values are undeclared.) Keyed by duration form; the friendly-alias form
# is added at declaration time so the integrity guard sees both.
_IBIS_DUCKDB_DECLARED: dict[str, tuple[str, ...]] = {
    "truncate": ("1q",),
    "floor_dt": ("1q",),
    "round_dt": _ALL_UNIT_VALUES,
    "ceil_dt": _ALL_UNIT_VALUES,
}
_NARWHALS_DECLARED: dict[str, tuple[str, ...]] = {
    "truncate": ("1w",),
    "floor_dt": ("1w",),
    "round_dt": _ALL_UNIT_VALUES,
    "ceil_dt": _ALL_UNIT_VALUES,
}


def _declared_with_aliases(
    declared_by_duration: dict[str, tuple[str, ...]],
) -> dict[str, tuple[str, ...]]:
    """Expand a duration-form declaration set to include the matching
    friendly aliases (e.g. "1q" -> "quarter", "1w" -> "week"). The api
    builder normalizes aliases to the canonical form before the visitor,
    so the visitor only ever resolves the duration form — the alias facts
    exist solely to satisfy the disposition matrix's
    ``declared cells ↔ facts`` equality (each alias in the domain gets
    its own cell)."""
    out: dict[str, tuple[str, ...]] = {}
    for op, declared in declared_by_duration.items():
        values = list(declared)
        for friendly, canonical in _FRIENDLY_ALIASES.items():
            if canonical in declared:
                values.append(friendly)
        out[op] = tuple(values)
    return out


# Per-(op, value) human-readable limitation messages, named after the real
# backend behavior the controller probe observed.
_IBIS_QUARTER_UNSUPPORTED = (
    "ibis TimestampTruncate rejects the quarter unit '1q' (and its "
    "friendly alias 'quarter')"
)
_IBIS_NO_NATIVE_ROUND_CEIL = (
    "ibis has no native datetime round/ceil; silently falling back to "
    "truncate would return a wrong value"
)
_NARWHALS_TRUNCATE_WEEK_UNSUPPORTED = (
    "narwhals truncate rejects the week unit '1w' (and its friendly "
    "alias 'week')"
)
_NARWHALS_NO_NATIVE_ROUND_CEIL = (
    "narwhals has no native datetime round/ceil; silently falling back to "
    "truncate would return a wrong value"
)


def _ibis_duckdb_message(op: str, value: str) -> str:
    if op in {"round_dt", "ceil_dt"}:
        return _IBIS_NO_NATIVE_ROUND_CEIL
    return _IBIS_QUARTER_UNSUPPORTED


def _narwhals_message(op: str, value: str) -> str:
    if op in {"round_dt", "ceil_dt"}:
        return _NARWHALS_NO_NATIVE_ROUND_CEIL
    return _NARWHALS_TRUNCATE_WEEK_UNSUPPORTED


def _build_ibis_duckdb_facts() -> tuple[CapabilityFact, ...]:
    declared = _declared_with_aliases(_IBIS_DUCKDB_DECLARED)
    return tuple(
        CapabilityFact(
            operation_key=_UNIT_OP_FKEYS[op],
            param="unit",
            option_value=value,
            level=CapabilityLevel.UNSUPPORTED,
            backend=CONST_BACKEND.IBIS,
            dialect="ibis-duckdb",
            message=_ibis_duckdb_message(op, value),
            since=_SINCE,
        )
        for op, declared_values in declared.items()
        for value in declared_values
    )


def _build_ibis_family_defaults() -> tuple[CapabilityFact, ...]:
    """ibis dialect=None family-default facts — protect every other ibis
    dialect (ibis-sqlite, ibis-bigquery, …) from silently re-accepting a
    value the family cannot honor. Mirrors _IBIS_FAMILY_DEFAULTS in the
    string padding slice."""
    declared = _declared_with_aliases(_IBIS_DUCKDB_DECLARED)
    return tuple(
        CapabilityFact(
            operation_key=_UNIT_OP_FKEYS[op],
            param="unit",
            option_value=value,
            level=CapabilityLevel.UNSUPPORTED,
            backend=CONST_BACKEND.IBIS,
            dialect=None,
            message=_ibis_duckdb_message(op, value),
            since=_SINCE,
        )
        for op, declared_values in declared.items()
        for value in declared_values
    )


def _build_narwhals_dialect_facts(dialect: str) -> tuple[CapabilityFact, ...]:
    declared = _declared_with_aliases(_NARWHALS_DECLARED)
    return tuple(
        CapabilityFact(
            operation_key=_UNIT_OP_FKEYS[op],
            param="unit",
            option_value=value,
            level=CapabilityLevel.UNSUPPORTED,
            backend=CONST_BACKEND.NARWHALS,
            dialect=dialect,
            message=_narwhals_message(op, value),
            since=_SINCE,
        )
        for op, declared_values in declared.items()
        for value in declared_values
    )


_IBIS_DUCKDB_FACTS = _build_ibis_duckdb_facts()
_IBIS_FAMILY_DEFAULTS = _build_ibis_family_defaults()
_NARWHALS_POLARS_FACTS = _build_narwhals_dialect_facts("narwhals-polars")
_NARWHALS_PANDAS_FACTS = _build_narwhals_dialect_facts("narwhals-pandas")

# polars honors EVERY value in the MA unit domain — no facts. The portable
# core + the divergent members (1w, 1q) all reach a real polars method.
# (1ns was dropped in Task 3a — the validator rejects it before the visitor.)


CapabilityRegistry.register_backend(
    CONST_BACKEND.IBIS,
    _IBIS_FAMILY_DEFAULTS + _IBIS_DUCKDB_FACTS,
)
CapabilityRegistry.register_backend(
    CONST_BACKEND.NARWHALS,
    _NARWHALS_POLARS_FACTS + _NARWHALS_PANDAS_FACTS,
)

