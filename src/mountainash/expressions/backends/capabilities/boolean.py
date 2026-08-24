"""Capability declarations for token-based boolean parsing."""
from __future__ import annotations

from mountainash.core.capabilities import (
    CapabilityDeclaration,
    CapabilityFact,
    CapabilityLevel,
    Clause,
    ClauseOp,
    Domain,
    FactSource,
    Predicate,
    ProbeEvidence,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_BOOLEAN as FK_BOOLEAN,
)

_SINCE = "2026-08-25"
_EVIDENCE = ProbeEvidence(
    probe_date=_SINCE,
    library_versions=(
        ("narwhals", "2.24.0"),
        ("polars", "1.43.2"),
        ("pandas", "3.0.5"),
        ("ibis", "12.0.0"),
    ),
    fixtures=("boolean-token-parse", "boolean-invalid-token-failure"),
)

_IBIS_SQLITE_THROW_GATE = CapabilityFact(
    operation_key=FK_BOOLEAN.PARSE_TOKENS,
    param="failure_behavior",
    option_value=None,
    predicate=Predicate((Clause("failure_behavior", ClauseOp.EQ, "throw"),)),
    level=CapabilityLevel.UNSUPPORTED,
    backend=CONST_BACKEND.IBIS,
    dialect="ibis-sqlite",
    message="ibis-sqlite cannot enforce throw-on-invalid boolean tokens",
    since=_SINCE,
)

DECLARATIONS = (
    CapabilityDeclaration(
        backend=CONST_BACKEND.POLARS,
        domain=Domain.BOOLEAN,
        source=FactSource.MOUNTAINASH,
        facts=(),
        evidence=_EVIDENCE,
    ),
    CapabilityDeclaration(
        backend=CONST_BACKEND.NARWHALS,
        domain=Domain.BOOLEAN,
        source=FactSource.MOUNTAINASH,
        facts=(),
        evidence=_EVIDENCE,
    ),
    CapabilityDeclaration(
        backend=CONST_BACKEND.IBIS,
        domain=Domain.BOOLEAN,
        source=FactSource.MOUNTAINASH,
        facts=(_IBIS_SQLITE_THROW_GATE,),
        evidence=_EVIDENCE,
    ),
)
