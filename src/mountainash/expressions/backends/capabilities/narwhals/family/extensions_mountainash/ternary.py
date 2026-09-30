"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.applicability import unbounded
from mountainash.core.capabilities.declarations import CapabilityInformation, CapabilityKey, CapabilitySegment, Domain
from mountainash.core.capabilities.schema import CapabilityLevel, InformationLayer
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_TERNARY

SEGMENT = CapabilitySegment(
    domain=Domain.TERNARY,
    information=(
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_TERNARY.COLLECT_VALUES, subject="*"),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.POLYMORPHIC,
            message="literal collections unwrap to raw values; expressions compile through (LIST-wrapper marker)",
            applicability=unbounded,
        ),
    ),
)
