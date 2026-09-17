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
from mountainash.expressions.core.expression_system.function_keys.enums import SUBSTRAIT_ARITHMETIC_WINDOW

SEGMENT = CapabilitySegment(
    domain=Domain.WINDOW,
    capabilities=(),
    manifestations=(
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=SUBSTRAIT_ARITHMETIC_WINDOW.DENSE_RANK),
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
                                                CaptureValue(tag="text", value="A"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "id",
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
                                    (
                                        "score",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="10"),
                                                CaptureValue(tag="integer", value="20"),
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
                        ("shape", CaptureValue(tag="text", value="dense_rank over group, sort group score id")),
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
                        CaptureValue(tag="text", value="historical rank divergence/WindowFunction failure"),
                    ),
                ),
            ),
            impact="rank/dense_rank/row_number return values one lower on ibis SQL",
            since="2026-08-06",
            workaround="Add 1 on ibis SQL, or use polars/narwhals",
            issue="IB-WIN-02",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=SUBSTRAIT_ARITHMETIC_WINDOW.DENSE_RANK),
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
                                        "score",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="10"),
                                                CaptureValue(tag="integer", value="30"),
                                                CaptureValue(tag="integer", value="20"),
                                                CaptureValue(tag="integer", value="15"),
                                                CaptureValue(tag="integer", value="25"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(("shape", CaptureValue(tag="text", value="over group method=min")),),
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
                                CaptureValue(tag="integer", value="1"),
                                CaptureValue(tag="integer", value="2"),
                                CaptureValue(tag="integer", value="3"),
                                CaptureValue(tag="integer", value="1"),
                                CaptureValue(tag="integer", value="2"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(("historical_source_claim", CaptureValue(tag="text", value="historical 0-based rank")),),
            ),
            impact="rank/dense_rank/row_number return values one lower on ibis SQL",
            since="2026-08-06",
            workaround="Add 1 on ibis SQL, or use polars/narwhals",
            issue="IB-WIN-02",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=SUBSTRAIT_ARITHMETIC_WINDOW.NTILE),
                scenario=Scenario(
                    arguments=(("x", CaptureValue(tag="integer", value="3")),),
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
                                                CaptureValue(tag="integer", value="60"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(("shape", CaptureValue(tag="text", value="ntile n=3 over group")),),
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
                                CaptureValue(tag="integer", value="3"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(("historical_source_claim", CaptureValue(tag="text", value="historical unsupported ntile")),),
            ),
            impact="ntile() is unsupported off Polars",
            since="2026-08-06",
            workaround="Use a Polars backend for ntile()",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=SUBSTRAIT_ARITHMETIC_WINDOW.RANK),
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
                                                CaptureValue(tag="text", value="eng"),
                                                CaptureValue(tag="text", value="sales"),
                                                CaptureValue(tag="text", value="sales"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "level",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="jr"),
                                                CaptureValue(tag="text", value="sr"),
                                                CaptureValue(tag="text", value="jr"),
                                                CaptureValue(tag="text", value="jr"),
                                                CaptureValue(tag="text", value="sr"),
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
                                                CaptureValue(tag="integer", value="90"),
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
                            CaptureValue(tag="text", value="rank method=min over dept and level, sorted relation"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.SEMANTICS,
            expected=CaptureValue(
                tag="mapping",
                value=(("historical_source_claim", CaptureValue(tag="text", value="five ranks all >= 1")),),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="historical rank divergence/WindowFunction failure"),
                    ),
                ),
            ),
            impact="rank/dense_rank/row_number return values one lower on ibis SQL",
            since="2026-08-06",
            workaround="Add 1 on ibis SQL, or use polars/narwhals",
            issue="IB-WIN-02",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=SUBSTRAIT_ARITHMETIC_WINDOW.RANK),
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
                                        CaptureValue(tag="sequence", value=(CaptureValue(tag="text", value="A"),)),
                                    ),
                                    (
                                        "score",
                                        CaptureValue(tag="sequence", value=(CaptureValue(tag="integer", value="99"),)),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(("shape", CaptureValue(tag="text", value="rank method=min over group")),),
                ),
            ),
            kind=DivergenceKind.SEMANTICS,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="sequence", value=(CaptureValue(tag="integer", value="1"),)),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="historical rank divergence/WindowFunction failure"),
                    ),
                ),
            ),
            impact="rank/dense_rank/row_number return values one lower on ibis SQL",
            since="2026-08-06",
            workaround="Add 1 on ibis SQL, or use polars/narwhals",
            issue="IB-WIN-02",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=SUBSTRAIT_ARITHMETIC_WINDOW.RANK),
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
                                                CaptureValue(tag="text", value="A"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "id",
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
                                    (
                                        "score",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="10"),
                                                CaptureValue(tag="integer", value="20"),
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
                        ("shape", CaptureValue(tag="text", value="rank method=min over group, sort group score id")),
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
                                CaptureValue(tag="integer", value="1"),
                                CaptureValue(tag="integer", value="2"),
                                CaptureValue(tag="integer", value="2"),
                                CaptureValue(tag="integer", value="4"),
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
                        CaptureValue(tag="text", value="historical rank divergence/WindowFunction failure"),
                    ),
                ),
            ),
            impact="rank/dense_rank/row_number return values one lower on ibis SQL",
            since="2026-08-06",
            workaround="Add 1 on ibis SQL, or use polars/narwhals",
            issue="IB-WIN-02",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=SUBSTRAIT_ARITHMETIC_WINDOW.RANK),
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
                                        "score",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="10"),
                                                CaptureValue(tag="integer", value="30"),
                                                CaptureValue(tag="integer", value="20"),
                                                CaptureValue(tag="integer", value="15"),
                                                CaptureValue(tag="integer", value="25"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(("shape", CaptureValue(tag="text", value="over group method=min")),),
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
                                CaptureValue(tag="integer", value="1"),
                                CaptureValue(tag="integer", value="2"),
                                CaptureValue(tag="integer", value="3"),
                                CaptureValue(tag="integer", value="1"),
                                CaptureValue(tag="integer", value="2"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(("historical_source_claim", CaptureValue(tag="text", value="historical 0-based rank")),),
            ),
            impact="rank/dense_rank/row_number return values one lower on ibis SQL",
            since="2026-08-06",
            workaround="Add 1 on ibis SQL, or use polars/narwhals",
            issue="IB-WIN-02",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=SUBSTRAIT_ARITHMETIC_WINDOW.ROW_NUMBER),
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
                                            ),
                                        ),
                                    ),
                                    (
                                        "score",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="30"),
                                                CaptureValue(tag="integer", value="10"),
                                                CaptureValue(tag="integer", value="20"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(("shape", CaptureValue(tag="text", value="row_number over group, sort group score")),),
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
                                CaptureValue(tag="integer", value="1"),
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
                        CaptureValue(tag="text", value="historical rank divergence/WindowFunction failure"),
                    ),
                ),
            ),
            impact="rank/dense_rank/row_number return values one lower on ibis SQL",
            since="2026-08-06",
            workaround="Add 1 on ibis SQL, or use polars/narwhals",
            issue="IB-WIN-02",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=SUBSTRAIT_ARITHMETIC_WINDOW.ROW_NUMBER),
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
                                        "score",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="10"),
                                                CaptureValue(tag="integer", value="30"),
                                                CaptureValue(tag="integer", value="20"),
                                                CaptureValue(tag="integer", value="15"),
                                                CaptureValue(tag="integer", value="25"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(("shape", CaptureValue(tag="text", value="over group method=min")),),
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
                                CaptureValue(tag="integer", value="1"),
                                CaptureValue(tag="integer", value="2"),
                                CaptureValue(tag="integer", value="3"),
                                CaptureValue(tag="integer", value="1"),
                                CaptureValue(tag="integer", value="2"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(("historical_source_claim", CaptureValue(tag="text", value="historical 0-based rank")),),
            ),
            impact="rank/dense_rank/row_number return values one lower on ibis SQL",
            since="2026-08-06",
            workaround="Add 1 on ibis SQL, or use polars/narwhals",
            issue="IB-WIN-02",
        ),
    ),
    changes=(),
)
