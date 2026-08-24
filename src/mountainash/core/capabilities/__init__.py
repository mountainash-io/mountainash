"""Capability spine — schema, registry, backend identity (spec 2026-07-05)."""
from mountainash.core.capabilities.bootstrap import load_all_capability_declarations
from mountainash.core.capabilities.declarations import (
    CapabilityDeclaration,
    CapabilityDeclarationModule,
    Domain,
    FactSource,
    ProbeEvidence,
    classify_domain,
    classify_source,
)
from mountainash.core.capabilities.identity import BackendIdentity, KNOWN_DIALECTS
from mountainash.core.capabilities.predicates import BoundCall
from mountainash.core.capabilities.registry import CapabilityRegistry, CapabilityViolation
from mountainash.core.capabilities.retired import RETIRED_FACTS, RetiredFact
from mountainash.core.capabilities.schema import (
    Boundary,
    CapabilityFact,
    CapabilityLevel,
    Clause,
    ClauseOp,
    DivergenceFact,
    Enforcement,
    DivergenceKind,
    Fidelity,
    GapKind,
    KnownGap,
    Predicate,
    ResidueSignal,
    TargetKind,
    ValueClass,
    WILDCARD_PARAM,
)

__all__ = [
    "BackendIdentity",
    "BoundCall",
    "Boundary",
    "CapabilityDeclaration",
    "CapabilityDeclarationModule",
    "CapabilityFact",
    "CapabilityLevel",
    "CapabilityRegistry",
    "CapabilityViolation",
    "Clause",
    "ClauseOp",
    "DivergenceFact",
    "DivergenceKind",
    "Domain",
    "Enforcement",
    "FactSource",
    "Fidelity",
    "GapKind",
    "KNOWN_DIALECTS",
    "KnownGap",
    "Predicate",
    "ResidueSignal",
    "ProbeEvidence",
    "RETIRED_FACTS",
    "RetiredFact",
    "TargetKind",
    "ValueClass",
    "WILDCARD_PARAM",
    "classify_domain",
    "classify_source",
    "load_all_capability_declarations",
]
