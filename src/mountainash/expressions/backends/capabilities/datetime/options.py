"""Import-safe datetime option capability declarations.

Disposition matrix (item 74: truncate/round_dt/ceil_dt/floor_dt now redirect
through the real round_temporal/round_calendar implementation instead of a
silent-wrong truncate-fallback; re-verified 2026-08-16 against the pinned
libraries -- authoritative):

| op          | polars | ibis-duckdb | ibis-sqlite            | ibis-polars      | narwhals (each dialect) |
|-------------|--------|-------------|-------------------------|------------------|--------------------------|
| truncate    | ALL    | ALL         | declare sub-day+quarter | ALL              | declare 1w               |
| floor_dt    | ALL    | ALL         | declare sub-day+quarter | ALL              | declare 1w               |
| round_dt    | ALL    | ALL         | declare sub-day+quarter | declare cal+qtr  | declare 1w               |
| ceil_dt     | ALL    | ALL         | declare sub-day+quarter | declare cal+qtr  | declare 1w               |

"declare sub-day+quarter" = {1h, 1m, 1s, 1ms, 1us, 1q} declared UNSUPPORTED
on ibis-sqlite for every op: sqlite's TimestampTruncate has no support for
units finer than DAY (blocks FLOOR itself, hence every op), and its
TimestampBucket has no compilation rule at all (blocks the multiple=3
bucketing 1q needs, regardless of rounding mode).

"declare cal+qtr" = {1y, 1mo, 1q} declared UNSUPPORTED on ibis-polars, but
ONLY for round_dt/ceil_dt: those need `floor + ibis.interval(months=..)`/
`interval(years=..)` to compute the next boundary, and ibis's polars
sub-backend translates intervals via `polars.duration()`, which has no
months/years kwarg. truncate/floor_dt only ever call FLOOR (no interval
needed), so they honor 1y/1mo/1q on ibis-polars -- unlike ibis-sqlite's gap,
this one is genuinely rounding-mode-scoped, verified empirically (both
dialects' full op x value matrix probed directly, not inferred).

Portable core = {1y, 1mo, 1d, 1h, 1m, 1s, 1ms, 1us}. 1ns was dropped in Task 3a
(divisor-by-zero panic in polars). Honored cells carry NO fact — the cell
disposition is ``honored``. Declared cells carry a value-scoped UNSUPPORTED
fact; the visitor raises ``BackendCapabilityError`` BEFORE calling the
backend (enforce_capabilities=True by default), so the silent
narwhals-truncate fallback and the raw ibis error are both replaced by a
clean error path.

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

Dialect scoping (item 74 revision): NO ibis family default (dialect=None).
ibis-duckdb honors every value; ibis-sqlite and ibis-polars each have real,
independent gaps (different units, different op subsets) discovered by
direct probing, not inference from one dialect. A shared family-default
baseline would either wrongly restrict duckdb or wrongly permit
sqlite/polars — concrete per-dialect facts for the two known-divergent
dialects is the honest choice (mirrors capabilities/datetime/rounding.py's
identical policy for the underlying Substrait round_temporal/round_calendar
ops in this same PR). narwhals declared facts remain per-dialect only
(narwhals-polars AND narwhals-pandas) — design-review I-1; NEVER a single
dialect=None narwhals family fact, which would conflate the two dialects.

Migrated from mountainash.expressions.backends.expression_systems.datetime_option_capabilities (2026-08 capability-architecture PR).
"""
from __future__ import annotations

from mountainash.core.capabilities import (
    CapabilityFact,
    CapabilityLevel,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_DATETIME as FK_DT,
)


_SINCE = "2026-08-16"

# Domain spelling must match MA_OPTION_DOMAINS — the test-side guard cross-references
# them. 1ns/nanosecond were dropped (Task 3a); 1q (quarter) and 1w (week) remain
# in the friendly input set but are declared per-backend by capability facts.
_ALL_UNIT_VALUES = ("1y", "1mo", "1d", "1h", "1m", "1s", "1ms", "1us", "1w", "1q")
_FRIENDLY_ALIASES: dict[str, str] = {
    "year": "1y", "quarter": "1q", "month": "1mo", "week": "1w",
    "day": "1d", "hour": "1h", "minute": "1m", "second": "1s",
    "millisecond": "1ms", "microsecond": "1us",
}

# Each op maps to the FKEY the visitor gates on.
_UNIT_OP_FKEYS: dict[str, object] = {
    "truncate": FK_DT.TRUNCATE,
    "round_dt": FK_DT.ROUND,
    "ceil_dt": FK_DT.CEIL,
    "floor_dt": FK_DT.FLOOR,
}
_ALL_FOUR_OPS = tuple(_UNIT_OP_FKEYS)

