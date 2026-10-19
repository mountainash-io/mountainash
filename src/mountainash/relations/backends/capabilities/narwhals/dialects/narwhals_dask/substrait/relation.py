"""Scope-owned Narwhals/Dask Substrait capability declarations."""

from __future__ import annotations

from mountainash.core.capabilities.applicability import unbounded
from mountainash.core.capabilities.declarations import (
    CapabilityInformation,
    CapabilityKey,
    CapabilityPolicyRule,
    CapabilitySegment,
    Domain,
    Selector,
)
from mountainash.core.capabilities.schema import (
    CapabilityLevel,
    Clause,
    ClauseOp,
    InformationLayer,
    PolicyAction,
    PolicyConsumer,
    Predicate,
)
from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_SUBSTRAIT_REL

_MESSAGE = (
    "Positive-offset slicing on Narwhals/Dask is unsupported because native "
    "offset construction can evaluate source rows before a terminal."
)
_KEY = CapabilityKey(
    operation=RKEY_SUBSTRAIT_REL.FETCH,
    subject="offset",
    selector=Selector(
        "predicate",
        Predicate((
            Clause("offset", ClauseOp.IS_SET),
            Clause("has_offset", ClauseOp.EQ, True),
        )),
    ),
)

SEGMENT = CapabilitySegment(
    domain=Domain.RELATION,
    information=(
        CapabilityInformation(
            key=_KEY,
            layer=InformationLayer.PUBLIC,
            level=CapabilityLevel.UNSUPPORTED,
            message=_MESSAGE,
            applicability=unbounded,
        ),
    ),
    policies=(
        CapabilityPolicyRule(
            key=_KEY,
            level=CapabilityLevel.UNSUPPORTED,
            message=_MESSAGE,
            consumer=PolicyConsumer.GATE,
            action=PolicyAction.BLOCK,
            applicability=unbounded,
        ),
    ),
)
