"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.applicability import unbounded
from mountainash.core.capabilities.declarations import (
    CapabilityInformation, CapabilityKey, CapabilityPolicyRule, CapabilitySegment, Domain, Selector,
)
from mountainash.core.capabilities.schema import (
    CapabilityLevel, Clause, ClauseOp, InformationLayer, PolicyAction, PolicyConsumer, Predicate,
)
from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_MOUNTAINASH_REL

_SEEDED_COUNT = CapabilityKey(
    operation=RKEY_MOUNTAINASH_REL.SAMPLE,
    subject="seed",
    selector=Selector("predicate", Predicate((
        Clause("n", ClauseOp.IS_SET),
        Clause("seed", ClauseOp.IS_SET),
    ))),
)
_SEEDED_COUNT_MESSAGE = "Ibis exact-count sampling with a seed is unsupported; omit seed or use fractional sampling where supported."
SEEDED_COUNT_POLICY = CapabilityPolicyRule(
    key=_SEEDED_COUNT,
    level=CapabilityLevel.UNSUPPORTED,
    message=_SEEDED_COUNT_MESSAGE,
    consumer=PolicyConsumer.GATE,
    action=PolicyAction.BLOCK,
    applicability=unbounded,
)

SEGMENT = CapabilitySegment(
    domain=Domain.RELATION,
    information=(
        CapabilityInformation(
            key=CapabilityKey(operation=RKEY_MOUNTAINASH_REL.READ_RESOURCE, subject="resource"),
            level=CapabilityLevel.UNSUPPORTED,
            message="CSV dialect fields require the portable provider fallback reader",
            workaround="none needed — mountainash routes automatically",
            layer=InformationLayer.PUBLIC,
            applicability=unbounded,
        ),
        CapabilityInformation(
            key=_SEEDED_COUNT,
            level=CapabilityLevel.UNSUPPORTED,
            message=_SEEDED_COUNT_MESSAGE,
            layer=InformationLayer.PUBLIC,
            applicability=unbounded,
        ),
    ),
)
