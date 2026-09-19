"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_DATETIME
from mountainash.core.capabilities.declarations import Selector
from mountainash.core.capabilities.declarations import CapabilityKey
from mountainash.core.capabilities.schema import CapabilityLevel, InformationLayer


from mountainash.core.capabilities.declarations import CapabilityInformation
from mountainash.core.capabilities.declarations import CapabilitySegment

SEGMENT = CapabilitySegment(
    domain=Domain.DATETIME,
    information=(
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.STRPTIME_DATE,
                subject="failure_behavior",
                selector=Selector(kind="exact", value="null"),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-21",
            message="null-on-invalid custom temporal parsing is supported only by Polars",
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.STRPTIME_TIMESTAMP,
                subject="failure_behavior",
                selector=Selector(kind="exact", value="null"),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-21",
            message="null-on-invalid custom temporal parsing is supported only by Polars",
        ),
    ),
)
