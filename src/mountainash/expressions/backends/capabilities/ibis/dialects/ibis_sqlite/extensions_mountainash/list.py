"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_LIST
from mountainash.core.capabilities.declarations import CapabilityKey
from mountainash.core.capabilities.schema import CapabilityLevel, InformationLayer


from mountainash.core.capabilities.declarations import CapabilityInformation
from mountainash.core.capabilities.declarations import Selector
from mountainash.core.capabilities.declarations import CapabilitySegment

SEGMENT = CapabilitySegment(
    domain=Domain.LIST,
    information=(
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_LIST.PARSE, subject="*"),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-24",
            message="This backend cannot execute LIST.PARSE for the requested item type and failure behavior",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_LIST.CAST_ITEMS,
                subject="failure_behavior",
                selector=Selector(kind="exact", value="throw"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-24",
            message="This backend cannot execute LIST.CAST_ITEMS for the requested failure behavior",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_LIST.CAST_ITEMS,
                subject="failure_behavior",
                selector=Selector(kind="exact", value="null"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-24",
            message="This backend cannot execute LIST.CAST_ITEMS for the requested failure behavior",
            layer=InformationLayer.NATIVE,
        ),
    ),
)
