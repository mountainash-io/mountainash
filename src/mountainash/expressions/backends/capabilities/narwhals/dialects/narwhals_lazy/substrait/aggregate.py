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
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.ANY_VALUE),
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
                    execution=(
                        (
                            "shape",
                            CaptureValue(tag="text", value="terminal aggregate"),
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
                        CaptureValue(tag="text", value="member of input"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="mode() and any_value() raise on narwhals-lazy"),
                    ),
                ),
            ),
            impact="mode() and any_value() raise on narwhals-lazy",
            since="2026-08-06",
            workaround="Use an eager backend",
            issue="NW-AGG-03",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.ANY_VALUE),
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
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="integer", value="20"),
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="integer", value="40"),
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
                            CaptureValue(tag="text", value="terminal aggregate"),
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
                        CaptureValue(tag="text", value="None, 20, or 40"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="historical InvalidOperationError"),
                    ),
                ),
            ),
            impact="mode() and any_value() raise on narwhals-lazy",
            since="2026-08-06",
            workaround="Use an eager backend",
            issue="NW-AGG-03",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.ANY_VALUE),
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
                                                CaptureValue(tag="null", value=""),
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
                            CaptureValue(tag="text", value="terminal all-null aggregate"),
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
                        CaptureValue(tag="null", value=""),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="historical InvalidOperationError"),
                    ),
                ),
            ),
            impact="mode() and any_value() raise on narwhals-lazy",
            since="2026-08-06",
            workaround="Use an eager backend",
            issue="NW-AGG-03",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.ANY_VALUE),
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
                                                CaptureValue(tag="text", value="alpha"),
                                                CaptureValue(tag="text", value="beta"),
                                                CaptureValue(tag="text", value="gamma"),
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
                            CaptureValue(tag="text", value="terminal aggregate"),
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
                        CaptureValue(tag="text", value="member of input"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="historical InvalidOperationError"),
                    ),
                ),
            ),
            impact="mode() and any_value() raise on narwhals-lazy",
            since="2026-08-06",
            workaround="Use an eager backend",
            issue="NW-AGG-03",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.ANY_VALUE),
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
                                                CaptureValue(tag="text", value="b"),
                                                CaptureValue(tag="text", value="b"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "x",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="1"),
                                                CaptureValue(tag="integer", value="2"),
                                                CaptureValue(tag="integer", value="3"),
                                                CaptureValue(tag="integer", value="4"),
                                                CaptureValue(tag="integer", value="6"),
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
                            CaptureValue(tag="text", value="group by g; any_value x alias v; sort g; to_dict"),
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
                        CaptureValue(tag="text", value="first group member in [1,2,3]; second in [4,6]"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="historical InvalidOperationError"),
                    ),
                ),
            ),
            impact="mode() and any_value() raise on narwhals-lazy",
            since="2026-08-06",
            workaround="Use an eager backend",
            issue="NW-AGG-03",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.ANY_VALUE),
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
                                        "x",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="1"),
                                                CaptureValue(tag="integer", value="2"),
                                                CaptureValue(tag="integer", value="3"),
                                                CaptureValue(tag="integer", value="4"),
                                                CaptureValue(tag="integer", value="6"),
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
                            CaptureValue(tag="text", value="relation.any_value x scalar terminal"),
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
                        CaptureValue(tag="text", value="member of [1,2,3,4,6]"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="historical InvalidOperationError"),
                    ),
                ),
            ),
            impact="mode() and any_value() raise on narwhals-lazy",
            since="2026-08-06",
            workaround="Use an eager backend",
            issue="NW-AGG-03",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.MODE),
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
                                                CaptureValue(tag="integer", value="1"),
                                                CaptureValue(tag="integer", value="2"),
                                                CaptureValue(tag="integer", value="2"),
                                                CaptureValue(tag="integer", value="3"),
                                                CaptureValue(tag="integer", value="3"),
                                                CaptureValue(tag="integer", value="3"),
                                                CaptureValue(tag="integer", value="4"),
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
                            CaptureValue(tag="text", value="terminal aggregate"),
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
                        CaptureValue(tag="text", value="3 or list containing 3"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="mode() and any_value() raise on narwhals-lazy"),
                    ),
                ),
            ),
            impact="mode() and any_value() raise on narwhals-lazy",
            since="2026-08-06",
            workaround="Use an eager backend",
            issue="NW-AGG-03",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.MODE),
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
                                                CaptureValue(tag="integer", value="7"),
                                                CaptureValue(tag="integer", value="7"),
                                                CaptureValue(tag="integer", value="7"),
                                                CaptureValue(tag="integer", value="7"),
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
                            CaptureValue(tag="text", value="terminal aggregate"),
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
                        CaptureValue(tag="text", value="7 or list containing 7"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="historical InvalidOperationError"),
                    ),
                ),
            ),
            impact="mode() and any_value() raise on narwhals-lazy",
            since="2026-08-06",
            workaround="Use an eager backend",
            issue="NW-AGG-03",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.MODE),
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
                                                CaptureValue(tag="text", value="x"),
                                                CaptureValue(tag="text", value="y"),
                                                CaptureValue(tag="text", value="y"),
                                                CaptureValue(tag="text", value="z"),
                                                CaptureValue(tag="text", value="y"),
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
                            CaptureValue(tag="text", value="terminal aggregate"),
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
                        CaptureValue(tag="text", value="y or list containing y"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="historical InvalidOperationError"),
                    ),
                ),
            ),
            impact="mode() and any_value() raise on narwhals-lazy",
            since="2026-08-06",
            workaround="Use an eager backend",
            issue="NW-AGG-03",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.MODE),
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
                                                CaptureValue(tag="text", value="b"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "x",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="1"),
                                                CaptureValue(tag="integer", value="1"),
                                                CaptureValue(tag="integer", value="2"),
                                                CaptureValue(tag="integer", value="5"),
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
                            CaptureValue(tag="text", value="group by g; mode x alias v; sort g; to_dict"),
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
                        CaptureValue(tag="text", value="1 and 5, scalar or list"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="historical InvalidOperationError"),
                    ),
                ),
            ),
            impact="mode() and any_value() raise on narwhals-lazy",
            since="2026-08-06",
            workaround="Use an eager backend",
            issue="NW-AGG-03",
        ),
    ),
    changes=(),
)
