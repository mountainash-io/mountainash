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
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_BOOLEAN

SEGMENT = CapabilitySegment(
    domain=Domain.BOOLEAN,
    capabilities=(),
    manifestations=(
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_BOOLEAN.XOR_PARITY),
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
                                        "a",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="80"),
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="integer", value="60"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "b",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="bool", value="true"),
                                                CaptureValue(tag="bool", value="true"),
                                                CaptureValue(tag="bool", value="true"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "c",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="bool", value="true"),
                                                CaptureValue(tag="bool", value="false"),
                                                CaptureValue(tag="bool", value="true"),
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
                            CaptureValue(tag="text", value="compile then select"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.SEMANTICS,
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
                        CaptureValue(tag="text", value="historical DuckDB integer-bitwise XOR"),
                    ),
                ),
            ),
            impact="Chained boolean parity via xor diverges on ibis-duckdb",
            since="2026-07-05",
            workaround="Use polars, narwhals, or ibis-sqlite for boolean parity",
            issue="IB-DT-06",
        ),
    ),
    changes=(),
)
