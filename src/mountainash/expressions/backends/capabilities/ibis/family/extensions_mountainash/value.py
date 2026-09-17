"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

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
                    execution=(
                        (
                            "shape",
                            CaptureValue(tag="text", value="collect expression"),
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
                                CaptureValue(tag="float", value="-0x1.0000000000000p+1"),
                                CaptureValue(tag="float", value="-0x1.8000000000000p+1"),
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
                        CaptureValue(tag="text", value="historical NaN outcome"),
                    ),
                ),
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
                    execution=(
                        (
                            "shape",
                            CaptureValue(tag="text", value="add literal 0 then over dept"),
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
                        CaptureValue(tag="text", value="length 4"),
                    ),
                ),
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
    ),
    changes=(),
)
