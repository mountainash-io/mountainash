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
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_FINITE),
                scenario=Scenario(
                    arguments=(
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "column",
                                        CaptureValue(tag="text", value="val"),
                                    ),
                                    (
                                        "expression",
                                        CaptureValue(tag="text", value="field"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(
                        (
                            "frame",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "val",
                                        CaptureValue(
                                            tag="mapping",
                                            value=(
                                                (
                                                    "logical_type",
                                                    CaptureValue(tag="text", value="float"),
                                                ),
                                                (
                                                    "nullable",
                                                    CaptureValue(tag="bool", value="false"),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    input_data=(
                        (
                            "frame",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "val",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="float", value="0x1.0000000000000p+0"),
                                                CaptureValue(tag="float", value="+inf"),
                                                CaptureValue(tag="float", value="0x1.8000000000000p+1"),
                                                CaptureValue(tag="float", value="-inf"),
                                                CaptureValue(tag="float", value="0x1.4000000000000p+2"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="compile-and-filter"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "count",
                        CaptureValue(tag="integer", value="3"),
                    ),
                    (
                        "historical",
                        CaptureValue(tag="bool", value="true"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "exception",
                        CaptureValue(tag="text", value="OperationNotDefinedError"),
                    ),
                    (
                        "historical",
                        CaptureValue(tag="bool", value="true"),
                    ),
                ),
            ),
            impact="ma.col(x).is_finite()/is_infinite() raise on ibis-sqlite; polars, pandas, narwhals, and ibis-polars/ibis-duckdb evaluate them",
            since="2026-08-06",
            workaround="Use is_null/fill checks or a non-sqlite backend for infinity detection",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_INFINITE),
                scenario=Scenario(
                    arguments=(
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "column",
                                        CaptureValue(tag="text", value="val"),
                                    ),
                                    (
                                        "expression",
                                        CaptureValue(tag="text", value="field"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(
                        (
                            "frame",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "val",
                                        CaptureValue(
                                            tag="mapping",
                                            value=(
                                                (
                                                    "logical_type",
                                                    CaptureValue(tag="text", value="float"),
                                                ),
                                                (
                                                    "nullable",
                                                    CaptureValue(tag="bool", value="false"),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    input_data=(
                        (
                            "frame",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "val",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="float", value="0x1.0000000000000p+0"),
                                                CaptureValue(tag="float", value="+inf"),
                                                CaptureValue(tag="float", value="0x1.8000000000000p+1"),
                                                CaptureValue(tag="float", value="-inf"),
                                                CaptureValue(tag="float", value="0x1.4000000000000p+2"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="compile-and-filter"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "count",
                        CaptureValue(tag="integer", value="2"),
                    ),
                    (
                        "historical",
                        CaptureValue(tag="bool", value="true"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "exception",
                        CaptureValue(tag="text", value="OperationNotDefinedError"),
                    ),
                    (
                        "historical",
                        CaptureValue(tag="bool", value="true"),
                    ),
                ),
            ),
            impact="ma.col(x).is_finite()/is_infinite() raise on ibis-sqlite; polars, pandas, narwhals, and ibis-polars/ibis-duckdb evaluate them",
            since="2026-08-06",
            workaround="Use is_null/fill checks or a non-sqlite backend for infinity detection",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_NAN),
                scenario=Scenario(
                    arguments=(
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="val"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "val",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="float", value="0x1.0000000000000p+0"),
                                                CaptureValue(tag="float", value="nan"),
                                                CaptureValue(tag="float", value="0x1.8000000000000p+1"),
                                                CaptureValue(tag="float", value="nan"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "mode",
                            CaptureValue(tag="text", value="filter_get_result_count"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.SEMANTICS,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="mapping",
                            value=(
                                (
                                    "count",
                                    CaptureValue(tag="integer", value="2"),
                                ),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text", value="SQL engines treat NaN as NULL; NaN == NaN yields NULL rather than False."
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="is_nan/fill_nan/NaN comparisons diverge on SQL engines.",
            since="2026-07-05",
            workaround="Use is_null/fill_null on SQL backends",
            issue="IB-TYPE-02",
        ),
    ),
    changes=(),
)
