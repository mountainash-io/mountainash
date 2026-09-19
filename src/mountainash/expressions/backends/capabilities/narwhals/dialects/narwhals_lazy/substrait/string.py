"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations


from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING
from mountainash.core.capabilities.declarations import CapabilityKey
from mountainash.core.capabilities.schema import CapabilityLevel, InformationLayer


from mountainash.core.capabilities.declarations import CapabilityInformation
from mountainash.core.capabilities.declarations import CapabilitySegment

SEGMENT = CapabilitySegment(
    domain=Domain.STRING,
    information=(
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS, subject="substring"),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-05",
            message="fixed upstream on the polars-backed narwhals path",
            issue="NW-STR-01",
        ),
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.REPLACE, subject="replacement"),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-05",
            message="fixed upstream on the polars-backed narwhals path",
            issue="NW-STR-03",
        ),
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_REPLACE, subject="replacement"),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-05",
            message="fixed upstream on the polars-backed narwhals path",
            issue="NW-STR-05",
        ),
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.STARTS_WITH, subject="substring"),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-05",
            message="fixed upstream on the polars-backed narwhals path",
            issue="NW-STR-01",
        ),
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.ENDS_WITH, subject="substring"),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-05",
            message="fixed upstream on the polars-backed narwhals path",
            issue="NW-STR-01",
        ),
    ),
)
