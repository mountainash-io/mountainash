"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.applicability import unbounded
from mountainash.core.capabilities.declarations import (
    CapabilityInformation,
    CapabilityKey,
    CapabilitySegment,
    Domain,
    Selector,
)
from mountainash.core.capabilities.schema import CapabilityLevel, InformationLayer, ValueClass
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_DATETIME

SEGMENT = CapabilitySegment(
    domain=Domain.DATETIME,
    information=(
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_TEMPORAL_ANY, subject="*"),
            level=CapabilityLevel.UNSUPPORTED,
            message="temporal-any parsing requires a row-wise native parser",
            layer=InformationLayer.NATIVE,
            applicability=unbounded,
        ),
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_DEFAULT, subject="*"),
            level=CapabilityLevel.UNSUPPORTED,
            message="default datetime parsing requires the Polars native parser",
            layer=InformationLayer.NATIVE,
            applicability=unbounded,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.TO_TIMEZONE,
                subject="timezone",
                selector=Selector(kind="value_class", value=ValueClass.IANA_TIMEZONE),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            message="to_timezone is correct only at the materialization boundary -- the target zone lives in the ibis output dtype, not in the engine (SQL is a bare CAST AS TIMESTAMPTZ), so any expression composed on the result raises UnsupportedOperationError (verified 2026-07-29, ibis 12.0.0/duckdb)",
            layer=InformationLayer.PUBLIC,
            applicability=unbounded,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.IS_DST,
                subject="timezone",
                selector=Selector(kind="value_class", value=ValueClass.IANA_TIMEZONE),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            message="is_dst is not supported on ibis -- ibis has no DST/timezone-offset primitive to build on (verified 2026-08-16, ibis 12.0.0/duckdb)",
            layer=InformationLayer.PUBLIC,
            applicability=unbounded,
        ),
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_YEARS, subject="years"),
            level=CapabilityLevel.LITERAL_ONLY,
            message="Ibis datetime offset operations require literal integer values",
            workaround="Use a literal integer for the offset amount",
            issue="IB-DT-01",
            layer=InformationLayer.NATIVE,
            applicability=unbounded,
        ),
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MONTHS, subject="months"),
            level=CapabilityLevel.LITERAL_ONLY,
            message="Ibis datetime offset operations require literal integer values",
            workaround="Use a literal integer for the offset amount",
            issue="IB-DT-01",
            layer=InformationLayer.NATIVE,
            applicability=unbounded,
        ),
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_DAYS, subject="days"),
            level=CapabilityLevel.LITERAL_ONLY,
            message="Ibis datetime offset operations require literal integer values",
            workaround="Use a literal integer for the offset amount",
            issue="IB-DT-01",
            layer=InformationLayer.NATIVE,
            applicability=unbounded,
        ),
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_HOURS, subject="hours"),
            level=CapabilityLevel.LITERAL_ONLY,
            message="Ibis datetime offset operations require literal integer values",
            workaround="Use a literal integer for the offset amount",
            issue="IB-DT-01",
            layer=InformationLayer.NATIVE,
            applicability=unbounded,
        ),
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MINUTES, subject="minutes"),
            level=CapabilityLevel.LITERAL_ONLY,
            message="Ibis datetime offset operations require literal integer values",
            workaround="Use a literal integer for the offset amount",
            issue="IB-DT-01",
            layer=InformationLayer.NATIVE,
            applicability=unbounded,
        ),
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_SECONDS, subject="seconds"),
            level=CapabilityLevel.LITERAL_ONLY,
            message="Ibis datetime offset operations require literal integer values",
            workaround="Use a literal integer for the offset amount",
            issue="IB-DT-01",
            layer=InformationLayer.NATIVE,
            applicability=unbounded,
        ),
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MILLISECONDS, subject="milliseconds"),
            level=CapabilityLevel.LITERAL_ONLY,
            message="Ibis datetime offset operations require literal integer values",
            workaround="Use a literal integer for the offset amount",
            issue="IB-DT-01",
            layer=InformationLayer.NATIVE,
            applicability=unbounded,
        ),
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MICROSECONDS, subject="microseconds"),
            level=CapabilityLevel.LITERAL_ONLY,
            message="Ibis datetime offset operations require literal integer values",
            workaround="Use a literal integer for the offset amount",
            issue="IB-DT-01",
            layer=InformationLayer.NATIVE,
            applicability=unbounded,
        ),
    ),
)
