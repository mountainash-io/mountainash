"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.applicability import unbounded
from mountainash.core.capabilities.declarations import (
    CapabilityInformation,
    CapabilityKey,
    CapabilityPolicyRule,
    CapabilitySegment,
    Domain,
    Selector,
)
from mountainash.core.capabilities.schema import CapabilityLevel, InformationLayer, PolicyAction, PolicyConsumer
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_DATETIME

SEGMENT = CapabilitySegment(
    domain=Domain.DATETIME,
    information=(
        CapabilityInformation(
            key=CapabilityKey(
                FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_XSD_DURATION,
                "failure_behavior",
                Selector(kind="exact", value="throw"),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            message="The native XSD duration parser silently converts invalid lexical values to null even when failure_behavior='throw'.",
            applicability=unbounded,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_XSD_PARTIAL_DATE,
                "failure_behavior",
                Selector(kind="exact", value="throw"),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            message="The native XSD partial-date parser silently converts invalid lexical values to null even when failure_behavior='throw'.",
            applicability=unbounded,
        ),
    ),
    policies=(
        CapabilityPolicyRule(
            key=CapabilityKey(FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_XSD_DURATION, "*"),
            level=CapabilityLevel.UNSUPPORTED,
            message="Detect invalid XSD duration lexical values that the native parser converts from non-null input to null.",
            consumer=PolicyConsumer.RESULT_PROTECTION,
            action=PolicyAction.DETECT_NON_NULL_TO_NULL,
            applicability=unbounded,
        ),
        CapabilityPolicyRule(
            key=CapabilityKey(FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_XSD_PARTIAL_DATE, "*"),
            level=CapabilityLevel.UNSUPPORTED,
            message="Detect invalid XSD partial-date lexical values that the native parser converts from non-null input to null.",
            consumer=PolicyConsumer.RESULT_PROTECTION,
            action=PolicyAction.DETECT_NON_NULL_TO_NULL,
            applicability=unbounded,
        ),
    ),
)
