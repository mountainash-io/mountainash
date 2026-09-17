"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import CapabilitySegment
from mountainash.core.capabilities.declarations import DivergenceManifestation
from mountainash.core.capabilities.declarations import Domain
from mountainash.core.capabilities.declarations import ManifestationKey
from mountainash.core.capabilities.schema import CaptureValue
from mountainash.core.capabilities.schema import DivergenceKind
from mountainash.core.capabilities.schema import OperationTarget
from mountainash.core.capabilities.schema import Scenario
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_COMPARISON

SEGMENT = CapabilitySegment(
    domain=Domain.COMPARISON,
    capabilities=(),
    manifestations=(
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_COMPARISON.IS_DUPLICATED),
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
                                        "idx",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="0"),
                                                CaptureValue(tag="integer", value="1"),
                                                CaptureValue(tag="integer", value="2"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "name",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="a"),
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="null", value=""),
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
                            CaptureValue(tag="text", value="relation sorted by idx"),
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
                                CaptureValue(tag="bool", value="false"),
                                CaptureValue(tag="bool", value="true"),
                                CaptureValue(tag="bool", value="true"),
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
                        CaptureValue(tag="text", value="historical WindowFunction translation failure"),
                    ),
                ),
            ),
            impact="window operations raise on ibis-polars",
            since="2026-08-06",
            workaround="Use ibis-duckdb/ibis-sqlite or a polars/narwhals backend",
            issue="IB-WIN-01",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_COMPARISON.IS_DUPLICATED),
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
                                        "idx",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="0"),
                                                CaptureValue(tag="integer", value="1"),
                                                CaptureValue(tag="integer", value="2"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "val",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="10"),
                                                CaptureValue(tag="integer", value="20"),
                                                CaptureValue(tag="integer", value="30"),
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
                            CaptureValue(tag="text", value="relation sorted by idx"),
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
                                CaptureValue(tag="bool", value="false"),
                                CaptureValue(tag="bool", value="false"),
                                CaptureValue(tag="bool", value="false"),
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
                        CaptureValue(tag="text", value="historical WindowFunction translation failure"),
                    ),
                ),
            ),
            impact="window operations raise on ibis-polars",
            since="2026-08-06",
            workaround="Use ibis-duckdb/ibis-sqlite or a polars/narwhals backend",
            issue="IB-WIN-01",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_COMPARISON.IS_DUPLICATED),
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
                                        "idx",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="0"),
                                                CaptureValue(tag="integer", value="1"),
                                                CaptureValue(tag="integer", value="2"),
                                                CaptureValue(tag="integer", value="3"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "name",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="a"),
                                                CaptureValue(tag="text", value="b"),
                                                CaptureValue(tag="text", value="a"),
                                                CaptureValue(tag="text", value="c"),
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
                            CaptureValue(tag="text", value="relation sorted by idx"),
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
                                CaptureValue(tag="bool", value="true"),
                                CaptureValue(tag="bool", value="false"),
                                CaptureValue(tag="bool", value="true"),
                                CaptureValue(tag="bool", value="false"),
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
                        CaptureValue(tag="text", value="historical WindowFunction translation failure"),
                    ),
                ),
            ),
            impact="window operations raise on ibis-polars",
            since="2026-08-06",
            workaround="Use ibis-duckdb/ibis-sqlite or a polars/narwhals backend",
            issue="IB-WIN-01",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_COMPARISON.IS_DUPLICATED),
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
                                        "idx",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="0"),
                                                CaptureValue(tag="integer", value="1"),
                                                CaptureValue(tag="integer", value="2"),
                                                CaptureValue(tag="integer", value="3"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "val",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="1"),
                                                CaptureValue(tag="integer", value="2"),
                                                CaptureValue(tag="integer", value="2"),
                                                CaptureValue(tag="integer", value="3"),
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
                            CaptureValue(tag="text", value="is_duplicated then not, relation sorted by idx"),
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
                                CaptureValue(tag="bool", value="true"),
                                CaptureValue(tag="bool", value="false"),
                                CaptureValue(tag="bool", value="false"),
                                CaptureValue(tag="bool", value="true"),
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
                        CaptureValue(tag="text", value="historical WindowFunction translation failure"),
                    ),
                ),
            ),
            impact="window operations raise on ibis-polars",
            since="2026-08-06",
            workaround="Use ibis-duckdb/ibis-sqlite or a polars/narwhals backend",
            issue="IB-WIN-01",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_COMPARISON.IS_DUPLICATED),
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
                                        "idx",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="0"),
                                                CaptureValue(tag="integer", value="1"),
                                                CaptureValue(tag="integer", value="2"),
                                                CaptureValue(tag="integer", value="3"),
                                                CaptureValue(tag="integer", value="4"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "val",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="1"),
                                                CaptureValue(tag="integer", value="2"),
                                                CaptureValue(tag="integer", value="2"),
                                                CaptureValue(tag="integer", value="3"),
                                                CaptureValue(tag="integer", value="1"),
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
                            CaptureValue(tag="text", value="relation sorted by idx"),
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
                                CaptureValue(tag="bool", value="true"),
                                CaptureValue(tag="bool", value="true"),
                                CaptureValue(tag="bool", value="true"),
                                CaptureValue(tag="bool", value="false"),
                                CaptureValue(tag="bool", value="true"),
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
                        CaptureValue(tag="text", value="window operations raise on ibis-polars"),
                    ),
                ),
            ),
            impact="window operations raise on ibis-polars",
            since="2026-08-06",
            workaround="Use ibis-duckdb/ibis-sqlite or a polars/narwhals backend",
            issue="IB-WIN-01",
        ),
    ),
    changes=(),
)
