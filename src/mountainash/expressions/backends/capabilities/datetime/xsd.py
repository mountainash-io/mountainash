"""Exact XSD throw-mode residue facts."""
from __future__ import annotations

from mountainash.core.capabilities import Boundary, CapabilityFact, CapabilityLevel, Enforcement, ResidueSignal, WILDCARD_PARAM
from mountainash.core.capabilities.declarations import CapabilityDeclaration, Domain, FactSource, ProbeEvidence
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_DATETIME as FK_DT

_SINCE = "2026-08-21"
_EVIDENCE = ProbeEvidence(
    probe_date=_SINCE,
    library_versions=(("ibis", "12.0.0"), ("narwhals", "2.24.0"), ("polars", "1.43.2")),
    fixtures=("ibis-sqlite", "ibis-duckdb", "ibis-polars", "narwhals-polars", "narwhals-pandas"),
)
_OPS = (FK_DT.PARSE_XSD_DURATION, FK_DT.PARSE_XSD_PARTIAL_DATE)
_CELLS = (
    (CONST_BACKEND.IBIS, "ibis-duckdb"),
    (CONST_BACKEND.IBIS, "ibis-polars"),
    (CONST_BACKEND.NARWHALS, "narwhals-polars"),
    (CONST_BACKEND.NARWHALS, "narwhals-pandas"),
)


def _facts(backend: CONST_BACKEND, dialect: str) -> tuple[CapabilityFact, ...]:
    return tuple(
        CapabilityFact(
            operation_key=op_key,
            param=WILDCARD_PARAM,
            level=CapabilityLevel.UNSUPPORTED,
            backend=backend,
            dialect=dialect,
            message="invalid XSD lexical values are converted to null by the residue policy",
            since=_SINCE,
            boundary=Boundary.MATERIALIZE,
            enforcement=Enforcement.MATERIALIZE_RESIDUE,
            residue_signal=ResidueSignal.NON_NULL_TO_NULL,
            native_errors=(),
        )
        for op_key in _OPS
    )


_SQLITE_GATES = tuple(
    CapabilityFact(
        operation_key=op_key,
        param=WILDCARD_PARAM,
        level=CapabilityLevel.UNSUPPORTED,
        backend=CONST_BACKEND.IBIS,
        dialect="ibis-sqlite",
        message="ibis-sqlite has no XSD lexical parser; gate before backend dispatch",
        since=_SINCE,
        boundary=Boundary.BUILD,
        enforcement=Enforcement.GATE,
    )
    for op_key in _OPS
)


DECLARATIONS = tuple(
    CapabilityDeclaration(
        backend=backend,
        domain=Domain.DATETIME,
        source=FactSource.MOUNTAINASH,
        facts=_facts(backend, dialect),
        evidence=_EVIDENCE,
    )
    for backend, dialect in _CELLS
) + (
    CapabilityDeclaration(
        backend=CONST_BACKEND.IBIS,
        domain=Domain.DATETIME,
        source=FactSource.MOUNTAINASH,
        facts=_SQLITE_GATES,
        evidence=_EVIDENCE,
    ),
)
