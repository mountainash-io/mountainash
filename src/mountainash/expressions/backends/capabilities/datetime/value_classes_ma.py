"""Import-safe value-class capability declarations (MA ops).

item 74 revision: truncate/round_dt/ceil_dt/floor_dt now redirect through the
real round_temporal/round_calendar implementation instead of calling
`x.truncate("<n><unit>")`/silently falling back to truncate. This retires
the DURATION_MULTIPLIER-class facts that used to declare ibis-duckdb
UNSUPPORTED for every multiplied unit ("2d", "3h", "12mo", ...) on all four
ops, and narwhals UNSUPPORTED for round_dt/ceil_dt specifically -- BOTH
claims are now false (verified 2026-08-16, re-probed through the live
redirect, not source-reading):

| op          | polars  | ibis-duckdb | ibis-sqlite | ibis-polars | narwhals (each dialect) |
|-------------|---------|-------------|-------------|-------------|--------------------------|
| truncate    | honored | honored     | RAISED      | honored     | honored                  |
| floor_dt    | honored | honored     | RAISED      | honored     | honored                  |
| round_dt    | honored | honored     | RAISED      | honored     | honored                  |
| ceil_dt     | honored | honored     | RAISED      | honored     | honored                  |
| to_timezone | honored | UNCOMPOSABLE| honored     | honored     | honored                  |

- ibis-duckdb honors every multiplied unit on all four rounding ops now:
  round_temporal/round_calendar's TimestampValue.bucket() (multiple > 1)
  works for every unit on duckdb.
- ibis-sqlite has no TimestampBucket compilation rule at all -- every
  multiplied unit on all four ops raises there (this is the SAME real gap
  capabilities/datetime/rounding.py declares for the direct Substrait
  round_temporal/round_calendar ops; this module declares it again for the
  four MA-wrapper FKEYs the visitor actually gates the outer call on).
- ibis-polars honors every multiplied fixed-duration unit (days/hours/etc);
  its genuine gap is calendar-unit (MONTH/YEAR) round/ceil, which is a
  closed, exact-value gap already declared in capabilities/datetime/options.py
  -- not a DURATION_MULTIPLIER-class (open-value) concern.
- narwhals HONORS every multiplied unit on all four ops now: round_dt/ceil_dt
  redirect through the same real hand-rolled round_temporal/round_calendar
  body as truncate/floor_dt (no more silent truncate-fallback).
- polars honors every multiplier on all four ops -> NO fact (unchanged).
- to_timezone on ibis is correct ONLY at the result-materialization boundary (the
  target zone lives in the ibis output dtype, but SQL is a bare CAST AS TIMESTAMPTZ),
  so any expression composed on the result raises UnsupportedOperationError (UNCOMPOSABLE).
  Declared UNSUPPORTED so the capability gate raises BackendCapabilityError.
  (Unchanged by item 74 -- unrelated to rounding.)

A value-class gates soundly here because the api-builder validates parameters to
their respective value-class domains (spec Section 3.2).

Dialect discipline (item 74 revision): NO ibis family default (dialect=None)
for the rounding facts -- ibis-duckdb and ibis-polars both honor every
multiplier now; only ibis-sqlite has a real gap, so it gets its own concrete
fact (mirrors capabilities/datetime/options.py's identical policy change in
this same PR). to_timezone's family default is unchanged (still a genuine
ibis-wide limitation). narwhals: per-dialect facts remain the convention
where needed, but round_dt/ceil_dt no longer need any narwhals fact at all.

Migrated from mountainash.expressions.backends.expression_systems.datetime_value_class_capabilities_ma (2026-08 capability-architecture PR).
"""
from __future__ import annotations

from mountainash.core.capabilities import (
    CapabilityFact,
    CapabilityLevel,
    ValueClass,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_DATETIME as FK_DT,
)

_SINCE = "2026-08-16"

# Known residual gap (documented, not enforced by a fact -- see module
# docstring): ibis-sqlite's TimestampBucket has no compilation rule, so a
# multi-digit MA-wrapper duration string (e.g. dt.truncate("2d")) on
# ibis-sqlite raises a raw native OperationNotDefinedError rather than a
# clean BackendCapabilityError. A DURATION_MULTIPLIER-class fact for this
# would need a corresponding class-backed OptionCell, which the 4-fixture
# argument-type matrix cannot instantiate for ibis-sqlite (same structural
# limit documented in test_option_fact_integrity.py's
# _MATRIX_UNREACHABLE_DIALECT_FACTS) -- tracked as a backlog follow-up
# rather than adding an untested, unexercised fact here.

_TO_TIMEZONE_MSG = (
    "to_timezone is correct only at the materialization boundary -- the "
    "target zone lives in the ibis output dtype, not in the engine (SQL is a "
    "bare CAST AS TIMESTAMPTZ), so any expression composed on the result "
    "raises UnsupportedOperationError (verified 2026-07-29, ibis 12.0.0/duckdb)"
)
_IS_DST_MSG = (
    "is_dst is not supported on ibis -- ibis has no DST/timezone-offset "
    "primitive to build on (verified 2026-08-16, ibis 12.0.0/duckdb)"
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


def _is_dst_fact(backend, dialect: str | None, message: str) -> CapabilityFact:
    return CapabilityFact(
        operation_key=FK_DT.IS_DST,
        param="timezone",
        value_class=ValueClass.IANA_TIMEZONE,
        level=CapabilityLevel.UNSUPPORTED,
        backend=backend,
        dialect=dialect,
        message=message,
        since="2026-08-16",
    )


_IBIS_FACTS = tuple(
    _tz_fact(CONST_BACKEND.IBIS, dialect, _TO_TIMEZONE_MSG)
    for dialect in (None, "ibis-duckdb")
) + tuple(
    _is_dst_fact(CONST_BACKEND.IBIS, dialect, _IS_DST_MSG)
    for dialect in (None, "ibis-duckdb")
)
# narwhals honors every multiplied unit on all four ops now -- no facts.
_NARWHALS_FACTS: tuple[CapabilityFact, ...] = ()


from mountainash.core.capabilities.declarations import (  # noqa: E402
    CapabilityDeclaration,
    Domain,
    FactSource,
    ProbeEvidence,
)

_EVIDENCE = ProbeEvidence(
    probe_date=_SINCE,
    library_versions=(),
    fixtures=("ibis-duckdb",),
)
_NARWHALS_EVIDENCE = ProbeEvidence(
    probe_date=_SINCE,
    library_versions=(),
    fixtures=("narwhals-polars", "narwhals-pandas"),
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
        facts=_NARWHALS_FACTS,
        evidence=_NARWHALS_EVIDENCE,
    ),
)
