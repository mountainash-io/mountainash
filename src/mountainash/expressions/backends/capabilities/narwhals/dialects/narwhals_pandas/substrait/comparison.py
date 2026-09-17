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
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_COMPARISON

SEGMENT = CapabilitySegment(
    domain=Domain.COMPARISON,
    capabilities=(),
    manifestations=(
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_COMPARISON.GREATEST),
                scenario=Scenario(
                    arguments=(
                        (
                            "args",
                            CaptureValue(
                                tag="sequence",
                                value=(
                                    CaptureValue(
                                        tag="mapping",
                                        value=(
                                            (
                                                "field",
                                                CaptureValue(tag="text", value="score"),
                                            ),
                                        ),
                                    ),
                                    CaptureValue(
                                        tag="mapping",
                                        value=(
                                            (
                                                "literal",
                                                CaptureValue(tag="integer", value="90"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(
                        (
                            "score",
                            CaptureValue(tag="text", value="integer"),
                        ),
                    ),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "id",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="1"),
                                                CaptureValue(tag="integer", value="2"),
                                                CaptureValue(tag="integer", value="3"),
                                                CaptureValue(tag="integer", value="4"),
                                                CaptureValue(tag="integer", value="5"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "score",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="85"),
                                                CaptureValue(tag="integer", value="92"),
                                                CaptureValue(tag="integer", value="78"),
                                                CaptureValue(tag="integer", value="95"),
                                                CaptureValue(tag="integer", value="88"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "projection_alias",
                            CaptureValue(tag="text", value="at_least_90"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                        (
                            "terminal",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "method",
                                        CaptureValue(tag="text", value="to_dict"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.SEMANTICS,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "claim",
                        CaptureValue(tag="text", value="source_reported_expected"),
                    ),
                    (
                        "fresh_native_result",
                        CaptureValue(tag="bool", value="false"),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical_source_claim"),
                    ),
                    (
                        "value",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="text", value="result at_least_90 == [90, 92, 90, 95, 90]"),
                                CaptureValue(tag="text", value="result at_least_90 == [90, 92, 90, 95, 90]"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "claim",
                        CaptureValue(tag="text", value="source_reported_observed"),
                    ),
                    (
                        "fresh_native_result",
                        CaptureValue(tag="bool", value="false"),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical_source_claim"),
                    ),
                    (
                        "value",
                        CaptureValue(
                            tag="text",
                            value="horizontal greatest()/least() produce diverging values on pandas and narwhals-pandas (pandas element-wise max/min semantics differ from polars/ibis)",
                        ),
                    ),
                ),
            ),
            impact="Relation greatest()/least() diverge on pandas/narwhals-pandas; polars/narwhals-polars and ibis agree",
            since="2026-08-06",
            workaround="Use a polars or ibis backend for horizontal greatest/least",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_COMPARISON.LEAST),
                scenario=Scenario(
                    arguments=(
                        (
                            "args",
                            CaptureValue(
                                tag="sequence",
                                value=(
                                    CaptureValue(
                                        tag="mapping",
                                        value=(
                                            (
                                                "field",
                                                CaptureValue(tag="text", value="score"),
                                            ),
                                        ),
                                    ),
                                    CaptureValue(
                                        tag="mapping",
                                        value=(
                                            (
                                                "literal",
                                                CaptureValue(tag="integer", value="90"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(
                        (
                            "score",
                            CaptureValue(tag="text", value="integer"),
                        ),
                    ),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "id",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="1"),
                                                CaptureValue(tag="integer", value="2"),
                                                CaptureValue(tag="integer", value="3"),
                                                CaptureValue(tag="integer", value="4"),
                                                CaptureValue(tag="integer", value="5"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "score",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="85"),
                                                CaptureValue(tag="integer", value="92"),
                                                CaptureValue(tag="integer", value="78"),
                                                CaptureValue(tag="integer", value="95"),
                                                CaptureValue(tag="integer", value="88"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "projection_alias",
                            CaptureValue(tag="text", value="capped_at_90"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                        (
                            "terminal",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "method",
                                        CaptureValue(tag="text", value="to_dict"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.SEMANTICS,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "claim",
                        CaptureValue(tag="text", value="source_reported_expected"),
                    ),
                    (
                        "fresh_native_result",
                        CaptureValue(tag="bool", value="false"),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical_source_claim"),
                    ),
                    (
                        "value",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="text", value="result capped_at_90 == [85, 90, 78, 90, 88]"),
                                CaptureValue(tag="text", value="result capped_at_90 == [85, 90, 78, 90, 88]"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "claim",
                        CaptureValue(tag="text", value="source_reported_observed"),
                    ),
                    (
                        "fresh_native_result",
                        CaptureValue(tag="bool", value="false"),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical_source_claim"),
                    ),
                    (
                        "value",
                        CaptureValue(
                            tag="text",
                            value="horizontal greatest()/least() produce diverging values on pandas and narwhals-pandas (pandas element-wise max/min semantics differ from polars/ibis)",
                        ),
                    ),
                ),
            ),
            impact="Relation greatest()/least() diverge on pandas/narwhals-pandas; polars/narwhals-polars and ibis agree",
            since="2026-08-06",
            workaround="Use a polars or ibis backend for horizontal greatest/least",
            issue=None,
        ),
    ),
    changes=(),
)
