"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_WINDOW

from mountainash.core.capabilities.declarations import CapabilitySegment
from mountainash.core.capabilities.declarations import DivergenceManifestation
from mountainash.core.capabilities.declarations import Domain
from mountainash.core.capabilities.declarations import ManifestationKey
from mountainash.core.capabilities.schema import CallableRef
from mountainash.core.capabilities.schema import CaptureValue
from mountainash.core.capabilities.schema import CompositionTarget
from mountainash.core.capabilities.schema import DivergenceKind
from mountainash.core.capabilities.schema import Scenario
from mountainash.core.capabilities.schema import TargetSurface
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_NULL
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_TERNARY
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

SEGMENT = CapabilitySegment(
    domain=Domain.VALUE,
    capabilities=(),
    manifestations=(
        DivergenceManifestation(
            key=ManifestationKey(
                target=CompositionTarget(
                    surface=TargetSurface.EXPRESSION,
                    entrypoint=CallableRef(
                        module="mountainash.expressions.core.expression_api.entrypoints", qualname="col"
                    ),
                    operations=(FKEY_MOUNTAINASH_SCALAR_TERNARY.T_GT, FKEY_MOUNTAINASH_NULL.FILL_NULL),
                ),
                scenario=Scenario(
                    arguments=(),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "score",
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
                                        "threshold",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="70"),
                                                CaptureValue(tag="integer", value="50"),
                                                CaptureValue(tag="null", value=""),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        ("mode", CaptureValue(tag="text", value="select_and_extract")),
                        ("stage", CaptureValue(tag="text", value="compilation")),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="integer", value="1"),
                                CaptureValue(tag="integer", value="0"),
                                CaptureValue(tag="integer", value="1"),
                            ),
                        ),
                    ),
                    ("status", CaptureValue(tag="text", value="historical-source-assertion")),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text", value="t_gt with fill_null and booleanizer=None fails on the marked provider."
                        ),
                    ),
                    ("status", CaptureValue(tag="text", value="historical-declaration")),
                ),
            ),
            impact="The null-safe ternary composition raises on the marked provider.",
            since="2026-08-06",
            workaround="Pass an explicit booleanizer, or use narwhals-polars/ibis backends",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=CompositionTarget(
                    surface=TargetSurface.EXPRESSION,
                    entrypoint=CallableRef(
                        module="mountainash.expressions.core.expression_protocols.api_builders.extensions_mountainash.prtcl_api_bldr_ext_ma_scalar_arithmetic",
                        qualname="MountainAshScalarArithmeticAPIBuilderProtocol.cbrt",
                    ),
                    operations=(FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.POWER,),
                ),
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
                                                CaptureValue(tag="float", value="-0x1.0000000000000p+3"),
                                                CaptureValue(tag="float", value="-0x1.b000000000000p+4"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(("shape", CaptureValue(tag="text", value="collect expression")),),
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
                                CaptureValue(tag="float", value="-0x1.0000000000000p+1"),
                                CaptureValue(tag="float", value="-0x1.8000000000000p+1"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(("historical_source_claim", CaptureValue(tag="text", value="historical NaN outcome")),),
            ),
            impact="ma.col(x).cbrt() on negative inputs yields NaN across all backends",
            since="2026-08-06",
            workaround="Compute sign(x) * abs(x) ** (1/3) manually for negative inputs",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=CompositionTarget(
                    surface=TargetSurface.EXPRESSION,
                    entrypoint=CallableRef(
                        module="mountainash.expressions.core.expression_protocols.api_builders.extensions_mountainash.prtcl_api_bldr_ext_ma_scalar_arithmetic",
                        qualname="MountainAshScalarArithmeticAPIBuilderProtocol.cot",
                    ),
                    operations=(FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE, FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TAN),
                ),
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
                                                CaptureValue(tag="text", value="pi/4"),
                                                CaptureValue(tag="text", value="pi/2"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(("shape", CaptureValue(tag="text", value="collect expression")),),
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
                                CaptureValue(tag="float", value="0x1.0000000000000p+0"),
                                CaptureValue(tag="float", value="0x0.0p+0"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(("historical_source_claim", CaptureValue(tag="text", value="historical NotImplementedError")),),
            ),
            impact="ma.col(x).cot() raises on pandas and all narwhals backends",
            since="2026-08-06",
            workaround="Use a polars or ibis backend for cot()",
            issue="NW-MATH-01",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=CompositionTarget(
                    surface=TargetSurface.EXPRESSION,
                    entrypoint=CallableRef(
                        module="mountainash.expressions.core.expression_api.api_base", qualname="BaseExpressionAPI.over"
                    ),
                    operations=(FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ADD,),
                ),
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
                                        "dept",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="eng"),
                                                CaptureValue(tag="text", value="eng"),
                                                CaptureValue(tag="text", value="sales"),
                                                CaptureValue(tag="text", value="sales"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "salary",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="100"),
                                                CaptureValue(tag="integer", value="120"),
                                                CaptureValue(tag="integer", value="80"),
                                                CaptureValue(tag="integer", value="110"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(("shape", CaptureValue(tag="text", value="add literal 0 then over dept")),),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping", value=(("historical_source_claim", CaptureValue(tag="text", value="length 4")),)
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="scalar_expr.over(...) raises off Polars"),
                    ),
                ),
            ),
            impact="scalar_expr.over(...) raises off Polars",
            since="2026-08-06",
            workaround="Use Polars, or wrap a genuine window function",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=CompositionTarget(
                    surface=TargetSurface.EXPRESSION,
                    entrypoint=CallableRef(
                        "mountainash.expressions.core.expression_api.api_builders.substrait.api_bldr_window_arithmetic",
                        "SubstraitWindowArithmeticAPIBuilder.diff",
                    ),
                    operations=(FKEY_MOUNTAINASH_WINDOW.DIFF,),
                ),
                scenario=Scenario(
                    arguments=(("n", CaptureValue(tag="integer", value="2")),),
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
                                                CaptureValue(tag="integer", value="10"),
                                                CaptureValue(tag="integer", value="20"),
                                                CaptureValue(tag="integer", value="30"),
                                                CaptureValue(tag="integer", value="40"),
                                                CaptureValue(tag="integer", value="50"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(("shape", CaptureValue(tag="text", value="n=2")),),
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
                                CaptureValue(tag="null", value=""),
                                CaptureValue(tag="null", value=""),
                                CaptureValue(tag="integer", value="20"),
                                CaptureValue(tag="integer", value="20"),
                                CaptureValue(tag="integer", value="20"),
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
                        CaptureValue(
                            tag="text", value="percent_rank/cume_dist/nth_value and diff(n>1) raise on pandas/narwhals"
                        ),
                    ),
                ),
            ),
            impact="percent_rank/cume_dist/nth_value and diff(n>1) raise on pandas/narwhals",
            since="2026-08-06",
            workaround="Use Polars or Ibis SQL",
            issue="NW-WIN-04",
        ),
    ),
    changes=(),
)
