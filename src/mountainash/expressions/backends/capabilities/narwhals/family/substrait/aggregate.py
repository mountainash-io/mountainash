"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.applicability import unbounded
from mountainash.core.capabilities.declarations import (
    CapabilityInformation,
    CapabilityKey,
    CapabilitySegment,
    Domain,
)
from mountainash.core.capabilities.schema import CapabilityLevel, InformationLayer
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_AGGREGATE,
)

SEGMENT = CapabilitySegment(
    domain=Domain.AGGREGATE,
    information=(
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.PRODUCT,
                subject="*",
            ),
            level=CapabilityLevel.UNSUPPORTED,
            message=(
                "Narwhals has no supported product aggregate; mountainash rejects "
                "PRODUCT on every Narwhals variant."
            ),
            layer=InformationLayer.NATIVE,
            applicability=unbounded,
        ),
    ),
)
