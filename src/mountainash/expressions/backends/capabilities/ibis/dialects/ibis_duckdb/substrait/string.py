"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING
from mountainash.core.capabilities.declarations import Selector
from mountainash.core.capabilities.declarations import CapabilityKey
from mountainash.core.capabilities.schema import CapabilityLevel, InformationLayer


from mountainash.core.capabilities.declarations import CapabilityInformation
from mountainash.core.capabilities.declarations import CapabilitySegment

SEGMENT = CapabilitySegment(
    domain=Domain.STRING,
    information=(
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_SENSITIVE"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.COUNT_SUBSTRING,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_SENSITIVE"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.ENDS_WITH,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_SENSITIVE"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.LIKE,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_SENSITIVE"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REPLACE,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_SENSITIVE"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.STARTS_WITH,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_SENSITIVE"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.STRPOS,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_SENSITIVE"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_SENSITIVE"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_REPLACE,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_SENSITIVE"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_SPLIT,
                subject="case_sensitivity",
                selector=Selector(kind="exact", value="CASE_SENSITIVE"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH,
                subject="multiline",
                selector=Selector(kind="exact", value="MULTILINE_DISABLED"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_REPLACE,
                subject="multiline",
                selector=Selector(kind="exact", value="MULTILINE_DISABLED"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_SPLIT,
                subject="multiline",
                selector=Selector(kind="exact", value="MULTILINE_DISABLED"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH,
                subject="dotall",
                selector=Selector(kind="exact", value="DOTALL_DISABLED"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_REPLACE,
                subject="dotall",
                selector=Selector(kind="exact", value="DOTALL_DISABLED"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_SPLIT,
                subject="dotall",
                selector=Selector(kind="exact", value="DOTALL_DISABLED"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.LOWER,
                subject="char_set",
                selector=Selector(kind="exact", value="UTF8"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.UPPER,
                subject="char_set",
                selector=Selector(kind="exact", value="UTF8"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.CAPITALIZE,
                subject="char_set",
                selector=Selector(kind="exact", value="UTF8"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.CENTER,
                subject="padding",
                selector=Selector(kind="exact", value="RIGHT"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="RIGHT is the builder default, so the explicit option is observably equivalent to omission and cannot discriminate",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_STRING.SUBSTRING,
                subject="negative_start",
                selector=Selector(kind="exact", value="WRAP_FROM_END"),
            ),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-23",
            message="The builder default emits WRAP_FROM_END, so the explicit option is observably equivalent to omission and cannot discriminate",
            layer=InformationLayer.NATIVE,
        ),
    ),
)
