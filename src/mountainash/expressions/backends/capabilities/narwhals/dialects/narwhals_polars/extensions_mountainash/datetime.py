"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations


from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_DATETIME
from mountainash.core.capabilities.declarations import Selector
from mountainash.core.capabilities.declarations import CapabilityKey
from mountainash.core.capabilities.schema import CapabilityLevel, InformationLayer


from mountainash.core.capabilities.declarations import CapabilityInformation, CapabilityPolicyRule
from mountainash.core.capabilities.schema import PolicyAction, PolicyConsumer
from mountainash.core.capabilities.declarations import CapabilitySegment

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
            since="2026-08-16",
            message="Narwhals datetime truncate, round, ceil, and floor reject the week unit '1w' and its 'week' alias on both dialects.",
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.TRUNCATE,
                subject="unit",
                selector=Selector(kind="exact", value="week"),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="Narwhals datetime truncate, round, ceil, and floor reject the week unit '1w' and its 'week' alias on both dialects.",
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ROUND,
                subject="unit",
                selector=Selector(kind="exact", value="1w"),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="Narwhals datetime truncate, round, ceil, and floor reject the week unit '1w' and its 'week' alias on both dialects.",
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ROUND,
                subject="unit",
                selector=Selector(kind="exact", value="week"),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="Narwhals datetime truncate, round, ceil, and floor reject the week unit '1w' and its 'week' alias on both dialects.",
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.CEIL,
                subject="unit",
                selector=Selector(kind="exact", value="1w"),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="Narwhals datetime truncate, round, ceil, and floor reject the week unit '1w' and its 'week' alias on both dialects.",
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.CEIL,
                subject="unit",
                selector=Selector(kind="exact", value="week"),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="Narwhals datetime truncate, round, ceil, and floor reject the week unit '1w' and its 'week' alias on both dialects.",
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.FLOOR,
                subject="unit",
                selector=Selector(kind="exact", value="1w"),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="Narwhals datetime truncate, round, ceil, and floor reject the week unit '1w' and its 'week' alias on both dialects.",
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.FLOOR,
                subject="unit",
                selector=Selector(kind="exact", value="week"),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="Narwhals datetime truncate, round, ceil, and floor reject the week unit '1w' and its 'week' alias on both dialects.",
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_XSD_DURATION,
                subject="failure_behavior",
                selector=Selector(kind="exact", value="throw"),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-21",
            message="Native XSD duration parsing converts invalid lexical values to null even when failure behavior is throw.",
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_XSD_PARTIAL_DATE,
                subject="failure_behavior",
                selector=Selector(kind="exact", value="throw"),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-21",
            message="Native XSD partial-date parsing converts invalid lexical values to null even when failure behavior is throw.",
        ),
    ),
    policies=(
        CapabilityPolicyRule(
            key=CapabilityKey(FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_XSD_DURATION, "*"),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-21",
            message="Invalid XSD duration lexicals silently become null during native parsing.",
            consumer=PolicyConsumer.RESULT_PROTECTION,
            action=PolicyAction.DETECT_NON_NULL_TO_NULL,
        ),
        CapabilityPolicyRule(
            key=CapabilityKey(FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_XSD_PARTIAL_DATE, "*"),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-21",
            message="Invalid XSD partial-date lexicals silently become null during native parsing.",
            consumer=PolicyConsumer.RESULT_PROTECTION,
            action=PolicyAction.DETECT_NON_NULL_TO_NULL,
        ),
    ),
)
