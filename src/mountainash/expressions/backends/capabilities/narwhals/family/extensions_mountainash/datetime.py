"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_DATETIME
from mountainash.core.capabilities.declarations import CapabilityKey
from mountainash.core.capabilities.schema import CapabilityLevel


from mountainash.core.capabilities.declarations import CapabilityAssertion
from mountainash.core.capabilities.declarations import CapabilitySegment

SEGMENT = CapabilitySegment(
    domain=Domain.DATETIME,
    capabilities=(
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_TEMPORAL_ANY, subject="*"),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-25",
            message="temporal-any parsing requires a row-wise native parser",
            probe_exempt="Temporal-any parsing is covered by conform temporal contract tests",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_DEFAULT, subject="*"),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-25",
            message="default datetime parsing requires the Polars native parser",
            probe_exempt="Default datetime parsing is covered by conform temporal contract tests",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_YEARS, subject="years"),
            level=CapabilityLevel.LITERAL_ONLY,
            since="2026-07-05",
            message="Narwhals datetime offset operations require literal integer values",
            workaround="Use a literal integer for the offset amount",
            issue="NW-DT-01",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MONTHS, subject="months"),
            level=CapabilityLevel.LITERAL_ONLY,
            since="2026-07-05",
            message="Narwhals datetime offset operations require literal integer values",
            workaround="Use a literal integer for the offset amount",
            issue="NW-DT-01",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_DAYS, subject="days"),
            level=CapabilityLevel.LITERAL_ONLY,
            since="2026-07-05",
            message="Narwhals datetime offset operations require literal integer values",
            workaround="Use a literal integer for the offset amount",
            issue="NW-DT-01",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_HOURS, subject="hours"),
            level=CapabilityLevel.LITERAL_ONLY,
            since="2026-07-05",
            message="Narwhals datetime offset operations require literal integer values",
            workaround="Use a literal integer for the offset amount",
            issue="NW-DT-01",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MINUTES, subject="minutes"),
            level=CapabilityLevel.LITERAL_ONLY,
            since="2026-07-05",
            message="Narwhals datetime offset operations require literal integer values",
            workaround="Use a literal integer for the offset amount",
            issue="NW-DT-01",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_SECONDS, subject="seconds"),
            level=CapabilityLevel.LITERAL_ONLY,
            since="2026-07-05",
            message="Narwhals datetime offset operations require literal integer values",
            workaround="Use a literal integer for the offset amount",
            issue="NW-DT-01",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MILLISECONDS, subject="milliseconds"),
            level=CapabilityLevel.LITERAL_ONLY,
            since="2026-07-05",
            message="Narwhals datetime offset operations require literal integer values",
            workaround="Use a literal integer for the offset amount",
            issue="NW-DT-01",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MICROSECONDS, subject="microseconds"),
            level=CapabilityLevel.LITERAL_ONLY,
            since="2026-07-05",
            message="Narwhals datetime offset operations require literal integer values",
            workaround="Use a literal integer for the offset amount",
            issue="NW-DT-01",
        ),
    ),
)
