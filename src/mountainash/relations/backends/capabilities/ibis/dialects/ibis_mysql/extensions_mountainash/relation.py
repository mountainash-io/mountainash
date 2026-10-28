"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.applicability import unbounded
from mountainash.core.capabilities.declarations import (
    CapabilityKey,
    CapabilityPolicyRule,
    CapabilitySegment,
    Domain,
)
from mountainash.core.capabilities.schema import CapabilityLevel, PolicyAction, PolicyConsumer
from mountainash.relations.backends.capabilities.ibis.family.extensions_mountainash.relation import (
    SAMPLE_SEEDED_COUNT_KEY,
    SAMPLE_SEEDED_COUNT_MESSAGE,
)
from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_MOUNTAINASH_REL

SEGMENT = CapabilitySegment(
    domain=Domain.RELATION,
    policies=(
        CapabilityPolicyRule(
            key=SAMPLE_SEEDED_COUNT_KEY,
            level=CapabilityLevel.UNSUPPORTED,
            message=SAMPLE_SEEDED_COUNT_MESSAGE,
            consumer=PolicyConsumer.GATE,
            action=PolicyAction.BLOCK,
            applicability=unbounded,
        ),
        CapabilityPolicyRule(
            key=CapabilityKey(RKEY_MOUNTAINASH_REL.IMPORT_INTO, "*"),
            level=CapabilityLevel.UNSUPPORTED,
            message="owned temporary-table adoption is unsupported on this SQL dialect",
            consumer=PolicyConsumer.GATE,
            action=PolicyAction.BLOCK,
            applicability=unbounded,
        ),
    ),
)
