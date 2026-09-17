"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_DATETIME
from mountainash.core.capabilities.declarations import Selector
from mountainash.core.capabilities.declarations import CapabilityKey
from mountainash.core.capabilities.schema import CapabilityLevel


from mountainash.core.capabilities.declarations import CapabilityAssertion
from mountainash.core.capabilities.declarations import CapabilitySegment

SEGMENT = CapabilitySegment(
    domain=Domain.DATETIME,
    capabilities=(
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.ROUND_TEMPORAL,
                subject="unit",
                selector=Selector(kind="exact", value="HOUR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite TimestampTruncate has no support for units finer than DAY (HOUR/MINUTE/SECOND/MILLISECOND/MICROSECOND); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.ROUND_TEMPORAL,
                subject="unit",
                selector=Selector(kind="exact", value="MINUTE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite TimestampTruncate has no support for units finer than DAY (HOUR/MINUTE/SECOND/MILLISECOND/MICROSECOND); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.ROUND_TEMPORAL,
                subject="unit",
                selector=Selector(kind="exact", value="SECOND"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite TimestampTruncate has no support for units finer than DAY (HOUR/MINUTE/SECOND/MILLISECOND/MICROSECOND); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.ROUND_TEMPORAL,
                subject="unit",
                selector=Selector(kind="exact", value="MILLISECOND"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite TimestampTruncate has no support for units finer than DAY (HOUR/MINUTE/SECOND/MILLISECOND/MICROSECOND); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.ROUND_TEMPORAL,
                subject="unit",
                selector=Selector(kind="exact", value="MICROSECOND"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite TimestampTruncate has no support for units finer than DAY (HOUR/MINUTE/SECOND/MILLISECOND/MICROSECOND); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.ROUND_CALENDAR,
                subject="unit",
                selector=Selector(kind="exact", value="HOUR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite TimestampTruncate has no support for units finer than DAY (HOUR/MINUTE/SECOND/MILLISECOND/MICROSECOND); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.ROUND_CALENDAR,
                subject="unit",
                selector=Selector(kind="exact", value="MINUTE"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite TimestampTruncate has no support for units finer than DAY (HOUR/MINUTE/SECOND/MILLISECOND/MICROSECOND); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.ROUND_CALENDAR,
                subject="unit",
                selector=Selector(kind="exact", value="SECOND"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite TimestampTruncate has no support for units finer than DAY (HOUR/MINUTE/SECOND/MILLISECOND/MICROSECOND); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.ROUND_CALENDAR,
                subject="unit",
                selector=Selector(kind="exact", value="MILLISECOND"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite TimestampTruncate has no support for units finer than DAY (HOUR/MINUTE/SECOND/MILLISECOND/MICROSECOND); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.ROUND_CALENDAR,
                subject="unit",
                selector=Selector(kind="exact", value="MICROSECOND"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite TimestampTruncate has no support for units finer than DAY (HOUR/MINUTE/SECOND/MILLISECOND/MICROSECOND); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.ROUND_TEMPORAL,
                subject="multiple",
                selector=Selector(kind="exact", value="2"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampBucket compilation rule -- multiple > 1 is unsupported for every unit; verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.ROUND_CALENDAR,
                subject="multiple",
                selector=Selector(kind="exact", value="3"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis-sqlite has no TimestampBucket compilation rule -- multiple > 1 is unsupported for every unit; verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.STRPTIME_DATE, subject="*"),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-30",
            message="ibis-sqlite has no compilation rule for StringToDate/StringToTimestamp (OperationNotDefinedError); format-driven parsing is unavailable on this dialect, so it is gated rather than left to fail natively",
            probe_exempt="whole-op gate on a WILDCARD_PARAM fact; cannot be keyed on an OpSpec param (OpSpecs are indexed by concrete argument name) — verified by the dedicated cross-backend gate tests in test_datetime_strptime_format.py",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.STRPTIME_TIMESTAMP, subject="*"),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-30",
            message="ibis-sqlite has no compilation rule for StringToDate/StringToTimestamp (OperationNotDefinedError); format-driven parsing is unavailable on this dialect, so it is gated rather than left to fail natively",
            probe_exempt="whole-op gate on a WILDCARD_PARAM fact; cannot be keyed on an OpSpec param (OpSpecs are indexed by concrete argument name) — verified by the dedicated cross-backend gate tests in test_datetime_strptime_format.py",
        ),
    ),
)
