"""Value-scoped capability facts for Substrait ``extract`` / ``extract_boolean``.

Backlog item 62 (substrait-datetime-missing-ops). Both ops are now API-reachable;
their closed ``component`` domain is enforced at the api-builder and the option
values reaching the visitor are exactly the set enumerated here (gate-domain ==
production-domain).

Only the closed ``component`` grain (``option_value=``) lives here — one
UNSUPPORTED fact per probe-confirmed (backend, component) cell the native
backend cannot produce. The backend body raises ``BackendCapabilityError``
for these; the fact is the registry's authoritative record and drives the
visitor gate. The open ``timezone`` grain (``value_class=ValueClass.IANA_TIMEZONE``)
is a placement-guard domain module restriction (spec §3: domain modules carry
option-value / WILDCARD_PARAM / value-agnostic grains only, never value_class)
— those facts live in ``value_classes_substrait.py`` alongside
``assume_timezone``/``local_timestamp``/``strptime_timestamp``.

Probe matrix — per-backend × per-component (2026-08-15, polars 1.43.2,
narwhals 2.24.0, ibis 12.0.0/duckdb), verified natively with gate disabled:

| component          | polars | ibis | narwhals (both) |
|--------------------|--------|------|-----------------|
| YEAR               | hon    | hon  | hon             |
| ISO_YEAR           | hon    | hon  | UNSUPPORTED     |
| US_YEAR            | UNS    | UNS  | UNS             |
| QUARTER            | hon    | hon  | hon             |
| MONTH              | hon    | hon  | hon             |
| DAY                | hon    | hon  | hon             |
| DAY_OF_YEAR        | hon    | hon  | hon             |
| MONDAY_DAY_OF_WEEK | hon    | hon  | hon             |
| SUNDAY_DAY_OF_WEEK | hon    | hon  | hon             |
| MONDAY_WEEK        | UNS    | UNS  | UNS             |
| SUNDAY_WEEK        | UNS    | UNS  | UNS             |
| ISO_WEEK           | hon    | hon  | UNS             |
| US_WEEK            | UNS    | UNS  | UNS             |
| HOUR               | hon    | hon  | hon             |
| MINUTE             | hon    | hon  | hon             |
| SECOND             | hon    | hon  | hon             |
| MILLISECOND        | hon    | hon  | hon             |
| MICROSECOND        | hon    | hon  | hon             |
| NANOSECOND         | hon    | UNS  | hon             |
| PICOSECOND         | UNS    | UNS  | UNS             |
| SUBSECOND          | hon    | hon  | hon             |
| UNIX_TIME          | hon    | hon  | UNS             |
| TIMEZONE_OFFSET    | UNS    | UNS  | UNS             |

``TIMEZONE_OFFSET`` is declared everywhere: its native primitives
(``base_utc_offset``/``dst_offset``) require a timezone-aware timestamp, which
``extract`` cannot guarantee at build time — surfaced as input-type-dependent
overload validity (spec §7.3), not a raw backend error.

``extract_boolean.IS_DST`` is declared on all three backends (item 65's
placeholder); ``IS_LEAP_YEAR`` is honored on all three.

Family/dialect discipline: ibis gets a family-default (``dialect=None``) fact
plus a concrete ``ibis-duckdb`` refinement; narwhals gets per-dialect facts
only; polars gets a single ``dialect="polars"`` fact (matching the arithmetic
capabilities precedent).
"""
from __future__ import annotations

from mountainash.core.capabilities import (
    CapabilityFact,
    CapabilityLevel,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_DATETIME as FK_SUB_DT,
)

_SINCE = "2026-08-15"

# Per-backend closed-domain components that are DECLARED UNSUPPORTED (the
# complement of each backend's honored set — the probe matrix above).
_POLARS_UNSUPPORTED = frozenset(
    {"US_YEAR", "MONDAY_WEEK", "SUNDAY_WEEK", "US_WEEK", "PICOSECOND", "TIMEZONE_OFFSET"}
)
_IBIS_UNSUPPORTED = frozenset(
    {
        "US_YEAR",
        "MONDAY_WEEK",
        "SUNDAY_WEEK",
        "US_WEEK",
        "NANOSECOND",
        "PICOSECOND",
        "TIMEZONE_OFFSET",
    }
)
_NARWHALS_UNSUPPORTED = frozenset(
    {
        "ISO_YEAR",
        "US_YEAR",
        "MONDAY_WEEK",
        "SUNDAY_WEEK",
        "ISO_WEEK",
        "US_WEEK",
        "PICOSECOND",
        "UNIX_TIME",
        "TIMEZONE_OFFSET",
    }
)

