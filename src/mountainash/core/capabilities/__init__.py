"""Capability spine — schema, registry, backend identity (spec 2026-07-05)."""
from mountainash.core.capabilities.schema import (
    Boundary,
    CapabilityFact,
    CapabilityLevel,
    DivergenceFact,
    DivergenceKind,
    Fidelity,
    GapKind,
    KnownGap,
    TargetKind,
    WILDCARD_PARAM,
)

__all__ = [
    "Boundary",
    "CapabilityFact",
    "CapabilityLevel",
    "DivergenceFact",
    "DivergenceKind",
    "Fidelity",
    "GapKind",
    "KnownGap",
    "TargetKind",
    "WILDCARD_PARAM",
]
