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
from mountainash.core.capabilities.declarations import Selector
from mountainash.core.capabilities.declarations import CapabilityKey
from mountainash.core.capabilities.schema import CapabilityLevel


from mountainash.core.capabilities.declarations import CapabilityAssertion
from mountainash.core.capabilities.schema import Boundary
from mountainash.core.capabilities.schema import Enforcement
from mountainash.core.capabilities.schema import ResidueSignal
from mountainash.core.capabilities.declarations import CapabilitySegment

SEGMENT = CapabilitySegment(
    domain=Domain.DATETIME,
    capabilities=(
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.TRUNCATE,
                subject="unit",
                selector=Selector(kind="exact", value="1w"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="narwhals dt.truncate rejects the week unit '1w' (and its friendly alias 'week') on both dialects",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.TRUNCATE,
                subject="unit",
                selector=Selector(kind="exact", value="week"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="narwhals dt.truncate rejects the week unit '1w' (and its friendly alias 'week') on both dialects",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ROUND,
                subject="unit",
                selector=Selector(kind="exact", value="1w"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="narwhals dt.truncate rejects the week unit '1w' (and its friendly alias 'week') on both dialects",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ROUND,
                subject="unit",
                selector=Selector(kind="exact", value="week"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="narwhals dt.truncate rejects the week unit '1w' (and its friendly alias 'week') on both dialects",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.CEIL,
                subject="unit",
                selector=Selector(kind="exact", value="1w"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="narwhals dt.truncate rejects the week unit '1w' (and its friendly alias 'week') on both dialects",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.CEIL,
                subject="unit",
                selector=Selector(kind="exact", value="week"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="narwhals dt.truncate rejects the week unit '1w' (and its friendly alias 'week') on both dialects",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.FLOOR,
                subject="unit",
                selector=Selector(kind="exact", value="1w"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="narwhals dt.truncate rejects the week unit '1w' (and its friendly alias 'week') on both dialects",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.FLOOR,
                subject="unit",
                selector=Selector(kind="exact", value="week"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="narwhals dt.truncate rejects the week unit '1w' (and its friendly alias 'week') on both dialects",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_XSD_DURATION, subject="*"),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-21",
            message="invalid XSD lexical values are converted to null by the residue policy",
            boundary=Boundary.MATERIALIZE,
            enforcement=Enforcement.MATERIALIZE_RESIDUE,
            signal=ResidueSignal.NON_NULL_TO_NULL,
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_XSD_PARTIAL_DATE, subject="*"),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-21",
            message="invalid XSD lexical values are converted to null by the residue policy",
            boundary=Boundary.MATERIALIZE,
            enforcement=Enforcement.MATERIALIZE_RESIDUE,
            signal=ResidueSignal.NON_NULL_TO_NULL,
        ),
    ),
    manifestations=(
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.DATE),
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
                                                CaptureValue(tag="text", value="2024-03-15T10:30"),
                                                CaptureValue(tag="text", value="2024-07-20T14:00"),
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
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="text", value="2024-03-15"),
                                CaptureValue(tag="text", value="2024-07-20"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="dt.date() raises on pandas and narwhals-pandas"),
                    ),
                ),
            ),
            impact="dt.date() raises on pandas and narwhals-pandas",
            since="2026-08-06",
            workaround="Use polars/narwhals-polars or ibis",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.DATE),
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
                                                CaptureValue(tag="text", value="2024-03-15T10:30:45"),
                                                CaptureValue(tag="text", value="2024-12-25T23:59"),
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
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="text", value="2024-03-15"),
                                CaptureValue(tag="text", value="2024-12-25"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="dt.date() raises on narwhals-pandas"),
                    ),
                ),
            ),
            impact="dt.date() raises on narwhals-pandas",
            since="2026-08-06",
            workaround="Use narwhals-polars, polars, or ibis",
            issue="NW-DT-07",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.DAYS_IN_MONTH),
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
                                                CaptureValue(tag="text", value="2024-02-15"),
                                                CaptureValue(tag="text", value="2024-03-15"),
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
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="integer", value="29"),
                                CaptureValue(tag="integer", value="31"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="datetime enrichment operations raise on pandas/narwhals"),
                    ),
                ),
            ),
            impact="datetime enrichment operations raise on pandas/narwhals",
            since="2026-08-06",
            workaround="Use a polars or ibis backend",
            issue=None,
        ),
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
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.MONTH_END),
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
                                                CaptureValue(tag="text", value="2024-02-15"),
                                                CaptureValue(tag="text", value="2024-03-15"),
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
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="integer", value="29"),
                                CaptureValue(tag="integer", value="31"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="datetime enrichment operations raise on pandas/narwhals"),
                    ),
                ),
            ),
            impact="datetime enrichment operations raise on pandas/narwhals",
            since="2026-08-06",
            workaround="Use a polars or ibis backend",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.MONTH_START),
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
                                                CaptureValue(tag="text", value="2024-03-15T10:30"),
                                                CaptureValue(tag="text", value="2024-07-20T14:00"),
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
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="integer", value="1"),
                                CaptureValue(tag="integer", value="1"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="datetime enrichment operations raise on pandas/narwhals"),
                    ),
                ),
            ),
            impact="datetime enrichment operations raise on pandas/narwhals",
            since="2026-08-06",
            workaround="Use a polars or ibis backend",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.TIME),
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
                                                CaptureValue(tag="text", value="2024-03-15T10:30"),
                                                CaptureValue(tag="text", value="2024-07-20T14:00"),
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
                        CaptureValue(tag="text", value="length 2"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="datetime enrichment operations raise on pandas/narwhals"),
                    ),
                ),
            ),
            impact="datetime enrichment operations raise on pandas/narwhals",
            since="2026-08-06",
            workaround="Use a polars or ibis backend",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.TIME),
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
                                                CaptureValue(tag="text", value="2024-03-15T10:30:45"),
                                                CaptureValue(tag="text", value="2024-12-25T23:59"),
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
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="text", value="10:30:45"),
                                CaptureValue(tag="text", value="23:59:00"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="dt.time() raises on narwhals-polars/narwhals-pandas"),
                    ),
                ),
            ),
            impact="dt.time() raises on narwhals-polars/narwhals-pandas",
            since="2026-08-06",
            workaround="Use a polars or ibis backend for dt.time()",
            issue="NW-DT-03",
        ),
    ),
)
