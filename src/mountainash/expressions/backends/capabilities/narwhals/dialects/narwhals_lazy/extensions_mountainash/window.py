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
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_WINDOW

SEGMENT = CapabilitySegment(
    domain=Domain.WINDOW,
    capabilities=(),
    manifestations=(
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_WINDOW.CUM_COUNT),
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
                    execution=(("shape", CaptureValue(tag="text", value="relation materialization")),),
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
                                CaptureValue(tag="integer", value="2"),
                                CaptureValue(tag="integer", value="3"),
                                CaptureValue(tag="integer", value="4"),
                                CaptureValue(tag="integer", value="5"),
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
                        CaptureValue(tag="text", value="order-dependent window operations raise on narwhals-lazy"),
                    ),
                ),
            ),
            impact="order-dependent window operations raise on narwhals-lazy",
            since="2026-08-06",
            workaround="Use an eager backend, or establish an explicit order",
            issue="NW-WIN-03",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_WINDOW.CUM_COUNT),
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
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="integer", value="30"),
                                                CaptureValue(tag="null", value=""),
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
                            CaptureValue(tag="text", value="cum_count non-null values"),
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
                                CaptureValue(tag="integer", value="2"),
                                CaptureValue(tag="integer", value="2"),
                                CaptureValue(tag="integer", value="3"),
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
            impact="order-dependent window operations raise on narwhals-lazy",
            since="2026-08-06",
            workaround="Use an eager backend, or establish an explicit order",
            issue="NW-WIN-03",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_WINDOW.CUM_MAX),
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
                                                CaptureValue(tag="integer", value="3"),
                                                CaptureValue(tag="integer", value="1"),
                                                CaptureValue(tag="integer", value="4"),
                                                CaptureValue(tag="integer", value="1"),
                                                CaptureValue(tag="integer", value="5"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(("shape", CaptureValue(tag="text", value="relation materialization")),),
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
                                CaptureValue(tag="integer", value="3"),
                                CaptureValue(tag="integer", value="3"),
                                CaptureValue(tag="integer", value="4"),
                                CaptureValue(tag="integer", value="4"),
                                CaptureValue(tag="integer", value="5"),
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
                        CaptureValue(tag="text", value="order-dependent window operations raise on narwhals-lazy"),
                    ),
                ),
            ),
            impact="order-dependent window operations raise on narwhals-lazy",
            since="2026-08-06",
            workaround="Use an eager backend, or establish an explicit order",
            issue="NW-WIN-03",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_WINDOW.CUM_MAX),
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
                                        "sales",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="10"),
                                                CaptureValue(tag="integer", value="20"),
                                                CaptureValue(tag="integer", value="30"),
                                                CaptureValue(tag="integer", value="100"),
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
                                CaptureValue(tag="integer", value="10"),
                                CaptureValue(tag="integer", value="20"),
                                CaptureValue(tag="integer", value="30"),
                                CaptureValue(tag="integer", value="100"),
                                CaptureValue(tag="integer", value="100"),
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
            impact="order-dependent window operations raise on narwhals-lazy",
            since="2026-08-06",
            workaround="Use an eager backend, or establish an explicit order",
            issue="NW-WIN-03",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_WINDOW.CUM_MIN),
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
                                                CaptureValue(tag="integer", value="5"),
                                                CaptureValue(tag="integer", value="3"),
                                                CaptureValue(tag="integer", value="4"),
                                                CaptureValue(tag="integer", value="1"),
                                                CaptureValue(tag="integer", value="2"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(("shape", CaptureValue(tag="text", value="relation materialization")),),
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
                                CaptureValue(tag="integer", value="5"),
                                CaptureValue(tag="integer", value="3"),
                                CaptureValue(tag="integer", value="3"),
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
                        CaptureValue(tag="text", value="order-dependent window operations raise on narwhals-lazy"),
                    ),
                ),
            ),
            impact="order-dependent window operations raise on narwhals-lazy",
            since="2026-08-06",
            workaround="Use an eager backend, or establish an explicit order",
            issue="NW-WIN-03",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_WINDOW.CUM_MIN),
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
                                        "sales",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="10"),
                                                CaptureValue(tag="integer", value="20"),
                                                CaptureValue(tag="integer", value="30"),
                                                CaptureValue(tag="integer", value="100"),
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
                                CaptureValue(tag="integer", value="10"),
                                CaptureValue(tag="integer", value="10"),
                                CaptureValue(tag="integer", value="10"),
                                CaptureValue(tag="integer", value="10"),
                                CaptureValue(tag="integer", value="10"),
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
            impact="order-dependent window operations raise on narwhals-lazy",
            since="2026-08-06",
            workaround="Use an eager backend, or establish an explicit order",
            issue="NW-WIN-03",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_WINDOW.CUM_PROD),
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
                            CaptureValue(tag="text", value="relation materialization"),
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
                                CaptureValue(tag="integer", value="2"),
                                CaptureValue(tag="integer", value="6"),
                                CaptureValue(tag="integer", value="24"),
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
                        CaptureValue(tag="text", value="order-dependent window operations raise on narwhals-lazy"),
                    ),
                ),
            ),
            impact="order-dependent window operations raise on narwhals-lazy",
            since="2026-08-06",
            workaround="Use an eager backend, or establish an explicit order",
            issue="NW-WIN-03",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_WINDOW.CUM_SUM),
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
                                                CaptureValue(tag="integer", value="3"),
                                                CaptureValue(tag="integer", value="4"),
                                                CaptureValue(tag="integer", value="5"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(("shape", CaptureValue(tag="text", value="relation materialization")),),
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
                                CaptureValue(tag="integer", value="3"),
                                CaptureValue(tag="integer", value="6"),
                                CaptureValue(tag="integer", value="10"),
                                CaptureValue(tag="integer", value="15"),
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
                        CaptureValue(tag="text", value="order-dependent window operations raise on narwhals-lazy"),
                    ),
                ),
            ),
            impact="order-dependent window operations raise on narwhals-lazy",
            since="2026-08-06",
            workaround="Use an eager backend, or establish an explicit order",
            issue="NW-WIN-03",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_WINDOW.CUM_SUM),
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
                                        "group",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="A"),
                                                CaptureValue(tag="text", value="A"),
                                                CaptureValue(tag="text", value="A"),
                                                CaptureValue(tag="text", value="B"),
                                                CaptureValue(tag="text", value="B"),
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
                                                CaptureValue(tag="integer", value="3"),
                                                CaptureValue(tag="integer", value="10"),
                                                CaptureValue(tag="integer", value="20"),
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
                            CaptureValue(tag="text", value="cum_sum over group, sorted group val"),
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
                                CaptureValue(tag="integer", value="3"),
                                CaptureValue(tag="integer", value="6"),
                                CaptureValue(tag="integer", value="10"),
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
            impact="order-dependent window operations raise on narwhals-lazy",
            since="2026-08-06",
            workaround="Use an eager backend, or establish an explicit order",
            issue="NW-WIN-03",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_WINDOW.CUM_SUM),
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
                                        "sales",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="10"),
                                                CaptureValue(tag="integer", value="20"),
                                                CaptureValue(tag="integer", value="30"),
                                                CaptureValue(tag="integer", value="100"),
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
                                CaptureValue(tag="integer", value="10"),
                                CaptureValue(tag="integer", value="30"),
                                CaptureValue(tag="integer", value="60"),
                                CaptureValue(tag="integer", value="160"),
                                CaptureValue(tag="integer", value="210"),
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
            impact="order-dependent window operations raise on narwhals-lazy",
            since="2026-08-06",
            workaround="Use an eager backend, or establish an explicit order",
            issue="NW-WIN-03",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_WINDOW.CUM_SUM),
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
                                        "sales",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="10"),
                                                CaptureValue(tag="integer", value="20"),
                                                CaptureValue(tag="integer", value="30"),
                                                CaptureValue(tag="integer", value="100"),
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
                            CaptureValue(tag="text", value="collect expression reverse=True"),
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
                                CaptureValue(tag="integer", value="210"),
                                CaptureValue(tag="integer", value="200"),
                                CaptureValue(tag="integer", value="180"),
                                CaptureValue(tag="integer", value="150"),
                                CaptureValue(tag="integer", value="50"),
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
            impact="order-dependent window operations raise on narwhals-lazy",
            since="2026-08-06",
            workaround="Use an eager backend, or establish an explicit order",
            issue="NW-WIN-03",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_WINDOW.DIFF),
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
                                                CaptureValue(tag="integer", value="35"),
                                                CaptureValue(tag="integer", value="50"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(("shape", CaptureValue(tag="text", value="relation materialization")),),
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
                                CaptureValue(tag="integer", value="15"),
                                CaptureValue(tag="integer", value="15"),
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
                        CaptureValue(tag="text", value="order-dependent window operations raise on narwhals-lazy"),
                    ),
                ),
            ),
            impact="order-dependent window operations raise on narwhals-lazy",
            since="2026-08-06",
            workaround="Use an eager backend, or establish an explicit order",
            issue="NW-WIN-03",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_WINDOW.DIFF),
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
                                        "value",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="10"),
                                                CaptureValue(tag="integer", value="30"),
                                                CaptureValue(tag="integer", value="25"),
                                                CaptureValue(tag="integer", value="100"),
                                                CaptureValue(tag="integer", value="80"),
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
                                CaptureValue(tag="null", value=""),
                                CaptureValue(tag="integer", value="20"),
                                CaptureValue(tag="integer", value="-5"),
                                CaptureValue(tag="integer", value="75"),
                                CaptureValue(tag="integer", value="-20"),
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
            impact="order-dependent window operations raise on narwhals-lazy",
            since="2026-08-06",
            workaround="Use an eager backend, or establish an explicit order",
            issue="NW-WIN-03",
        ),
    ),
    changes=(),
)
