"""Op-level UNSUPPORTED facts for format-driven string->temporal parsing.

`format` is an OPEN, unvalidated string, so it has no ValueClass -- see
ValueClass's docstring: "strftime is open (unvalidated) so it has NO
value-class -- it gates value-agnostically."  Gate-domain == production-domain
cannot hold for a format grammar, so these are whole-op WILDCARD_PARAM facts
(precedent: mountainash.expressions.backends.capabilities.string._op_level_facts), not value-scoped ones.

Probe matrix -- `format` on strptime_date / strptime_timestamp (2026-07-30,
ibis 12.0.0, narwhals 2.23.0):

| fixture         | strptime_date | strptime_timestamp |
|-----------------|---------------|--------------------|
| polars          | honored       | honored            |
| ibis-duckdb     | honored       | honored            |
| ibis-polars     | honored       | honored            |
| ibis-sqlite     | UNSUPPORTED   | UNSUPPORTED        |
| narwhals-polars | honored       | honored            |
| narwhals-pandas | UNSUPPORTED   | honored            |

Family / dialect discipline: the ibis FAMILY supports these ops (duckdb and
polars both honor the format), so `ibis-sqlite` is a dialect-scoped refinement
with NO family default -- a `dialect=None` fact would gate duckdb, which works.
This is the documented exception to the "ibis gets family-default AND concrete
dialect" rule, which addresses family-wide gaps.

Boundary: BUILD, not MATERIALIZE.  The gate fires at visit time and the backend
is never reached, so BUILD is what production does; MATERIALIZE would require
`native_errors`, forcing a backend import into a module that must stay
import-safe.  The native exception types are recorded test-side.

Migrated from mountainash.expressions.backends.expression_systems.strptime_format_capabilities (2026-08 capability-architecture PR).
"""
from __future__ import annotations

from mountainash.core.capabilities import (
    CapabilityFact,
    CapabilityLevel,
    WILDCARD_PARAM,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_DATETIME as FK_SUB_DT,
)

_SINCE = "2026-07-30"

_SQLITE_MSG = (
    "ibis-sqlite has no compilation rule for StringToDate/StringToTimestamp "
    "(OperationNotDefinedError); format-driven parsing is unavailable on this "
    "dialect, so it is gated rather than left to fail natively"
)

_OP_LEVEL_EXEMPTION = (
    "whole-op gate on a WILDCARD_PARAM fact; cannot be keyed on an OpSpec param "
    "(OpSpecs are indexed by concrete argument name) — verified by the dedicated "
    "cross-backend gate tests in test_datetime_strptime_format.py"
)

_IBIS_SQLITE_FACTS = tuple(
    CapabilityFact(
        operation_key=op_key,
        param=WILDCARD_PARAM,
        level=CapabilityLevel.UNSUPPORTED,
        backend=CONST_BACKEND.IBIS,
        dialect="ibis-sqlite",
        message=_SQLITE_MSG,
        since=_SINCE,
        probe_exempt=_OP_LEVEL_EXEMPTION,
    )
    for op_key in (FK_SUB_DT.STRPTIME_DATE, FK_SUB_DT.STRPTIME_TIMESTAMP)
)

_NARWHALS_PANDAS_MSG = (
    "narwhals raises NotImplementedError for str.to_date() on the default "
    "pandas backend (it would return an object-dtype Series, diverging from "
    "the polars API); str.to_datetime() is unaffected and stays supported"
)

_NARWHALS_FACTS = (
    CapabilityFact(
        operation_key=FK_SUB_DT.STRPTIME_DATE,
        param=WILDCARD_PARAM,
        level=CapabilityLevel.UNSUPPORTED,
        backend=CONST_BACKEND.NARWHALS,
        dialect="narwhals-pandas",
        message=_NARWHALS_PANDAS_MSG,
        since=_SINCE,
        probe_exempt=_OP_LEVEL_EXEMPTION,
    ),
)


from mountainash.core.capabilities.declarations import (  # noqa: E402
    CapabilityDeclaration,
    Domain,
    FactSource,
    ProbeEvidence,
)

_EVIDENCE = ProbeEvidence(
    probe_date=_SINCE,          # 2026-07-30
    library_versions=(("ibis", "12.0.0"), ("narwhals", "2.23.0")),
    fixtures=(
        "polars", "ibis-duckdb", "ibis-polars", "ibis-sqlite",
        "narwhals-polars", "narwhals-pandas",
    ),
)

DECLARATIONS = (
    CapabilityDeclaration(
        backend=CONST_BACKEND.IBIS, domain=Domain.DATETIME,
        source=FactSource.SUBSTRAIT,
        facts=_IBIS_SQLITE_FACTS,
        evidence=_EVIDENCE,
    ),
    CapabilityDeclaration(
        backend=CONST_BACKEND.NARWHALS, domain=Domain.DATETIME,
        source=FactSource.SUBSTRAIT,
        facts=_NARWHALS_FACTS,
        evidence=_EVIDENCE,
    ),
)
