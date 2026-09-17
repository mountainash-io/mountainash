"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_DATETIME
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
                operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.EXTRACT,
                subject="component",
                selector=Selector(kind="exact", value="MONDAY_WEEK"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-15",
            message="the native backend has no primitive for this extract component (verified by semantic probe; see capabilities/datetime/extract.py)",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.EXTRACT,
                subject="component",
                selector=Selector(kind="exact", value="NANOSECOND"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-15",
            message="the native backend has no primitive for this extract component (verified by semantic probe; see capabilities/datetime/extract.py)",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.EXTRACT,
                subject="component",
                selector=Selector(kind="exact", value="PICOSECOND"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-15",
            message="the native backend has no primitive for this extract component (verified by semantic probe; see capabilities/datetime/extract.py)",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.EXTRACT,
                subject="component",
                selector=Selector(kind="exact", value="SUNDAY_WEEK"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-15",
            message="the native backend has no primitive for this extract component (verified by semantic probe; see capabilities/datetime/extract.py)",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.EXTRACT,
                subject="component",
                selector=Selector(kind="exact", value="TIMEZONE_OFFSET"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-15",
            message="the native backend has no primitive for this extract component (verified by semantic probe; see capabilities/datetime/extract.py)",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.EXTRACT,
                subject="component",
                selector=Selector(kind="exact", value="US_WEEK"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-15",
            message="the native backend has no primitive for this extract component (verified by semantic probe; see capabilities/datetime/extract.py)",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.EXTRACT,
                subject="component",
                selector=Selector(kind="exact", value="US_YEAR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-15",
            message="the native backend has no primitive for this extract component (verified by semantic probe; see capabilities/datetime/extract.py)",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.EXTRACT_BOOLEAN,
                subject="component",
                selector=Selector(kind="exact", value="IS_DST"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-15",
            message="extract_boolean(IS_DST) is a placeholder (constant False) on all backends; deferred to backlog item 65 (is-dst-placeholder-implementation)",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.STRPTIME_DATE,
                subject="failure_behavior",
                selector=Selector(kind="exact", value="null"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-21",
            message="null-on-invalid custom temporal parsing is supported only by Polars",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.STRPTIME_TIMESTAMP,
                subject="failure_behavior",
                selector=Selector(kind="exact", value="null"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-21",
            message="null-on-invalid custom temporal parsing is supported only by Polars",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.ASSUME_TIMEZONE,
                subject="timezone",
                selector=Selector(kind="value_class", value=ValueClass.IANA_TIMEZONE),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-25",
            message="assume_timezone silently drops the timezone (returns a naive timestamp) — the tz argument is ignored; only polars attaches the timezone",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.LOCAL_TIMESTAMP,
                subject="timezone",
                selector=Selector(kind="value_class", value=ValueClass.IANA_TIMEZONE),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-29",
            message="local_timestamp returns the UTC wall clock, not the target-zone wall clock -- ibis has no timezone method and the naive re-cast discards the conversion (verified 2026-07-29, ibis 12.0.0/duckdb: 12:00 instead of 17:30 for Asia/Kolkata)",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.STRPTIME_TIMESTAMP,
                subject="timezone",
                selector=Selector(kind="value_class", value=ValueClass.IANA_TIMEZONE),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-15",
            message="strptime_timestamp silently drops the timezone (returns a naive timestamp) on ibis -- ibis has no timezone primitives, matching assume_timezone/to_timezone/local_timestamp/extract.timezone",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.EXTRACT,
                subject="timezone",
                selector=Selector(kind="value_class", value=ValueClass.IANA_TIMEZONE),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-15",
            message="ibis has no timezone primitives; extract/extract_boolean's timezone option is silently ignored (the local component is read from the stored value, not the target zone) -- see capabilities/datetime/extract.py",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.EXTRACT_BOOLEAN,
                subject="timezone",
                selector=Selector(kind="value_class", value=ValueClass.IANA_TIMEZONE),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-15",
            message="ibis has no timezone primitives; extract/extract_boolean's timezone option is silently ignored (the local component is read from the stored value, not the target zone) -- see capabilities/datetime/extract.py",
        ),
    ),
)
