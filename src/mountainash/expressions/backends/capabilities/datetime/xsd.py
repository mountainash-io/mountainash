"""Capability facts for XSD semantic-string operations."""
from __future__ import annotations

from mountainash.core.capabilities import CapabilityFact, CapabilityLevel
from mountainash.core.capabilities.declarations import CapabilityDeclaration, Domain, FactSource, ProbeEvidence
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_DATETIME as FK_DT

_SINCE = "2026-08-21"
_EVIDENCE = ProbeEvidence(
    probe_date=_SINCE,
    library_versions=(("ibis", "12.0.0"), ("narwhals", "2.24.0"), ("polars", "1.43.2")),
    fixtures=("ibis-sqlite", "ibis-duckdb", "ibis-polars", "narwhals-polars", "narwhals-pandas", "polars"),
)

# SQLite cannot materialize the throw-mode residue expressions. The visitor
# gates these cells before execution; null mode remains portable.
_FACTS = tuple(
    CapabilityFact(
        operation_key=op_key,
        param="failure_behavior",
        option_value="throw",
        level=CapabilityLevel.UNSUPPORTED,
        backend=CONST_BACKEND.IBIS,
        dialect="ibis-sqlite",
        message="Ibis SQLite cannot materialize XSD throw-mode validation",
        since=_SINCE,
    )
    for op_key in (FK_DT.PARSE_XSD_DURATION, FK_DT.PARSE_XSD_PARTIAL_DATE)
)

DECLARATIONS = (
    CapabilityDeclaration(
        backend=CONST_BACKEND.IBIS,
        domain=Domain.DATETIME,
        source=FactSource.MOUNTAINASH,
        facts=_FACTS,
        evidence=_EVIDENCE,
    ),
)