# ibis-sqlite: every op declares the same set (TimestampTruncate has no
# sub-day support at all, which blocks FLOOR itself; TimestampBucket has no
# sqlite compilation rule, which blocks 1q's multiple=3 bucketing).
_IBIS_SQLITE_DECLARED: dict[str, tuple[str, ...]] = {
    op: ("1h", "1m", "1s", "1ms", "1us", "1q") for op in _ALL_FOUR_OPS
}

# ibis-polars: ONLY round_dt/ceil_dt declare 1y/1mo/1q -- truncate/floor_dt
# (FLOOR-only, no interval addition) honor them.
_IBIS_POLARS_DECLARED: dict[str, tuple[str, ...]] = {
    "round_dt": ("1y", "1mo", "1q"),
    "ceil_dt": ("1y", "1mo", "1q"),
}

# narwhals: every op declares only 1w (dt.truncate rejects the '1w' duration
# on both dialects; round_dt/ceil_dt redirect through the same truncate-based
# implementation as truncate/floor_dt, so they inherit the identical gap).
_NARWHALS_DECLARED: dict[str, tuple[str, ...]] = {
    op: ("1w",) for op in _ALL_FOUR_OPS
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


_IBIS_SQLITE_MSG = (
    "ibis-sqlite has no TimestampTruncate support for units finer than DAY, "
    "and no TimestampBucket compilation rule (blocks multiple>1 bucketing, "
    "which quarter needs); verified 2026-08-16, ibis 12.0.0"
)
_IBIS_POLARS_MSG = (
    "ibis's polars sub-backend translates interval addition via "
    "polars.duration(), which has no months/years kwarg -- round/ceil "
    "cannot compute the next calendar boundary (truncate/floor, which only "
    "need FLOOR, are unaffected); verified 2026-08-16, ibis 12.0.0"
)
_NARWHALS_TRUNCATE_WEEK_UNSUPPORTED = (
    "narwhals dt.truncate rejects the week unit '1w' (and its friendly "
    "alias 'week') on both dialects"
)


def _build_ibis_sqlite_facts() -> tuple[CapabilityFact, ...]:
    declared = _declared_with_aliases(_IBIS_SQLITE_DECLARED)
    return tuple(
        CapabilityFact(
            operation_key=_UNIT_OP_FKEYS[op],
            param="unit",
            option_value=value,
            level=CapabilityLevel.UNSUPPORTED,
            backend=CONST_BACKEND.IBIS,
            dialect="ibis-sqlite",
            message=_IBIS_SQLITE_MSG,
            since=_SINCE,
        )
        for op, declared_values in declared.items()
        for value in declared_values
    )


def _build_ibis_polars_facts() -> tuple[CapabilityFact, ...]:
    declared = _declared_with_aliases(_IBIS_POLARS_DECLARED)
    return tuple(
        CapabilityFact(
            operation_key=_UNIT_OP_FKEYS[op],
            param="unit",
            option_value=value,
            level=CapabilityLevel.UNSUPPORTED,
            backend=CONST_BACKEND.IBIS,
            dialect="ibis-polars",
            message=_IBIS_POLARS_MSG,
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
            message=_NARWHALS_TRUNCATE_WEEK_UNSUPPORTED,
            since=_SINCE,
        )
        for op, declared_values in declared.items()
        for value in declared_values
    )


_IBIS_FACTS = _build_ibis_sqlite_facts() + _build_ibis_polars_facts()
_NARWHALS_POLARS_FACTS = _build_narwhals_dialect_facts("narwhals-polars")
_NARWHALS_PANDAS_FACTS = _build_narwhals_dialect_facts("narwhals-pandas")

# polars honors EVERY value in the MA unit domain — no facts.
# ibis-duckdb honors EVERY value now that round_dt/ceil_dt redirect through
# the real round_temporal/round_calendar implementation — no facts.


from mountainash.core.capabilities.declarations import (  # noqa: E402
    CapabilityDeclaration,
    Domain,
    FactSource,
    ProbeEvidence,
)

_EVIDENCE = ProbeEvidence(
    probe_date=_SINCE,
    library_versions=(),
    fixtures=("ibis-sqlite", "ibis-polars", "narwhals-polars", "narwhals-pandas"),
)

DECLARATIONS = (
    CapabilityDeclaration(
        backend=CONST_BACKEND.IBIS, domain=Domain.DATETIME,
        source=FactSource.MOUNTAINASH,
        facts=_IBIS_FACTS,
        evidence=_EVIDENCE,
    ),
    CapabilityDeclaration(
        backend=CONST_BACKEND.NARWHALS, domain=Domain.DATETIME,
        source=FactSource.MOUNTAINASH,
        facts=_NARWHALS_POLARS_FACTS + _NARWHALS_PANDAS_FACTS,
        evidence=_EVIDENCE,
    ),
)
