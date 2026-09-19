"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_SET
from mountainash.core.capabilities.declarations import CapabilityKey
from mountainash.core.capabilities.schema import CapabilityLevel, InformationLayer


from mountainash.core.capabilities.declarations import CapabilityInformation
from mountainash.core.capabilities.declarations import CapabilitySegment

SEGMENT = CapabilitySegment(
    domain=Domain.SET,
    information=(
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_SET.IS_IN, subject="haystack"),
            level=CapabilityLevel.POLYMORPHIC,
            since="2026-07-05",
            message="literal collections unwrap to raw values; expressions compile through (LIST-wrapper marker)",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_SET.IS_NOT_IN, subject="haystack"),
            level=CapabilityLevel.POLYMORPHIC,
            since="2026-07-05",
            message="literal collections unwrap to raw values; expressions compile through (LIST-wrapper marker)",
            layer=InformationLayer.NATIVE,
        ),
    ),
)
