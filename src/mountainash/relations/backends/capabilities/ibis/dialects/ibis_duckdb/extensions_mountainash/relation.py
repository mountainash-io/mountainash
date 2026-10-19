"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.applicability import unbounded
from mountainash.core.capabilities.declarations import CapabilityPolicyRule, CapabilitySegment, Domain
from mountainash.core.capabilities.schema import CapabilityLevel, PolicyAction, PolicyConsumer
from mountainash.relations.backends.capabilities.ibis.family.extensions_mountainash.relation import (
    SAMPLE_SEEDED_COUNT_KEY,
    SAMPLE_SEEDED_COUNT_MESSAGE,
)

SEGMENT = CapabilitySegment(
    domain=Domain.RELATION,
    policies=(CapabilityPolicyRule(
        key=SAMPLE_SEEDED_COUNT_KEY,
        level=CapabilityLevel.UNSUPPORTED,
        message=SAMPLE_SEEDED_COUNT_MESSAGE,
        consumer=PolicyConsumer.GATE,
        action=PolicyAction.BLOCK,
        applicability=unbounded,
    ),),
)
