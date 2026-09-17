"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_DATETIME
from mountainash.core.capabilities.declarations import Selector
from mountainash.core.capabilities.declarations import CapabilityKey
from mountainash.core.capabilities.schema import CapabilityLevel


from mountainash.core.capabilities.declarations import CapabilityAssertion
from mountainash.core.capabilities.declarations import CapabilitySegment

SEGMENT = CapabilitySegment(
    domain=Domain.DATETIME,
    capabilities=(
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.ROUND_CALENDAR,
                subject="unit",
                selector=Selector(kind="exact", value="MONTH"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis's polars sub-backend translates interval addition via polars.duration(), which has no months/years kwarg -- CEIL/ROUND_TIE_DOWN/ROUND_TIE_UP cannot compute the next calendar boundary; verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.ROUND_CALENDAR,
                subject="unit",
                selector=Selector(kind="exact", value="YEAR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis's polars sub-backend translates interval addition via polars.duration(), which has no months/years kwarg -- CEIL/ROUND_TIE_DOWN/ROUND_TIE_UP cannot compute the next calendar boundary; verified 2026-08-16, ibis 12.0.0",
        ),
    ),
)
