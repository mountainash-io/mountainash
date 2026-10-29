"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.applicability import unbounded
from mountainash.core.capabilities.declarations import CapabilityInformation, CapabilityKey, CapabilitySegment, Domain
from mountainash.core.capabilities.schema import CapabilityLevel, InformationLayer
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

SEGMENT = CapabilitySegment(
    domain=Domain.STRING,
    information=(
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS, subject="substring"),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.EXPR_CAPABLE,
            message="fixed upstream on the polars-backed narwhals path",
            issue="NW-STR-01",
            applicability=unbounded,
        ),
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.REPLACE, subject="replacement"),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.EXPR_CAPABLE,
            message="fixed upstream on the polars-backed narwhals path",
            issue="NW-STR-03",
            applicability=unbounded,
        ),
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_REPLACE, subject="replacement"),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.EXPR_CAPABLE,
            message="fixed upstream on the polars-backed narwhals path",
            issue="NW-STR-05",
            applicability=unbounded,
        ),
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.STARTS_WITH, subject="substring"),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.EXPR_CAPABLE,
            message="fixed upstream on the polars-backed narwhals path",
            issue="NW-STR-01",
            applicability=unbounded,
        ),
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.ENDS_WITH, subject="substring"),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.EXPR_CAPABLE,
            message="fixed upstream on the polars-backed narwhals path",
            issue="NW-STR-01",
            applicability=unbounded,
        ),
    ),
)
