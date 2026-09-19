"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations


from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_DATETIME
from mountainash.core.capabilities.declarations import CapabilityKey
from mountainash.core.capabilities.schema import CapabilityLevel, InformationLayer


from mountainash.core.capabilities.declarations import CapabilityInformation
from mountainash.core.capabilities.declarations import CapabilitySegment

SEGMENT = CapabilitySegment(
    domain=Domain.DATETIME,
    information=(
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_TEMPORAL_ANY, subject="*"),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-25",
            message="temporal-any parsing requires a row-wise native parser",
        ),
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_DEFAULT, subject="*"),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-25",
            message="default datetime parsing requires the Polars native parser",
        ),
    ),
)
