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
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.TRUNCATE,
                subject="unit",
                selector=Selector(kind="exact", value="1w"),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            message="Narwhals datetime truncate, round, ceil, and floor reject the week unit '1w' and its 'week' alias on both dialects.",
            applicability=unbounded,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.TRUNCATE,
                subject="unit",
                selector=Selector(kind="exact", value="week"),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            message="Narwhals datetime truncate, round, ceil, and floor reject the week unit '1w' and its 'week' alias on both dialects.",
            applicability=unbounded,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ROUND,
                subject="unit",
                selector=Selector(kind="exact", value="1w"),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            message="Narwhals datetime truncate, round, ceil, and floor reject the week unit '1w' and its 'week' alias on both dialects.",
            applicability=unbounded,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ROUND,
                subject="unit",
                selector=Selector(kind="exact", value="week"),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            message="Narwhals datetime truncate, round, ceil, and floor reject the week unit '1w' and its 'week' alias on both dialects.",
            applicability=unbounded,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.CEIL,
                subject="unit",
                selector=Selector(kind="exact", value="1w"),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            message="Narwhals datetime truncate, round, ceil, and floor reject the week unit '1w' and its 'week' alias on both dialects.",
            applicability=unbounded,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.CEIL,
                subject="unit",
                selector=Selector(kind="exact", value="week"),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            message="Narwhals datetime truncate, round, ceil, and floor reject the week unit '1w' and its 'week' alias on both dialects.",
            applicability=unbounded,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.FLOOR,
                subject="unit",
                selector=Selector(kind="exact", value="1w"),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            message="Narwhals datetime truncate, round, ceil, and floor reject the week unit '1w' and its 'week' alias on both dialects.",
            applicability=unbounded,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.FLOOR,
                subject="unit",
                selector=Selector(kind="exact", value="week"),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            message="Narwhals datetime truncate, round, ceil, and floor reject the week unit '1w' and its 'week' alias on both dialects.",
            applicability=unbounded,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_XSD_DURATION,
                subject="failure_behavior",
                selector=Selector(kind="exact", value="throw"),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            message="Native XSD duration parsing converts invalid lexical values to null even when failure behavior is throw.",
            applicability=unbounded,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_XSD_PARTIAL_DATE,
                subject="failure_behavior",
                selector=Selector(kind="exact", value="throw"),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            message="Native XSD partial-date parsing converts invalid lexical values to null even when failure behavior is throw.",
            applicability=unbounded,
        ),
    ),
    policies=(
        CapabilityPolicyRule(
            key=CapabilityKey(FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_XSD_DURATION, "*"),
            level=CapabilityLevel.UNSUPPORTED,
            message="Invalid XSD duration lexicals silently become null during native parsing.",
            consumer=PolicyConsumer.RESULT_PROTECTION,
            action=PolicyAction.DETECT_NON_NULL_TO_NULL,
            applicability=unbounded,
        ),
        CapabilityPolicyRule(
            key=CapabilityKey(FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_XSD_PARTIAL_DATE, "*"),
            level=CapabilityLevel.UNSUPPORTED,
            message="Invalid XSD partial-date lexicals silently become null during native parsing.",
            consumer=PolicyConsumer.RESULT_PROTECTION,
            action=PolicyAction.DETECT_NON_NULL_TO_NULL,
            applicability=unbounded,
        ),
    ),
)
