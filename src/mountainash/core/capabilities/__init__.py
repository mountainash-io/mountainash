"""Capability spine — schema, registry, backend identity (spec 2026-07-05)."""
from mountainash.core.capabilities.bootstrap import load_all_capability_declarations
from mountainash.core.capabilities.identity import BackendIdentity, KNOWN_DIALECTS
from mountainash.core.capabilities.registry import CapabilityRegistry, CapabilityViolation
from mountainash.core.capabilities.schema import (
    Boundary,
    CapabilityFact,
    CapabilityLevel,
    DivergenceFact,
    DivergenceKind,
    Enforcement,
    Fidelity,
    GapKind,
    KnownGap,
    TargetKind,
    ValueClass,
    WILDCARD_PARAM,
)

__all__ = [
    "BackendIdentity",
    "Boundary",
    "CapabilityFact",
    "CapabilityLevel",
    "CapabilityRegistry",
    "CapabilityViolation",
    "DivergenceFact",
    "DivergenceKind",
    "Enforcement",
    "Fidelity",
    "GapKind",
    "KNOWN_DIALECTS",
    "KnownGap",
    "TargetKind",
    "ValueClass",
    "WILDCARD_PARAM",
    "load_all_capability_declarations",
]
