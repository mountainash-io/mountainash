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
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_AGGREGATE

SEGMENT = CapabilitySegment(
    domain=Domain.AGGREGATE,
    capabilities=(),
    manifestations=(
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.CORR),
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
                                        "g",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="a"),
                                                CaptureValue(tag="text", value="a"),
                                                CaptureValue(tag="text", value="a"),
                                                CaptureValue(tag="text", value="a"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "x",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="float", value="0x1.0000000000000p+0"),
                                                CaptureValue(tag="float", value="0x1.0000000000000p+1"),
                                                CaptureValue(tag="float", value="0x1.8000000000000p+1"),
                                                CaptureValue(tag="float", value="0x1.0000000000000p+2"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "y",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="float", value="0x1.0000000000000p+1"),
                                                CaptureValue(tag="float", value="0x1.0000000000000p+2"),
                                                CaptureValue(tag="float", value="0x1.8000000000000p+2"),
                                                CaptureValue(tag="float", value="0x1.0000000000000p+3"),
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
                            CaptureValue(tag="text", value="grouped corr alias c"),
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
                        CaptureValue(tag="float", value="0x1.0000000000000p+0"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="ma.corr() raises on all backends except ibis-polars"),
                    ),
                ),
            ),
            impact="ma.corr() raises on all backends except ibis-polars",
            since="2026-08-06",
            workaround="Use ibis-polars or compute correlation manually",
            issue=None,
        ),
    ),
    changes=(),
)
