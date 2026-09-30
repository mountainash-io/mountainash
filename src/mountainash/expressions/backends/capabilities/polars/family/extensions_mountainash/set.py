"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.applicability import unbounded
from mountainash.core.capabilities.declarations import CapabilityInformation, CapabilityKey, CapabilitySegment, Domain
from mountainash.core.capabilities.schema import CapabilityLevel, InformationLayer
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_SET

SEGMENT = CapabilitySegment(
    domain=Domain.SET,
    information=(
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_SET.IS_IN, subject="haystack"),
            layer=InformationLayer.PUBLIC,
            level=CapabilityLevel.POLYMORPHIC,
            message="literal collections unwrap to raw values; expressions compile through (LIST-wrapper marker)",
            applicability=unbounded,
        ),
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_SET.IS_NOT_IN, subject="haystack"),
            layer=InformationLayer.PUBLIC,
            level=CapabilityLevel.POLYMORPHIC,
            message="literal collections unwrap to raw values; expressions compile through (LIST-wrapper marker)",
            applicability=unbounded,
        ),
    ),
)
