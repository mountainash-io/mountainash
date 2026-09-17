"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_WINDOW
from mountainash.core.capabilities.schema import CompositionTarget
from mountainash.expressions.core.expression_system.function_keys.enums import SUBSTRAIT_ARITHMETIC_WINDOW
from mountainash.core.capabilities.schema import TargetSurface

from mountainash.core.capabilities.declarations import CapabilitySegment
from mountainash.core.capabilities.declarations import DivergenceManifestation
from mountainash.core.capabilities.declarations import Domain
from mountainash.core.capabilities.declarations import ManifestationKey
from mountainash.core.capabilities.schema import CallableRef
from mountainash.core.capabilities.schema import CaptureValue
from mountainash.core.capabilities.schema import DivergenceKind
from mountainash.core.capabilities.schema import ProtocolMethodTarget
from mountainash.core.capabilities.schema import Scenario

SEGMENT = CapabilitySegment(
    domain=Domain.VALUE,
    capabilities=(),
    manifestations=(
        DivergenceManifestation(
            key=ManifestationKey(
                target=ProtocolMethodTarget(
                    protocol=CallableRef(
                        module="mountainash.expressions.core.expression_protocols.api_builders.substrait.prtcl_api_bldr_window_arithmetic",
                        qualname="SubstraitWindowArithmeticAPIBuilderProtocol",
                    ),
                    method="shift",
                ),
                scenario=Scenario(
                    arguments=(("n", CaptureValue(tag="integer", value="-1")),),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "values",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "group",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="A"),
                                                CaptureValue(tag="text", value="A"),
                                                CaptureValue(tag="text", value="A"),
                                                CaptureValue(tag="text", value="A"),
                                                CaptureValue(tag="text", value="A"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "score",
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
                    execution=(("shape", CaptureValue(tag="text", value="shift n=-1 over group")),),
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
                                CaptureValue(tag="integer", value="20"),
                                CaptureValue(tag="integer", value="30"),
                                CaptureValue(tag="integer", value="40"),
                                CaptureValue(tag="integer", value="50"),
                                CaptureValue(tag="null", value=""),
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
                        CaptureValue(tag="text", value="historical WindowFunction/order-dependent failure"),
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
                target=ProtocolMethodTarget(
                    protocol=CallableRef(
                        module="mountainash.expressions.core.expression_protocols.api_builders.substrait.prtcl_api_bldr_window_arithmetic",
                        qualname="SubstraitWindowArithmeticAPIBuilderProtocol",
                    ),
                    method="shift",
                ),
                scenario=Scenario(
                    arguments=(("n", CaptureValue(tag="integer", value="1")),),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "values",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "group",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="A"),
                                                CaptureValue(tag="text", value="A"),
                                                CaptureValue(tag="text", value="A"),
                                                CaptureValue(tag="text", value="A"),
                                                CaptureValue(tag="text", value="A"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "score",
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
                    execution=(("shape", CaptureValue(tag="text", value="shift n=1 over group")),),
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
                                CaptureValue(tag="integer", value="10"),
                                CaptureValue(tag="integer", value="20"),
                                CaptureValue(tag="integer", value="30"),
                                CaptureValue(tag="integer", value="40"),
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
                        CaptureValue(tag="text", value="historical WindowFunction/order-dependent failure"),
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
                target=ProtocolMethodTarget(
                    protocol=CallableRef(
                        module="mountainash.expressions.core.expression_protocols.api_builders.substrait.prtcl_api_bldr_window_arithmetic",
                        qualname="SubstraitWindowArithmeticAPIBuilderProtocol",
                    ),
                    method="shift",
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
                                        "group",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="A"),
                                                CaptureValue(tag="text", value="A"),
                                                CaptureValue(tag="text", value="A"),
                                                CaptureValue(tag="text", value="A"),
                                                CaptureValue(tag="text", value="A"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "score",
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
                    execution=(("shape", CaptureValue(tag="text", value="shift n=2 over group")),),
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
                                CaptureValue(tag="integer", value="10"),
                                CaptureValue(tag="integer", value="20"),
                                CaptureValue(tag="integer", value="30"),
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
                        CaptureValue(tag="text", value="historical WindowFunction/order-dependent failure"),
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
                target=CompositionTarget(
                    surface=TargetSurface.EXPRESSION,
                    entrypoint=CallableRef(
                        "mountainash.expressions.core.expression_api.api_builders.substrait.api_bldr_window_arithmetic",
                        "SubstraitWindowArithmeticAPIBuilder.lag",
                    ),
                    operations=(SUBSTRAIT_ARITHMETIC_WINDOW.LAG,),
                ),
                scenario=Scenario(
                    arguments=(("offset", CaptureValue(tag="integer", value="2")),),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "values",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "group",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="A"),
                                                CaptureValue(tag="text", value="A"),
                                                CaptureValue(tag="text", value="A"),
                                                CaptureValue(tag="text", value="A"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "score",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="10"),
                                                CaptureValue(tag="integer", value="20"),
                                                CaptureValue(tag="integer", value="30"),
                                                CaptureValue(tag="integer", value="40"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(("shape", CaptureValue(tag="text", value="lag n=2 over group")),),
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
                                CaptureValue(tag="integer", value="10"),
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
                        CaptureValue(tag="text", value="historical WindowFunction/order-dependent failure"),
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
                target=CompositionTarget(
                    surface=TargetSurface.EXPRESSION,
                    entrypoint=CallableRef(
                        "mountainash.expressions.core.expression_api.api_builders.substrait.api_bldr_window_arithmetic",
                        "SubstraitWindowArithmeticAPIBuilder.lead",
                    ),
                    operations=(SUBSTRAIT_ARITHMETIC_WINDOW.LEAD,),
                ),
                scenario=Scenario(
                    arguments=(("offset", CaptureValue(tag="integer", value="2")),),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "values",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "group",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="A"),
                                                CaptureValue(tag="text", value="A"),
                                                CaptureValue(tag="text", value="A"),
                                                CaptureValue(tag="text", value="A"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "score",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="10"),
                                                CaptureValue(tag="integer", value="20"),
                                                CaptureValue(tag="integer", value="30"),
                                                CaptureValue(tag="integer", value="40"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(("shape", CaptureValue(tag="text", value="lead n=2 over group")),),
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
                                CaptureValue(tag="integer", value="30"),
                                CaptureValue(tag="integer", value="40"),
                                CaptureValue(tag="null", value=""),
                                CaptureValue(tag="null", value=""),
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
                        CaptureValue(tag="text", value="historical WindowFunction/order-dependent failure"),
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
                    execution=(("shape", CaptureValue(tag="text", value="diff n=2")),),
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
                target=CompositionTarget(
                    surface=TargetSurface.EXPRESSION,
                    entrypoint=CallableRef(
                        "mountainash.expressions.core.expression_api.api_builders.substrait.api_bldr_window_arithmetic",
                        "SubstraitWindowArithmeticAPIBuilder.lag",
                    ),
                    operations=(SUBSTRAIT_ARITHMETIC_WINDOW.LAG,),
                ),
                scenario=Scenario(
                    arguments=(("offset", CaptureValue(tag="integer", value="1")),),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "values",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "group",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="A"),
                                                CaptureValue(tag="text", value="A"),
                                                CaptureValue(tag="text", value="A"),
                                                CaptureValue(tag="text", value="B"),
                                                CaptureValue(tag="text", value="B"),
                                                CaptureValue(tag="text", value="B"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "score",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="10"),
                                                CaptureValue(tag="integer", value="20"),
                                                CaptureValue(tag="integer", value="30"),
                                                CaptureValue(tag="integer", value="15"),
                                                CaptureValue(tag="integer", value="25"),
                                                CaptureValue(tag="integer", value="35"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(("shape", CaptureValue(tag="text", value="lag n=1 over group sorted by group, score")),),
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
                                CaptureValue(tag="integer", value="10"),
                                CaptureValue(tag="integer", value="20"),
                                CaptureValue(tag="null", value=""),
                                CaptureValue(tag="integer", value="15"),
                                CaptureValue(tag="integer", value="25"),
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
                        CaptureValue(tag="text", value="historical WindowFunction/order-dependent failure"),
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
                target=CompositionTarget(
                    surface=TargetSurface.EXPRESSION,
                    entrypoint=CallableRef(
                        "mountainash.expressions.core.expression_api.api_builders.substrait.api_bldr_window_arithmetic",
                        "SubstraitWindowArithmeticAPIBuilder.lead",
                    ),
                    operations=(SUBSTRAIT_ARITHMETIC_WINDOW.LEAD,),
                ),
                scenario=Scenario(
                    arguments=(("offset", CaptureValue(tag="integer", value="1")),),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "values",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "group",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="A"),
                                                CaptureValue(tag="text", value="A"),
                                                CaptureValue(tag="text", value="A"),
                                                CaptureValue(tag="text", value="B"),
                                                CaptureValue(tag="text", value="B"),
                                                CaptureValue(tag="text", value="B"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "score",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="10"),
                                                CaptureValue(tag="integer", value="20"),
                                                CaptureValue(tag="integer", value="30"),
                                                CaptureValue(tag="integer", value="15"),
                                                CaptureValue(tag="integer", value="25"),
                                                CaptureValue(tag="integer", value="35"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        ("shape", CaptureValue(tag="text", value="lead n=1 over group sorted by group, score")),
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
                                CaptureValue(tag="integer", value="20"),
                                CaptureValue(tag="integer", value="30"),
                                CaptureValue(tag="null", value=""),
                                CaptureValue(tag="integer", value="25"),
                                CaptureValue(tag="integer", value="35"),
                                CaptureValue(tag="null", value=""),
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
                        CaptureValue(tag="text", value="historical WindowFunction/order-dependent failure"),
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
