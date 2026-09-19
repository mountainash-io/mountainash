"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations


from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_DATETIME
from mountainash.core.capabilities.declarations import Selector
from mountainash.core.capabilities.declarations import CapabilityKey
from mountainash.core.capabilities.schema import CapabilityLevel, InformationLayer, PolicyAction, PolicyConsumer


from mountainash.core.capabilities.declarations import CapabilityInformation, CapabilityPolicyRule
from mountainash.core.capabilities.declarations import CapabilitySegment

SEGMENT = CapabilitySegment(
    domain=Domain.DATETIME,
    information=(
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ROUND,
                subject="unit",
                selector=Selector(kind="exact", value="1y"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis's polars sub-backend translates interval addition via polars.duration(), which has no months/years kwarg -- round/ceil cannot compute the next calendar boundary (truncate/floor, which only need FLOOR, are unaffected); verified 2026-08-16, ibis 12.0.0",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ROUND,
                subject="unit",
                selector=Selector(kind="exact", value="1mo"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis's polars sub-backend translates interval addition via polars.duration(), which has no months/years kwarg -- round/ceil cannot compute the next calendar boundary (truncate/floor, which only need FLOOR, are unaffected); verified 2026-08-16, ibis 12.0.0",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ROUND,
                subject="unit",
                selector=Selector(kind="exact", value="1q"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis's polars sub-backend translates interval addition via polars.duration(), which has no months/years kwarg -- round/ceil cannot compute the next calendar boundary (truncate/floor, which only need FLOOR, are unaffected); verified 2026-08-16, ibis 12.0.0",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ROUND,
                subject="unit",
                selector=Selector(kind="exact", value="year"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis's polars sub-backend translates interval addition via polars.duration(), which has no months/years kwarg -- round/ceil cannot compute the next calendar boundary (truncate/floor, which only need FLOOR, are unaffected); verified 2026-08-16, ibis 12.0.0",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ROUND,
                subject="unit",
                selector=Selector(kind="exact", value="quarter"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis's polars sub-backend translates interval addition via polars.duration(), which has no months/years kwarg -- round/ceil cannot compute the next calendar boundary (truncate/floor, which only need FLOOR, are unaffected); verified 2026-08-16, ibis 12.0.0",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ROUND,
                subject="unit",
                selector=Selector(kind="exact", value="month"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis's polars sub-backend translates interval addition via polars.duration(), which has no months/years kwarg -- round/ceil cannot compute the next calendar boundary (truncate/floor, which only need FLOOR, are unaffected); verified 2026-08-16, ibis 12.0.0",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.CEIL,
                subject="unit",
                selector=Selector(kind="exact", value="1y"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis's polars sub-backend translates interval addition via polars.duration(), which has no months/years kwarg -- round/ceil cannot compute the next calendar boundary (truncate/floor, which only need FLOOR, are unaffected); verified 2026-08-16, ibis 12.0.0",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.CEIL,
                subject="unit",
                selector=Selector(kind="exact", value="1mo"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis's polars sub-backend translates interval addition via polars.duration(), which has no months/years kwarg -- round/ceil cannot compute the next calendar boundary (truncate/floor, which only need FLOOR, are unaffected); verified 2026-08-16, ibis 12.0.0",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.CEIL,
                subject="unit",
                selector=Selector(kind="exact", value="1q"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis's polars sub-backend translates interval addition via polars.duration(), which has no months/years kwarg -- round/ceil cannot compute the next calendar boundary (truncate/floor, which only need FLOOR, are unaffected); verified 2026-08-16, ibis 12.0.0",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.CEIL,
                subject="unit",
                selector=Selector(kind="exact", value="year"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis's polars sub-backend translates interval addition via polars.duration(), which has no months/years kwarg -- round/ceil cannot compute the next calendar boundary (truncate/floor, which only need FLOOR, are unaffected); verified 2026-08-16, ibis 12.0.0",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.CEIL,
                subject="unit",
                selector=Selector(kind="exact", value="quarter"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis's polars sub-backend translates interval addition via polars.duration(), which has no months/years kwarg -- round/ceil cannot compute the next calendar boundary (truncate/floor, which only need FLOOR, are unaffected); verified 2026-08-16, ibis 12.0.0",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.CEIL,
                subject="unit",
                selector=Selector(kind="exact", value="month"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis's polars sub-backend translates interval addition via polars.duration(), which has no months/years kwarg -- round/ceil cannot compute the next calendar boundary (truncate/floor, which only need FLOOR, are unaffected); verified 2026-08-16, ibis 12.0.0",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_XSD_DURATION,
                "failure_behavior",
                Selector(kind="exact", value="throw"),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-21",
            message="The native XSD duration parser silently converts invalid lexical values to null even when failure_behavior='throw'.",
        ),
        CapabilityInformation(
            key=CapabilityKey(
                FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_XSD_PARTIAL_DATE,
                "failure_behavior",
                Selector(kind="exact", value="throw"),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-21",
            message="The native XSD partial-date parser silently converts invalid lexical values to null even when failure_behavior='throw'.",
        ),
    ),
    policies=(
        CapabilityPolicyRule(
            key=CapabilityKey(FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_XSD_DURATION, "*"),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-21",
            message="Detect invalid XSD duration lexical values that the native parser converts from non-null input to null.",
            consumer=PolicyConsumer.RESULT_PROTECTION,
            action=PolicyAction.DETECT_NON_NULL_TO_NULL,
        ),
        CapabilityPolicyRule(
            key=CapabilityKey(FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_XSD_PARTIAL_DATE, "*"),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-21",
            message="Detect invalid XSD partial-date lexical values that the native parser converts from non-null input to null.",
            consumer=PolicyConsumer.RESULT_PROTECTION,
            action=PolicyAction.DETECT_NON_NULL_TO_NULL,
        ),
    ),
)
