"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_LIST
from mountainash.core.capabilities.declarations import CapabilityKey
from mountainash.core.capabilities.schema import CapabilityLevel


from mountainash.core.capabilities.declarations import CapabilityAssertion
from mountainash.core.capabilities.declarations import CapabilitySegment

SEGMENT = CapabilitySegment(
    domain=Domain.LIST,
    capabilities=(
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_LIST.CONTAINS, subject="item"),
            level=CapabilityLevel.LITERAL_ONLY,
            since="2026-07-05",
            message="Narwhals list.contains() requires a literal item argument, not a column expression",
            workaround="Use a literal value for item or use the Polars/Ibis backend.",
            issue="NW-LIST-01",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_LIST.T_CONTAINS, subject="item"),
            level=CapabilityLevel.LITERAL_ONLY,
            since="2026-07-05",
            message="Narwhals list.t_contains() requires a literal item argument, not a column expression",
            workaround="Use a literal value for item or use the Polars/Ibis backend.",
            issue="NW-LIST-01",
        ),
    ),
)
