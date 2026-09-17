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
                target=OperationTarget(operation=SUBSTRAIT_ARITHMETIC_WINDOW.CUME_DIST),
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
                                                CaptureValue(tag="integer", value="20"),
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
                    execution=(("shape", CaptureValue(tag="text", value="over group order_by=score")),),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(("historical_source_claim", CaptureValue(tag="text", value="all values in [0,1]")),),
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
                                                CaptureValue(tag="integer", value="30"),
                                                CaptureValue(tag="integer", value="30"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(("shape", CaptureValue(tag="text", value="rank method=dense over group")),),
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
                        CaptureValue(tag="text", value="rank(method='dense'|'ordinal') raises off Polars"),
                    ),
                ),
            ),
            impact="rank(method='dense'|'ordinal') raises off Polars",
            since="2026-08-06",
            workaround="Use dense_rank()/row_number() directly, or Polars",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=SUBSTRAIT_ARITHMETIC_WINDOW.NTH_VALUE),
                scenario=Scenario(
                    arguments=(("window_offset", CaptureValue(tag="integer", value="2")),),
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
                                                CaptureValue(tag="integer", value="10"),
                                                CaptureValue(tag="integer", value="20"),
                                                CaptureValue(tag="integer", value="30"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(("shape", CaptureValue(tag="text", value="over group n=2")),),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping", value=(("historical_source_claim", CaptureValue(tag="text", value="all values 20")),)
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
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=SUBSTRAIT_ARITHMETIC_WINDOW.NTILE),
                scenario=Scenario(
                    arguments=(("x", CaptureValue(tag="integer", value="2")),),
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
                    execution=(("shape", CaptureValue(tag="text", value="ntile=2 over group")),),
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
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    ("historical_source_claim", CaptureValue(tag="text", value="ntile() is unsupported off Polars")),
                ),
            ),
            impact="ntile() is unsupported off Polars",
            since="2026-08-06",
            workaround="Use a Polars backend for ntile()",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=SUBSTRAIT_ARITHMETIC_WINDOW.PERCENT_RANK),
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
                                                CaptureValue(tag="integer", value="20"),
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
                    execution=(("shape", CaptureValue(tag="text", value="over group order_by=score")),),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(("historical_source_claim", CaptureValue(tag="text", value="all values in [0,1]")),),
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
                                                CaptureValue(tag="integer", value="30"),
                                                CaptureValue(tag="integer", value="30"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(("shape", CaptureValue(tag="text", value="rank method=ordinal over group")),),
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
                        CaptureValue(tag="text", value="rank(method='dense'|'ordinal') raises off Polars"),
                    ),
                ),
            ),
            impact="rank(method='dense'|'ordinal') raises off Polars",
            since="2026-08-06",
            workaround="Use dense_rank()/row_number() directly, or Polars",
            issue=None,
        ),
    ),
    changes=(),
)
