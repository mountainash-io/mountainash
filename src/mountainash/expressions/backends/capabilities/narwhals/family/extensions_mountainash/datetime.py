"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import DivergenceManifestation
from mountainash.core.capabilities.declarations import ManifestationKey
from mountainash.core.capabilities.schema import CaptureValue
from mountainash.core.capabilities.schema import DivergenceKind
from mountainash.core.capabilities.schema import OperationTarget
from mountainash.core.capabilities.schema import Scenario

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
    manifestations=(
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_WEEK),
                scenario=Scenario(
                    arguments=(),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "values",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "ts",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="2024-01-01"),
                                                CaptureValue(tag="text", value="2024-01-07"),
                                                CaptureValue(tag="text", value="2024-06-15"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "shape",
                            CaptureValue(tag="text", value="collect expression"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="first week >= 1"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="dt.week_of_year() raises on pandas and all narwhals backends"),
                    ),
                ),
            ),
            impact="dt.week_of_year() raises on pandas and all narwhals backends",
            since="2026-08-06",
            workaround="Use a polars or ibis backend for ISO week extraction",
            issue="NW-DT-06",
        ),
    ),
)
