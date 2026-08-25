"""Capability facts for temporal-``any`` parsing."""
from __future__ import annotations

from mountainash.core.capabilities import CapabilityFact, CapabilityLevel, WILDCARD_PARAM
from mountainash.core.capabilities.declarations import CapabilityDeclaration, Domain, FactSource, ProbeEvidence
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_DATETIME as FK_DT

_SINCE = "2026-08-25"
_EVIDENCE = ProbeEvidence(
    probe_date=_SINCE,
    library_versions=(("ibis", "12.0.0"), ("narwhals", "2.24.0")),
    fixtures=("datetime-any", "ibis", "narwhals-polars", "narwhals-pandas"),
)


def _facts(backend: CONST_BACKEND) -> tuple[CapabilityFact, ...]:
    return (
        CapabilityFact(
            operation_key=FK_DT.PARSE_TEMPORAL_ANY,
            param=WILDCARD_PARAM,
            level=CapabilityLevel.UNSUPPORTED,
            backend=backend,
            message="temporal-any parsing requires a row-wise native parser",
            since=_SINCE,
            probe_exempt="Temporal-any parsing is covered by conform temporal contract tests",
        ),
    )


DECLARATIONS = (
    CapabilityDeclaration(
        backend=CONST_BACKEND.IBIS,
        domain=Domain.DATETIME,
        source=FactSource.MOUNTAINASH,
        facts=_facts(CONST_BACKEND.IBIS),
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
