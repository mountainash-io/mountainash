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
from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_MOUNTAINASH_REL

SEGMENT = CapabilitySegment(
    domain=Domain.RELATION,
    policies=(
        CapabilityPolicyRule(
            key=CapabilityKey(RKEY_MOUNTAINASH_REL.IMPORT_INTO, "*"),
            level=CapabilityLevel.UNSUPPORTED,
            message="a lazy-only Narwhals implementation cannot import an eager Arrow table",
            consumer=PolicyConsumer.MATERIALIZATION_ERROR,
            action=PolicyAction.ENRICH,
            native_errors=(ValueError,),
            native_issue="narwhals:eager-arrow-import",
            applicability=unbounded,
        ),
    ),
)
