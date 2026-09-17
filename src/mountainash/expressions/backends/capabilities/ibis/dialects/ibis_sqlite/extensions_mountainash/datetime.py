"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_DATETIME
from mountainash.core.capabilities.declarations import Selector
from mountainash.core.capabilities.declarations import CapabilityKey
from mountainash.core.capabilities.schema import CapabilityLevel


from mountainash.core.capabilities.declarations import CapabilityAssertion
from mountainash.core.capabilities.schema import ValueClass
from mountainash.core.capabilities.declarations import CapabilitySegment

SEGMENT = CapabilitySegment(
    domain=Domain.DATETIME,
    capabilities=(
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.TRUNCATE,
                subject="unit",
                selector=Selector(kind="exact", value="1h"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.TRUNCATE,
                subject="unit",
                selector=Selector(kind="exact", value="1m"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.TRUNCATE,
                subject="unit",
                selector=Selector(kind="exact", value="1s"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.TRUNCATE,
                subject="unit",
                selector=Selector(kind="exact", value="1ms"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.TRUNCATE,
                subject="unit",
                selector=Selector(kind="exact", value="1us"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.TRUNCATE,
                subject="unit",
                selector=Selector(kind="exact", value="1q"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.TRUNCATE,
                subject="unit",
                selector=Selector(kind="exact", value="quarter"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.TRUNCATE,
                subject="unit",
                selector=Selector(kind="exact", value="hour"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.TRUNCATE,
                subject="unit",
                selector=Selector(kind="exact", value="minute"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.TRUNCATE,
                subject="unit",
                selector=Selector(kind="exact", value="second"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.TRUNCATE,
                subject="unit",
                selector=Selector(kind="exact", value="millisecond"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.TRUNCATE,
                subject="unit",
                selector=Selector(kind="exact", value="microsecond"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ROUND,
                subject="unit",
                selector=Selector(kind="exact", value="1h"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ROUND,
                subject="unit",
                selector=Selector(kind="exact", value="1m"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ROUND,
                subject="unit",
                selector=Selector(kind="exact", value="1s"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ROUND,
                subject="unit",
                selector=Selector(kind="exact", value="1ms"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ROUND,
                subject="unit",
                selector=Selector(kind="exact", value="1us"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ROUND,
                subject="unit",
                selector=Selector(kind="exact", value="1q"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ROUND,
                subject="unit",
                selector=Selector(kind="exact", value="quarter"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ROUND,
                subject="unit",
                selector=Selector(kind="exact", value="hour"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ROUND,
                subject="unit",
                selector=Selector(kind="exact", value="minute"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ROUND,
                subject="unit",
                selector=Selector(kind="exact", value="second"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ROUND,
                subject="unit",
                selector=Selector(kind="exact", value="millisecond"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ROUND,
                subject="unit",
                selector=Selector(kind="exact", value="microsecond"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.CEIL,
                subject="unit",
                selector=Selector(kind="exact", value="1h"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.CEIL,
                subject="unit",
                selector=Selector(kind="exact", value="1m"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.CEIL,
                subject="unit",
                selector=Selector(kind="exact", value="1s"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.CEIL,
                subject="unit",
                selector=Selector(kind="exact", value="1ms"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.CEIL,
                subject="unit",
                selector=Selector(kind="exact", value="1us"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.CEIL,
                subject="unit",
                selector=Selector(kind="exact", value="1q"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.CEIL,
                subject="unit",
                selector=Selector(kind="exact", value="quarter"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.CEIL,
                subject="unit",
                selector=Selector(kind="exact", value="hour"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.CEIL,
                subject="unit",
                selector=Selector(kind="exact", value="minute"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.CEIL,
                subject="unit",
                selector=Selector(kind="exact", value="second"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.CEIL,
                subject="unit",
                selector=Selector(kind="exact", value="millisecond"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.CEIL,
                subject="unit",
                selector=Selector(kind="exact", value="microsecond"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.FLOOR,
                subject="unit",
                selector=Selector(kind="exact", value="1h"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.FLOOR,
                subject="unit",
                selector=Selector(kind="exact", value="1m"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.FLOOR,
                subject="unit",
                selector=Selector(kind="exact", value="1s"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.FLOOR,
                subject="unit",
                selector=Selector(kind="exact", value="1ms"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.FLOOR,
                subject="unit",
                selector=Selector(kind="exact", value="1us"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.FLOOR,
                subject="unit",
                selector=Selector(kind="exact", value="1q"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.FLOOR,
                subject="unit",
                selector=Selector(kind="exact", value="quarter"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.FLOOR,
                subject="unit",
                selector=Selector(kind="exact", value="hour"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.FLOOR,
                subject="unit",
                selector=Selector(kind="exact", value="minute"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.FLOOR,
                subject="unit",
                selector=Selector(kind="exact", value="second"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.FLOOR,
                subject="unit",
                selector=Selector(kind="exact", value="millisecond"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.FLOOR,
                subject="unit",
                selector=Selector(kind="exact", value="microsecond"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.TRUNCATE,
                subject="unit",
                selector=Selector(kind="value_class", value=ValueClass.DURATION_MULTIPLIER),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-18",
            message="ibis-sqlite has no TimestampBucket compilation rule -- a multiplied MA duration (e.g. dt.truncate('2d')) is unsupported there; verified 2026-08-18, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ROUND,
                subject="unit",
                selector=Selector(kind="value_class", value=ValueClass.DURATION_MULTIPLIER),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-18",
            message="ibis-sqlite has no TimestampBucket compilation rule -- a multiplied MA duration (e.g. dt.truncate('2d')) is unsupported there; verified 2026-08-18, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.CEIL,
                subject="unit",
                selector=Selector(kind="value_class", value=ValueClass.DURATION_MULTIPLIER),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-18",
            message="ibis-sqlite has no TimestampBucket compilation rule -- a multiplied MA duration (e.g. dt.truncate('2d')) is unsupported there; verified 2026-08-18, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.FLOOR,
                subject="unit",
                selector=Selector(kind="value_class", value=ValueClass.DURATION_MULTIPLIER),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-18",
            message="ibis-sqlite has no TimestampBucket compilation rule -- a multiplied MA duration (e.g. dt.truncate('2d')) is unsupported there; verified 2026-08-18, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_XSD_DURATION, subject="*"),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-21",
            message="ibis-sqlite has no XSD lexical parser; gate before backend dispatch",
            probe_exempt="XSD lexical parser behavior is covered by conform temporal contract tests",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_XSD_PARTIAL_DATE, subject="*"),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-21",
            message="ibis-sqlite has no XSD lexical parser; gate before backend dispatch",
            probe_exempt="XSD lexical parser behavior is covered by conform temporal contract tests",
        ),
    ),
)
