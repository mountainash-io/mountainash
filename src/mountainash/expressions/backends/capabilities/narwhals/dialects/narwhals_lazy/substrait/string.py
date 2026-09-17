"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING
from mountainash.core.capabilities.declarations import CapabilityKey
from mountainash.core.capabilities.schema import CapabilityLevel


from mountainash.core.capabilities.declarations import CapabilityAssertion
from mountainash.core.capabilities.declarations import CapabilitySegment

SEGMENT = CapabilitySegment(
    domain=Domain.STRING,
    capabilities=(
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS, subject="substring"),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-05",
            message="fixed upstream on the polars-backed narwhals path",
            issue="NW-STR-01",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.REPLACE, subject="replacement"),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-05",
            message="fixed upstream on the polars-backed narwhals path",
            issue="NW-STR-03",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_REPLACE, subject="replacement"),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-05",
            message="fixed upstream on the polars-backed narwhals path",
            issue="NW-STR-05",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.STARTS_WITH, subject="substring"),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-05",
            message="fixed upstream on the polars-backed narwhals path",
            issue="NW-STR-01",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.ENDS_WITH, subject="substring"),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-05",
            message="fixed upstream on the polars-backed narwhals path",
            issue="NW-STR-01",
        ),
    ),
)
