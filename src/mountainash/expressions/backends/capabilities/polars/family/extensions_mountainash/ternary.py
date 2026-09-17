"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_TERNARY
from mountainash.core.capabilities.declarations import CapabilityKey
from mountainash.core.capabilities.schema import CapabilityLevel


from mountainash.core.capabilities.declarations import CapabilityAssertion
from mountainash.core.capabilities.declarations import CapabilitySegment

SEGMENT = CapabilitySegment(
    domain=Domain.TERNARY,
    capabilities=(
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_TERNARY.COLLECT_VALUES, subject="*"),
            level=CapabilityLevel.POLYMORPHIC,
            since="2026-07-05",
            message="literal collections unwrap to raw values; expressions compile through (LIST-wrapper marker)",
            probe_exempt="polymorphic — both paths supported by design",
        ),
    ),
)
