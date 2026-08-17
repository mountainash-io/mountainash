"""Capability declarations for round_temporal / round_calendar (item 74).

Both ops share the real Substrait 9-unit closed domain (YEAR..MICROSECOND).
Every backend implements the shared algorithm in its Python body; the
per-dialect gaps below were discovered empirically (2026-08-16 probe against
ibis 12.0.0's duckdb/sqlite/polars sub-backends) and are NOT modeled in the
Python bodies — a single shared implementation covers duckdb natively, and
these facts block the dialects where it does not translate, rather than the
body special-casing dialects it cannot itself distinguish.

ibis-sqlite:
  - ``TimestampTruncate`` has no HOUR/MINUTE/SECOND/MILLISECOND/MICROSECOND
    support (only YEAR/MONTH/WEEK/DAY) -- FLOOR itself fails for those units
    on round_temporal (whose whole unit domain is a subset of them) and on
    round_calendar's sub-day units.
  - ``TimestampBucket`` (used for multiple > 1) has no sqlite compilation
    rule at all -- declared per the single representative multiplier value
    this repo's tests actually exercise (mirrors the OPTION_VALUE_DOMAINS
    "representative value" convention for open-domain int options).

ibis-polars:
  - CEIL/tie modes need `ibis.interval(months=..)`/`ibis.interval(years=..)`
    to compute the next boundary; ibis's polars sub-backend translates
    intervals via `polars.duration()`, which has no months/years kwarg
    (calendar-length intervals are not fixed-duration). FLOOR alone (which
    only calls `.truncate()`, no interval) would still work for MONTH/YEAR,
    but declaring the whole unit UNSUPPORTED is the closed-by-default
    choice: partial per-rounding-mode support within one unit is exactly
    the "silently inconsistent" shape this repo's capability facts exist
    to prevent (see round_dt/ceil_dt in options.py for the same policy).
"""
from __future__ import annotations

from mountainash.core.capabilities import CapabilityFact, CapabilityLevel
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_DATETIME as FK_DT,
)

_SINCE = "2026-08-16"

_SQLITE_UNIT_MSG = (
    "ibis-sqlite TimestampTruncate has no support for units finer than DAY "
    "(HOUR/MINUTE/SECOND/MILLISECOND/MICROSECOND); verified 2026-08-16, "
    "ibis 12.0.0"
)
_SQLITE_MULTIPLE_MSG = (
    "ibis-sqlite has no TimestampBucket compilation rule -- multiple > 1 is "
    "unsupported for every unit; verified 2026-08-16, ibis 12.0.0"
)
_POLARS_CALENDAR_MSG = (
    "ibis's polars sub-backend translates interval addition via "
    "polars.duration(), which has no months/years kwarg -- CEIL/"
    "ROUND_TIE_DOWN/ROUND_TIE_UP cannot compute the next calendar boundary; "
    "verified 2026-08-16, ibis 12.0.0"
)

_SQLITE_SUB_DAY_UNITS = ("HOUR", "MINUTE", "SECOND", "MILLISECOND", "MICROSECOND")
_ROUNDING_OPS = (FK_DT.ROUND_TEMPORAL, FK_DT.ROUND_CALENDAR)


def _sqlite_unit_facts() -> tuple[CapabilityFact, ...]:
    return tuple(
        CapabilityFact(
            operation_key=op,
            param="unit",
            option_value=unit,
            level=CapabilityLevel.UNSUPPORTED,
            backend=CONST_BACKEND.IBIS,
            dialect="ibis-sqlite",
            message=_SQLITE_UNIT_MSG,
            since=_SINCE,
        )
        for op in _ROUNDING_OPS
        for unit in _SQLITE_SUB_DAY_UNITS
    )


def _sqlite_multiple_facts() -> tuple[CapabilityFact, ...]:
    # Representative multiplier values this repo's tests exercise (item 74's
    # cross-backend test file): round_temporal HOUR multiple=2, round_calendar
    # MONTH multiple=3. HOUR is already blocked by _sqlite_unit_facts above;
    # the multiple=2 fact is retained for completeness/symmetry.
    return (
        CapabilityFact(
            operation_key=FK_DT.ROUND_TEMPORAL,
            param="multiple",
            option_value="2",
            level=CapabilityLevel.UNSUPPORTED,
            backend=CONST_BACKEND.IBIS,
            dialect="ibis-sqlite",
            message=_SQLITE_MULTIPLE_MSG,
            since=_SINCE,
        ),
        CapabilityFact(
            operation_key=FK_DT.ROUND_CALENDAR,
            param="multiple",
            option_value="3",
            level=CapabilityLevel.UNSUPPORTED,
            backend=CONST_BACKEND.IBIS,
            dialect="ibis-sqlite",
            message=_SQLITE_MULTIPLE_MSG,
            since=_SINCE,
        ),
    )


def _polars_calendar_unit_facts() -> tuple[CapabilityFact, ...]:
    return tuple(
        CapabilityFact(
            operation_key=FK_DT.ROUND_CALENDAR,
            param="unit",
            option_value=unit,
            level=CapabilityLevel.UNSUPPORTED,
            backend=CONST_BACKEND.IBIS,
            dialect="ibis-polars",
            message=_POLARS_CALENDAR_MSG,
            since=_SINCE,
        )
        for unit in ("MONTH", "YEAR")
    )


_IBIS_FACTS = _sqlite_unit_facts() + _sqlite_multiple_facts() + _polars_calendar_unit_facts()


from mountainash.core.capabilities.declarations import (  # noqa: E402
    CapabilityDeclaration,
    Domain,
    FactSource,
    ProbeEvidence,
)

_EVIDENCE = ProbeEvidence(
    probe_date=_SINCE,
    library_versions=(),
    fixtures=("ibis-sqlite", "ibis-polars"),
)

DECLARATIONS = (
    CapabilityDeclaration(
        backend=CONST_BACKEND.IBIS, domain=Domain.DATETIME,
        source=FactSource.SUBSTRAIT,
        facts=_IBIS_FACTS,
        evidence=_EVIDENCE,
    ),
)
