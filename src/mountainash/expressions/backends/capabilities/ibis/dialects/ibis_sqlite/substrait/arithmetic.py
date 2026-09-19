"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import CapabilitySegment

from mountainash.core.capabilities.declarations import Domain


from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC
from mountainash.core.capabilities.declarations import CapabilityInformation, CapabilityKey, Selector
from mountainash.core.capabilities.schema import CapabilityLevel, InformationLayer

SEGMENT = CapabilitySegment(
    domain=Domain.ARITHMETIC,
    information=(
        CapabilityInformation(
            key=CapabilityKey(
                FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ABS,
                "overflow",
                Selector(kind="exact", value="ERROR"),
            ),
            layer=InformationLayer.PUBLIC,
            level=CapabilityLevel.POLYMORPHIC,
            since="2026-08-21",
            message="SQLite ABS ERROR is available only for declared Ibis Int64 operands; narrower declared literal widths wrap at their native minima.",
        ),
    ),
)
