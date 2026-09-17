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
                selector=Selector(kind="exact", value="ISO_WEEK"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-15",
            message="the native backend has no primitive for this extract component (verified by semantic probe; see capabilities/datetime/extract.py)",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.EXTRACT,
                subject="component",
                selector=Selector(kind="exact", value="ISO_YEAR"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-15",
            message="the native backend has no primitive for this extract component (verified by semantic probe; see capabilities/datetime/extract.py)",
        ),
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
                selector=Selector(kind="exact", value="UNIX_TIME"),
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
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.STRPTIME_DATE, subject="*"),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-30",
            message="narwhals raises NotImplementedError for str.to_date() on the default pandas backend (it would return an object-dtype Series, diverging from the polars API); str.to_datetime() is unaffected and stays supported",
            probe_exempt="whole-op gate on a WILDCARD_PARAM fact; cannot be keyed on an OpSpec param (OpSpecs are indexed by concrete argument name) — verified by the dedicated cross-backend gate tests in test_datetime_strptime_format.py",
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
    ),
)
