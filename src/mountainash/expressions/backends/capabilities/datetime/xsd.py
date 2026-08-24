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

_OPS = (FK_DT.PARSE_XSD_DURATION, FK_DT.PARSE_XSD_PARTIAL_DATE)


def _facts(backend: CONST_BACKEND, dialect: str | None = None) -> tuple[CapabilityFact, ...]:
    return tuple(
        CapabilityFact(
            operation_key=op_key,
            param="failure_behavior",
            option_value="throw",
            level=CapabilityLevel.UNSUPPORTED,
            backend=backend,
            dialect=dialect,
            message="XSD throw-mode validation is gated where no residue materializer exists",
            since=_SINCE,
        )
        for op_key in _OPS
    )


DECLARATIONS = (
    CapabilityDeclaration(
        backend=CONST_BACKEND.IBIS,
        domain=Domain.DATETIME,
        source=FactSource.MOUNTAINASH,
        facts=_facts(CONST_BACKEND.IBIS, "ibis-sqlite") + _facts(CONST_BACKEND.IBIS),
        evidence=_EVIDENCE,
    ),
    CapabilityDeclaration(
        backend=CONST_BACKEND.NARWHALS,
        domain=Domain.DATETIME,
        source=FactSource.MOUNTAINASH,
        facts=_facts(CONST_BACKEND.NARWHALS),
        evidence=_EVIDENCE,
    ),
)