_COMPONENT_MSG = (
    "the native backend has no primitive for this extract component "
    "(verified by semantic probe; see capabilities/datetime/extract.py)"
)


def _component_fact(
    backend: CONST_BACKEND, dialect: str | None, component: str
) -> CapabilityFact:
    return CapabilityFact(
        operation_key=FK_SUB_DT.EXTRACT,
        param="component",
        option_value=component,
        level=CapabilityLevel.UNSUPPORTED,
        backend=backend,
        dialect=dialect,
        message=_COMPONENT_MSG,
        since=_SINCE,
    )


_POLARS_FACTS = tuple(
    _component_fact(CONST_BACKEND.POLARS, "polars", c) for c in sorted(_POLARS_UNSUPPORTED)
)
_IBIS_FACTS = tuple(
    _component_fact(CONST_BACKEND.IBIS, None, c) for c in sorted(_IBIS_UNSUPPORTED)
) + tuple(
    _component_fact(CONST_BACKEND.IBIS, "ibis-duckdb", c) for c in sorted(_IBIS_UNSUPPORTED)
)
_NARWHALS_FACTS = tuple(
    fact
    for dialect in ("narwhals-polars", "narwhals-pandas")
    for fact in (
        tuple(
            _component_fact(CONST_BACKEND.NARWHALS, dialect, c)
            for c in sorted(_NARWHALS_UNSUPPORTED)
        )
    )
)

_IS_DST_MSG = (
    "extract_boolean(IS_DST) is a placeholder (constant False) on all backends; "
    "deferred to backlog item 65 (is-dst-placeholder-implementation)"
)


def _isdst_fact(backend: CONST_BACKEND, dialect: str | None) -> CapabilityFact:
    return CapabilityFact(
        operation_key=FK_SUB_DT.EXTRACT_BOOLEAN,
        param="component",
        option_value="IS_DST",
        level=CapabilityLevel.UNSUPPORTED,
        backend=backend,
        dialect=dialect,
        message=_IS_DST_MSG,
        since=_SINCE,
    )


_IS_DST_FACTS = (
    _isdst_fact(CONST_BACKEND.POLARS, "polars"),
    _isdst_fact(CONST_BACKEND.IBIS, None),
    _isdst_fact(CONST_BACKEND.IBIS, "ibis-duckdb"),
    _isdst_fact(CONST_BACKEND.NARWHALS, "narwhals-polars"),
    _isdst_fact(CONST_BACKEND.NARWHALS, "narwhals-pandas"),
)


from mountainash.core.capabilities.declarations import (  # noqa: E402
    CapabilityDeclaration,
    Domain,
    FactSource,
    ProbeEvidence,
)

_EVIDENCE = ProbeEvidence(
    probe_date=_SINCE,
    library_versions=(("polars", "1.43.2"), ("narwhals", "2.24.0"), ("ibis", "12.0.0")),
    fixtures=("polars", "ibis-duckdb", "narwhals-polars", "narwhals-pandas"),
)

DECLARATIONS = (
    CapabilityDeclaration(
        backend=CONST_BACKEND.POLARS,
        domain=Domain.DATETIME,
        source=FactSource.SUBSTRAIT,
        facts=_POLARS_FACTS + (_IS_DST_FACTS[0],),
        evidence=_EVIDENCE,
    ),
    CapabilityDeclaration(
        backend=CONST_BACKEND.IBIS,
        domain=Domain.DATETIME,
        source=FactSource.SUBSTRAIT,
        facts=_IBIS_FACTS + _IS_DST_FACTS[1:3],
        evidence=_EVIDENCE,
    ),
    CapabilityDeclaration(
        backend=CONST_BACKEND.NARWHALS,
        domain=Domain.DATETIME,
        source=FactSource.SUBSTRAIT,
        facts=_NARWHALS_FACTS + _IS_DST_FACTS[3:5],
        evidence=_EVIDENCE,
    ),
)
