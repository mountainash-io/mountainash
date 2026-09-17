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
from mountainash.core.capabilities.schema import EntrypointStage
from mountainash.core.capabilities.schema import EntrypointStageTarget
from mountainash.core.capabilities.schema import OperationTarget
from mountainash.core.capabilities.schema import Scenario
from mountainash.core.capabilities.schema import TargetSurface
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_AGGREGATE
from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_MOUNTAINASH_REL

SEGMENT = CapabilitySegment(
    domain=Domain.RELATION,
    capabilities=(),
    manifestations=(
        DivergenceManifestation(
            key=ManifestationKey(
                target=CompositionTarget(
                    surface=TargetSurface.RELATION,
                    entrypoint=CallableRef(
                        module="mountainash.relations.core.relation_protocols.prtcl_relation_api",
                        qualname="GroupedRelationAPIProtocol.agg",
                    ),
                    operations=(FKEY_SUBSTRAIT_SCALAR_AGGREGATE.SUM,),
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
                                        "k",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="a"),
                                                CaptureValue(tag="text", value="a"),
                                                CaptureValue(tag="text", value="b"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "v",
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
                        ),
                    ),
                    execution=(
                        (
                            "shape",
                            CaptureValue(tag="text", value="group_by k unaliased sum"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.NAMING,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="inferred and materialized column sets equal"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="historical Ibis Sum(v) name"),
                    ),
                ),
            ),
            impact="Inferred schemas and Ibis runtime output names can disagree",
            since="2026-07-05",
            workaround="Always alias aggregate measures when pipelines may execute on Ibis",
            issue="IB-AGG-04",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=EntrypointStageTarget(
                    surface=TargetSurface.RELATION,
                    entrypoint=CallableRef(
                        module="mountainash.validation.runner", qualname="ValidationRunner.validate_relation"
                    ),
                    stage=EntrypointStage.MATERIALIZATION,
                ),
                scenario=Scenario(
                    arguments=(
                        (
                            "checks",
                            CaptureValue(
                                tag="sequence",
                                value=(
                                    CaptureValue(
                                        tag="mapping",
                                        value=(
                                            (
                                                "column",
                                                CaptureValue(tag="text", value="age"),
                                            ),
                                            (
                                                "kind",
                                                CaptureValue(tag="text", value="ScalarRule"),
                                            ),
                                            (
                                                "recipe",
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(
                                                            tag="sequence",
                                                            value=(CaptureValue(tag="text", value="mean"),),
                                                        ),
                                                        CaptureValue(
                                                            tag="sequence",
                                                            value=(
                                                                CaptureValue(tag="text", value="gt"),
                                                                CaptureValue(tag="integer", value="0"),
                                                            ),
                                                        ),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                        (
                            "relation",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "input",
                                        CaptureValue(tag="text", value="frame"),
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
                                        "age",
                                        CaptureValue(
                                            tag="mapping",
                                            value=(
                                                (
                                                    "logical_type",
                                                    CaptureValue(tag="text", value="null"),
                                                ),
                                                (
                                                    "nullable",
                                                    CaptureValue(tag="bool", value="true"),
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
                                        "age",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
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
                            "mode",
                            CaptureValue(tag="text", value="validate-relation"),
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
                        "historical",
                        CaptureValue(tag="bool", value="true"),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="failed"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "fresh_native_observation",
                        CaptureValue(tag="bool", value="false"),
                    ),
                    (
                        "historical",
                        CaptureValue(tag="bool", value="true"),
                    ),
                    (
                        "inferred_column",
                        CaptureValue(tag="text", value="untyped-NullColumn"),
                    ),
                ),
            ),
            impact="a ScalarRule verdict over an all-null column diverges on ibis-polars/ibis-sqlite; polars/narwhals compute the 'unknown' verdict (ibis-duckdb rejects the all-null table outright — IB-REL-06)",
            since="2026-08-06",
            workaround="Use a polars or narwhals backend for scalar verdicts over all-null columns",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=RKEY_MOUNTAINASH_REL.CONFORM),
                scenario=Scenario(
                    arguments=(),
                    options=(),
                    input_schema=(
                        (
                            "extra",
                            CaptureValue(tag="text", value="integer"),
                        ),
                        (
                            "raw_label",
                            CaptureValue(tag="text", value="string"),
                        ),
                        (
                            "raw_score",
                            CaptureValue(tag="text", value="string"),
                        ),
                    ),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "extra",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="10"),
                                                CaptureValue(tag="integer", value="20"),
                                                CaptureValue(tag="integer", value="30"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "raw_label",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="foo"),
                                                CaptureValue(tag="text", value="bar"),
                                                CaptureValue(tag="null", value=""),
                                            ),
                                        ),
                                    ),
                                    (
                                        "raw_score",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="1.5"),
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="text", value="3.5"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "stage",
                            CaptureValue(tag="text", value="logical_egress"),
                        ),
                        (
                            "terminal",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "method",
                                        CaptureValue(tag="text", value="to_polars"),
                                    ),
                                ),
                            ),
                        ),
                        (
                            "upstream_conform",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "apply_value_transforms",
                                        CaptureValue(tag="bool", value="true"),
                                    ),
                                    (
                                        "spec",
                                        CaptureValue(
                                            tag="mapping",
                                            value=(
                                                (
                                                    "fields",
                                                    CaptureValue(
                                                        tag="sequence",
                                                        value=(
                                                            CaptureValue(
                                                                tag="mapping",
                                                                value=(
                                                                    (
                                                                        "name",
                                                                        CaptureValue(tag="text", value="score"),
                                                                    ),
                                                                    (
                                                                        "null_fill",
                                                                        CaptureValue(tag="float", value="0x0.0p+0"),
                                                                    ),
                                                                    (
                                                                        "rename_from",
                                                                        CaptureValue(
                                                                            tag="mapping",
                                                                            value=(
                                                                                (
                                                                                    "field_path",
                                                                                    CaptureValue(
                                                                                        tag="sequence",
                                                                                        value=(
                                                                                            CaptureValue(
                                                                                                tag="text",
                                                                                                value="raw_score",
                                                                                            ),
                                                                                        ),
                                                                                    ),
                                                                                ),
                                                                            ),
                                                                        ),
                                                                    ),
                                                                    (
                                                                        "type",
                                                                        CaptureValue(tag="text", value="NUMBER"),
                                                                    ),
                                                                ),
                                                            ),
                                                            CaptureValue(
                                                                tag="mapping",
                                                                value=(
                                                                    (
                                                                        "name",
                                                                        CaptureValue(tag="text", value="label"),
                                                                    ),
                                                                    (
                                                                        "null_fill",
                                                                        CaptureValue(tag="text", value="n/a"),
                                                                    ),
                                                                    (
                                                                        "rename_from",
                                                                        CaptureValue(
                                                                            tag="mapping",
                                                                            value=(
                                                                                (
                                                                                    "field_path",
                                                                                    CaptureValue(
                                                                                        tag="sequence",
                                                                                        value=(
                                                                                            CaptureValue(
                                                                                                tag="text",
                                                                                                value="raw_label",
                                                                                            ),
                                                                                        ),
                                                                                    ),
                                                                                ),
                                                                            ),
                                                                        ),
                                                                    ),
                                                                    (
                                                                        "type",
                                                                        CaptureValue(tag="text", value="STRING"),
                                                                    ),
                                                                ),
                                                            ),
                                                        ),
                                                    ),
                                                ),
                                                (
                                                    "fields_match",
                                                    CaptureValue(tag="text", value="open"),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
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
                                CaptureValue(
                                    tag="text",
                                    value="score == [1.5,0.0,3.5]; label == ['foo','bar','n/a']; extra retained",
                                ),
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
                            value="conform multi-transform full pipeline raises IbisTypeError on all ibis backends (deferred type resolution rejects the chained transform)",
                        ),
                    ),
                ),
            ),
            impact="a full conform multi-transform pipeline raises on ibis-duckdb/ibis-polars/ibis-sqlite; polars/narwhals run it",
            since="2026-08-06",
            workaround="Use a polars or narwhals backend for full conform transform pipelines",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=RKEY_MOUNTAINASH_REL.CONFORM),
                scenario=Scenario(
                    arguments=(),
                    options=(),
                    input_schema=(
                        (
                            "id",
                            CaptureValue(tag="text", value="integer"),
                        ),
                        (
                            "n",
                            CaptureValue(tag="text", value="string"),
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
                                            ),
                                        ),
                                    ),
                                    (
                                        "n",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="1"),
                                                CaptureValue(tag="text", value="bad"),
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="text", value="3"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "stage",
                            CaptureValue(tag="text", value="logical_egress"),
                        ),
                        (
                            "terminal",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "method",
                                        CaptureValue(tag="text", value="to_polars"),
                                    ),
                                ),
                            ),
                        ),
                        (
                            "upstream_conform",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "contract",
                                        CaptureValue(
                                            tag="mapping",
                                            value=(
                                                (
                                                    "data_type",
                                                    CaptureValue(tag="text", value="discard_row"),
                                                ),
                                            ),
                                        ),
                                    ),
                                    (
                                        "spec",
                                        CaptureValue(
                                            tag="mapping",
                                            value=(
                                                (
                                                    "fields",
                                                    CaptureValue(
                                                        tag="sequence",
                                                        value=(
                                                            CaptureValue(
                                                                tag="mapping",
                                                                value=(
                                                                    (
                                                                        "name",
                                                                        CaptureValue(tag="text", value="n"),
                                                                    ),
                                                                    (
                                                                        "type",
                                                                        CaptureValue(tag="text", value="INTEGER"),
                                                                    ),
                                                                ),
                                                            ),
                                                        ),
                                                    ),
                                                ),
                                                (
                                                    "fields_match",
                                                    CaptureValue(tag="text", value="open"),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
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
                            value=(CaptureValue(tag="text", value="id == [1,3,4] and n == [1.0,None,3.0]"),),
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
                            value="conform discard-value/discard-row drift policies are unsupported on pandas/narwhals (unenriched BackendCapabilityError) and ibis-sqlite (OperationNotDefinedError)",
                        ),
                    ),
                ),
            ),
            impact="conform() discard_value/discard_row policies raise on pandas/narwhals and ibis-sqlite; polars and ibis-duckdb/ibis-polars apply them",
            since="2026-08-06",
            workaround="Use a polars backend or ibis-duckdb/ibis-polars for discard drift policies",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=RKEY_MOUNTAINASH_REL.CONFORM),
                scenario=Scenario(
                    arguments=(),
                    options=(),
                    input_schema=(
                        (
                            "n",
                            CaptureValue(tag="text", value="string"),
                        ),
                    ),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "n",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="1"),
                                                CaptureValue(tag="text", value="bad"),
                                                CaptureValue(tag="text", value="3"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "stage",
                            CaptureValue(tag="text", value="logical_egress"),
                        ),
                        (
                            "terminal",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "method",
                                        CaptureValue(tag="text", value="to_polars"),
                                    ),
                                ),
                            ),
                        ),
                        (
                            "upstream_conform",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "contract",
                                        CaptureValue(
                                            tag="mapping",
                                            value=(
                                                (
                                                    "data_type",
                                                    CaptureValue(tag="text", value="discard_value"),
                                                ),
                                            ),
                                        ),
                                    ),
                                    (
                                        "spec",
                                        CaptureValue(
                                            tag="mapping",
                                            value=(
                                                (
                                                    "fields",
                                                    CaptureValue(
                                                        tag="sequence",
                                                        value=(
                                                            CaptureValue(
                                                                tag="mapping",
                                                                value=(
                                                                    (
                                                                        "name",
                                                                        CaptureValue(tag="text", value="n"),
                                                                    ),
                                                                    (
                                                                        "type",
                                                                        CaptureValue(tag="text", value="INTEGER"),
                                                                    ),
                                                                ),
                                                            ),
                                                        ),
                                                    ),
                                                ),
                                                (
                                                    "fields_match",
                                                    CaptureValue(tag="text", value="equal"),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
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
                                CaptureValue(
                                    tag="text", value="_as_float_list(result['n'].to_list()) == [1.0, None, 3.0]"
                                ),
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
                            value="conform discard-value/discard-row drift policies are unsupported on pandas/narwhals (unenriched BackendCapabilityError) and ibis-sqlite (OperationNotDefinedError)",
                        ),
                    ),
                ),
            ),
            impact="conform() discard_value/discard_row policies raise on pandas/narwhals and ibis-sqlite; polars and ibis-duckdb/ibis-polars apply them",
            since="2026-08-06",
            workaround="Use a polars backend or ibis-duckdb/ibis-polars for discard drift policies",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=RKEY_MOUNTAINASH_REL.CONFORM),
                scenario=Scenario(
                    arguments=(),
                    options=(),
                    input_schema=(
                        (
                            "other",
                            CaptureValue(tag="text", value="string"),
                        ),
                        (
                            "payload",
                            CaptureValue(tag="text", value="struct{id: integer}"),
                        ),
                    ),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "other",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="x"),
                                                CaptureValue(tag="text", value="y"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "payload",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="mapping",
                                                    value=(
                                                        (
                                                            "id",
                                                            CaptureValue(tag="integer", value="1"),
                                                        ),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="mapping",
                                                    value=(
                                                        (
                                                            "id",
                                                            CaptureValue(tag="integer", value="2"),
                                                        ),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "stage",
                            CaptureValue(tag="text", value="logical_egress"),
                        ),
                        (
                            "terminal",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "method",
                                        CaptureValue(tag="text", value="to_polars"),
                                    ),
                                ),
                            ),
                        ),
                        (
                            "upstream_conform",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "contract",
                                        CaptureValue(tag="null", value=""),
                                    ),
                                    (
                                        "spec",
                                        CaptureValue(
                                            tag="mapping",
                                            value=(
                                                (
                                                    "fields",
                                                    CaptureValue(
                                                        tag="sequence",
                                                        value=(
                                                            CaptureValue(
                                                                tag="mapping",
                                                                value=(
                                                                    (
                                                                        "name",
                                                                        CaptureValue(tag="text", value="pid"),
                                                                    ),
                                                                    (
                                                                        "rename_from",
                                                                        CaptureValue(
                                                                            tag="mapping",
                                                                            value=(
                                                                                (
                                                                                    "field_path",
                                                                                    CaptureValue(
                                                                                        tag="sequence",
                                                                                        value=(
                                                                                            CaptureValue(
                                                                                                tag="text",
                                                                                                value="payload",
                                                                                            ),
                                                                                            CaptureValue(
                                                                                                tag="text", value="id"
                                                                                            ),
                                                                                        ),
                                                                                    ),
                                                                                ),
                                                                            ),
                                                                        ),
                                                                    ),
                                                                    (
                                                                        "type",
                                                                        CaptureValue(tag="text", value="INTEGER"),
                                                                    ),
                                                                ),
                                                            ),
                                                        ),
                                                    ),
                                                ),
                                                (
                                                    "fields_match",
                                                    CaptureValue(tag="text", value="subset"),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
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
                            value=(CaptureValue(tag="text", value="result pid == [1,2] and columns == ['pid']"),),
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
                            value="conform struct dotted-source extraction is unsupported on pandas/narwhals-pandas (TypeError) and ibis-sqlite (UnsupportedBackendType) — no native struct column type",
                        ),
                    ),
                ),
            ),
            impact="conform() with a dotted struct source path raises on pandas/narwhals-pandas/ibis-sqlite; polars and ibis-duckdb/ibis-polars extract it",
            since="2026-08-06",
            workaround="Use a polars backend or ibis-duckdb/ibis-polars for struct dotted-source conform",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=RKEY_MOUNTAINASH_REL.CONFORM),
                scenario=Scenario(
                    arguments=(),
                    options=(),
                    input_schema=(
                        (
                            "payload",
                            CaptureValue(tag="text", value="struct{id: integer}"),
                        ),
                    ),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "payload",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="mapping",
                                                    value=(
                                                        (
                                                            "id",
                                                            CaptureValue(tag="integer", value="1"),
                                                        ),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="mapping",
                                                    value=(
                                                        (
                                                            "id",
                                                            CaptureValue(tag="integer", value="2"),
                                                        ),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "stage",
                            CaptureValue(tag="text", value="logical_egress"),
                        ),
                        (
                            "terminal",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "method",
                                        CaptureValue(tag="text", value="to_polars"),
                                    ),
                                ),
                            ),
                        ),
                        (
                            "upstream_conform",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "contract",
                                        CaptureValue(tag="null", value=""),
                                    ),
                                    (
                                        "spec",
                                        CaptureValue(
                                            tag="mapping",
                                            value=(
                                                (
                                                    "fields",
                                                    CaptureValue(
                                                        tag="sequence",
                                                        value=(
                                                            CaptureValue(
                                                                tag="mapping",
                                                                value=(
                                                                    (
                                                                        "name",
                                                                        CaptureValue(tag="text", value="pid"),
                                                                    ),
                                                                    (
                                                                        "rename_from",
                                                                        CaptureValue(
                                                                            tag="mapping",
                                                                            value=(
                                                                                (
                                                                                    "field_path",
                                                                                    CaptureValue(
                                                                                        tag="sequence",
                                                                                        value=(
                                                                                            CaptureValue(
                                                                                                tag="text",
                                                                                                value="payload",
                                                                                            ),
                                                                                            CaptureValue(
                                                                                                tag="text", value="id"
                                                                                            ),
                                                                                        ),
                                                                                    ),
                                                                                ),
                                                                            ),
                                                                        ),
                                                                    ),
                                                                    (
                                                                        "type",
                                                                        CaptureValue(tag="text", value="INTEGER"),
                                                                    ),
                                                                ),
                                                            ),
                                                        ),
                                                    ),
                                                ),
                                                (
                                                    "fields_match",
                                                    CaptureValue(tag="text", value="equal"),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
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
                            tag="sequence", value=(CaptureValue(tag="text", value="result['pid'].to_list() == [1, 2]"),)
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
                            value="conform struct dotted-source extraction is unsupported on pandas/narwhals-pandas (TypeError) and ibis-sqlite (UnsupportedBackendType) — no native struct column type",
                        ),
                    ),
                ),
            ),
            impact="conform() with a dotted struct source path raises on pandas/narwhals-pandas/ibis-sqlite; polars and ibis-duckdb/ibis-polars extract it",
            since="2026-08-06",
            workaround="Use a polars backend or ibis-duckdb/ibis-polars for struct dotted-source conform",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=RKEY_MOUNTAINASH_REL.DROP_NANS),
                scenario=Scenario(
                    arguments=(
                        (
                            "subset",
                            CaptureValue(tag="null", value=""),
                        ),
                    ),
                    options=(),
                    input_schema=(
                        (
                            "a",
                            CaptureValue(tag="text", value="float"),
                        ),
                    ),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "a",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="float", value="0x1.0000000000000p+0"),
                                                CaptureValue(tag="float", value="nan"),
                                                CaptureValue(tag="float", value="0x1.8000000000000p+1"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "b",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="float", value="0x1.4000000000000p+3"),
                                                CaptureValue(tag="float", value="0x1.4000000000000p+4"),
                                                CaptureValue(tag="float", value="0x1.e000000000000p+4"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
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
                                        CaptureValue(tag="text", value="to_dicts"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
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
                                CaptureValue(tag="text", value="len(result) == 2 and result a values are [1.0, 3.0]"),
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
                            value="ibis-sqlite lacks array/pivot relational translations: drop_nans, unpivot/melt raise OperationNotDefinedError",
                        ),
                    ),
                ),
            ),
            impact="Relation.drop_nans()/unpivot()/melt() raise on ibis-sqlite; other backends compute them",
            since="2026-08-06",
            workaround="Use ibis-duckdb or a polars/narwhals backend for these relational ops",
            issue="IB-REL-10",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=RKEY_MOUNTAINASH_REL.JOIN_ASOF),
                scenario=Scenario(
                    arguments=(
                        (
                            "by",
                            CaptureValue(tag="sequence", value=(CaptureValue(tag="text", value="g"),)),
                        ),
                        (
                            "on",
                            CaptureValue(tag="text", value="t"),
                        ),
                        (
                            "right",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "relation_ref",
                                        CaptureValue(tag="text", value="right"),
                                    ),
                                ),
                            ),
                        ),
                        (
                            "strategy",
                            CaptureValue(tag="text", value="backward"),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "left_right_fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "left",
                                        CaptureValue(
                                            tag="mapping",
                                            value=(
                                                (
                                                    "g",
                                                    CaptureValue(
                                                        tag="sequence",
                                                        value=(
                                                            CaptureValue(tag="text", value="a"),
                                                            CaptureValue(tag="text", value="b"),
                                                            CaptureValue(tag="text", value="a"),
                                                            CaptureValue(tag="text", value="b"),
                                                        ),
                                                    ),
                                                ),
                                                (
                                                    "t",
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
                                                    "val",
                                                    CaptureValue(
                                                        tag="sequence",
                                                        value=(
                                                            CaptureValue(tag="text", value="a1"),
                                                            CaptureValue(tag="text", value="b2"),
                                                            CaptureValue(tag="text", value="a3"),
                                                            CaptureValue(tag="text", value="b4"),
                                                        ),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                    (
                                        "right",
                                        CaptureValue(
                                            tag="mapping",
                                            value=(
                                                (
                                                    "g",
                                                    CaptureValue(
                                                        tag="sequence",
                                                        value=(
                                                            CaptureValue(tag="text", value="a"),
                                                            CaptureValue(tag="text", value="b"),
                                                            CaptureValue(tag="text", value="a"),
                                                            CaptureValue(tag="text", value="b"),
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
                                                            CaptureValue(tag="integer", value="50"),
                                                        ),
                                                    ),
                                                ),
                                                (
                                                    "t",
                                                    CaptureValue(
                                                        tag="sequence",
                                                        value=(
                                                            CaptureValue(tag="integer", value="1"),
                                                            CaptureValue(tag="integer", value="2"),
                                                            CaptureValue(tag="integer", value="3"),
                                                            CaptureValue(tag="integer", value="5"),
                                                        ),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "lazy_or_deferred_plan",
                            CaptureValue(tag="bool", value="true"),
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
                                        CaptureValue(tag="text", value="to_dicts"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
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
                                CaptureValue(
                                    tag="text",
                                    value="result == Polars oracle (source explicitly says matched values remain correct)",
                                ),
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
                            value="Ibis's SQL-backend asof paths (native duckdb backward, and the emulation used for forward/nearest and all sqlite strategies) order output by [by, on] for determinism, which groups rows contiguously by `by` value; Polars (and narwhals/pandas natively, and ibis-polars natively) instead preserve the left input's own row order, which differs whenever `by` groups are interleaved in that input",
                        ),
                    ),
                ),
            ),
            impact="Relation.join_asof(by=...) on ibis-duckdb/ibis-sqlite returns rows grouped by `by` value rather than in left input order when groups interleave; matched values are always correct, only row position differs",
            since="2026-08-19",
            workaround="Use ibis-polars, polars, or narwhals if exact left-input row order must be preserved for interleaved by-groups",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=RKEY_MOUNTAINASH_REL.JOIN_ASOF),
                scenario=Scenario(
                    arguments=(
                        (
                            "on",
                            CaptureValue(tag="text", value="t"),
                        ),
                        (
                            "right",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "relation_ref",
                                        CaptureValue(tag="text", value="right"),
                                    ),
                                ),
                            ),
                        ),
                        (
                            "strategy",
                            CaptureValue(tag="text", value="backward"),
                        ),
                        (
                            "tolerance",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "source_expression",
                                        CaptureValue(tag="text", value="timedelta(minutes=2)"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "left_right_fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "left",
                                        CaptureValue(
                                            tag="mapping",
                                            value=(
                                                (
                                                    "t",
                                                    CaptureValue(
                                                        tag="sequence",
                                                        value=(
                                                            CaptureValue(
                                                                tag="mapping",
                                                                value=(
                                                                    (
                                                                        "source_expression",
                                                                        CaptureValue(
                                                                            tag="text", value="datetime(2026,1,1,0,0)"
                                                                        ),
                                                                    ),
                                                                ),
                                                            ),
                                                            CaptureValue(
                                                                tag="mapping",
                                                                value=(
                                                                    (
                                                                        "source_expression",
                                                                        CaptureValue(
                                                                            tag="text", value="datetime(2026,1,1,0,3)"
                                                                        ),
                                                                    ),
                                                                ),
                                                            ),
                                                        ),
                                                    ),
                                                ),
                                                (
                                                    "val",
                                                    CaptureValue(
                                                        tag="sequence",
                                                        value=(
                                                            CaptureValue(tag="text", value="a"),
                                                            CaptureValue(tag="text", value="b"),
                                                        ),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                    (
                                        "right",
                                        CaptureValue(
                                            tag="mapping",
                                            value=(
                                                (
                                                    "score",
                                                    CaptureValue(
                                                        tag="sequence",
                                                        value=(
                                                            CaptureValue(tag="integer", value="10"),
                                                            CaptureValue(tag="integer", value="40"),
                                                        ),
                                                    ),
                                                ),
                                                (
                                                    "t",
                                                    CaptureValue(
                                                        tag="sequence",
                                                        value=(
                                                            CaptureValue(
                                                                tag="mapping",
                                                                value=(
                                                                    (
                                                                        "source_expression",
                                                                        CaptureValue(
                                                                            tag="text", value="datetime(2026,1,1,0,1)"
                                                                        ),
                                                                    ),
                                                                ),
                                                            ),
                                                            CaptureValue(
                                                                tag="mapping",
                                                                value=(
                                                                    (
                                                                        "source_expression",
                                                                        CaptureValue(
                                                                            tag="text", value="datetime(2026,1,1,0,4)"
                                                                        ),
                                                                    ),
                                                                ),
                                                            ),
                                                        ),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "lazy_or_deferred_plan",
                            CaptureValue(tag="bool", value="true"),
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
                                        CaptureValue(tag="text", value="to_dicts"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
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
                            tag="sequence", value=(CaptureValue(tag="text", value="result == Polars oracle"),)
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
                            value="ibis-sqlite has no TimestampDelta translation (OperationNotDefinedError, probe-confirmed on ibis 12.0.0); the asof emulation cannot compute a temporal distance there",
                        ),
                    ),
                ),
            ),
            impact="Relation.join_asof(strategy='nearest') or tolerance=... over a temporal `on` column raises BackendCapabilityError on ibis-sqlite; forward/backward over temporal keys (no distance needed) work fine there",
            since="2026-08-18",
            workaround="Use ibis-duckdb, polars, or narwhals for temporal nearest/tolerance asof joins",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=RKEY_MOUNTAINASH_REL.JOIN_ASOF),
                scenario=Scenario(
                    arguments=(
                        (
                            "on",
                            CaptureValue(tag="text", value="t"),
                        ),
                        (
                            "right",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "relation_ref",
                                        CaptureValue(tag="text", value="right"),
                                    ),
                                ),
                            ),
                        ),
                        (
                            "strategy",
                            CaptureValue(tag="text", value="nearest"),
                        ),
                    ),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "left_right_fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "left",
                                        CaptureValue(
                                            tag="mapping",
                                            value=(
                                                (
                                                    "t",
                                                    CaptureValue(
                                                        tag="sequence",
                                                        value=(
                                                            CaptureValue(
                                                                tag="mapping",
                                                                value=(
                                                                    (
                                                                        "source_expression",
                                                                        CaptureValue(
                                                                            tag="text", value="datetime(2026,1,1,0,0)"
                                                                        ),
                                                                    ),
                                                                ),
                                                            ),
                                                            CaptureValue(
                                                                tag="mapping",
                                                                value=(
                                                                    (
                                                                        "source_expression",
                                                                        CaptureValue(
                                                                            tag="text", value="datetime(2026,1,1,0,3)"
                                                                        ),
                                                                    ),
                                                                ),
                                                            ),
                                                        ),
                                                    ),
                                                ),
                                                (
                                                    "val",
                                                    CaptureValue(
                                                        tag="sequence",
                                                        value=(
                                                            CaptureValue(tag="text", value="a"),
                                                            CaptureValue(tag="text", value="b"),
                                                        ),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                    (
                                        "right",
                                        CaptureValue(
                                            tag="mapping",
                                            value=(
                                                (
                                                    "score",
                                                    CaptureValue(
                                                        tag="sequence",
                                                        value=(
                                                            CaptureValue(tag="integer", value="10"),
                                                            CaptureValue(tag="integer", value="40"),
                                                        ),
                                                    ),
                                                ),
                                                (
                                                    "t",
                                                    CaptureValue(
                                                        tag="sequence",
                                                        value=(
                                                            CaptureValue(
                                                                tag="mapping",
                                                                value=(
                                                                    (
                                                                        "source_expression",
                                                                        CaptureValue(
                                                                            tag="text", value="datetime(2026,1,1,0,1)"
                                                                        ),
                                                                    ),
                                                                ),
                                                            ),
                                                            CaptureValue(
                                                                tag="mapping",
                                                                value=(
                                                                    (
                                                                        "source_expression",
                                                                        CaptureValue(
                                                                            tag="text", value="datetime(2026,1,1,0,4)"
                                                                        ),
                                                                    ),
                                                                ),
                                                            ),
                                                        ),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "lazy_or_deferred_plan",
                            CaptureValue(tag="bool", value="true"),
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
                                        CaptureValue(tag="text", value="to_dicts"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
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
                            tag="sequence", value=(CaptureValue(tag="text", value="result == Polars oracle"),)
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
                            value="ibis-sqlite has no TimestampDelta translation (OperationNotDefinedError, probe-confirmed on ibis 12.0.0); the asof emulation cannot compute a temporal distance there",
                        ),
                    ),
                ),
            ),
            impact="Relation.join_asof(strategy='nearest') or tolerance=... over a temporal `on` column raises BackendCapabilityError on ibis-sqlite; forward/backward over temporal keys (no distance needed) work fine there",
            since="2026-08-18",
            workaround="Use ibis-duckdb, polars, or narwhals for temporal nearest/tolerance asof joins",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=RKEY_MOUNTAINASH_REL.PIVOT),
                scenario=Scenario(
                    arguments=(
                        (
                            "aggregate_function",
                            CaptureValue(tag="text", value="first"),
                        ),
                        (
                            "index",
                            CaptureValue(tag="sequence", value=(CaptureValue(tag="text", value="id"),)),
                        ),
                        (
                            "on",
                            CaptureValue(tag="text", value="category"),
                        ),
                        (
                            "values",
                            CaptureValue(tag="text", value="value"),
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
                                        "category",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="x"),
                                                CaptureValue(tag="text", value="y"),
                                                CaptureValue(tag="text", value="x"),
                                                CaptureValue(tag="text", value="y"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "id",
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
                                    (
                                        "value",
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
                    execution=(
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
                                        CaptureValue(tag="text", value="to_dicts"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
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
                            value=(CaptureValue(tag="text", value="row x/y values are (10,20) then (30,40)"),),
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
                            value="pivot (long-to-wide) is unsupported on ibis (TypeError) and narwhals-lazy (AttributeError)",
                        ),
                    ),
                ),
            ),
            impact="Relation.pivot() raises on all ibis backends and narwhals-lazy; polars and eager narwhals compute it",
            since="2026-08-06",
            workaround="Use a polars or eager narwhals backend for pivot",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=RKEY_MOUNTAINASH_REL.UNPIVOT),
                scenario=Scenario(
                    arguments=(
                        (
                            "index",
                            CaptureValue(tag="sequence", value=(CaptureValue(tag="text", value="a"),)),
                        ),
                        (
                            "on",
                            CaptureValue(tag="sequence", value=(CaptureValue(tag="text", value="b"),)),
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
                                        "a",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="1"),
                                                CaptureValue(tag="integer", value="2"),
                                                CaptureValue(tag="integer", value="3"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "b",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="4"),
                                                CaptureValue(tag="integer", value="5"),
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
                            "public_alias",
                            CaptureValue(tag="text", value="melt"),
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
                                        CaptureValue(tag="text", value="to_dicts"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
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
                            tag="sequence", value=(CaptureValue(tag="text", value="melt_result == unpivot_result"),)
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
                            value="ibis-sqlite lacks array/pivot relational translations: drop_nans, unpivot/melt raise OperationNotDefinedError",
                        ),
                    ),
                ),
            ),
            impact="Relation.drop_nans()/unpivot()/melt() raise on ibis-sqlite; other backends compute them",
            since="2026-08-06",
            workaround="Use ibis-duckdb or a polars/narwhals backend for these relational ops",
            issue="IB-REL-10",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=RKEY_MOUNTAINASH_REL.UNPIVOT),
                scenario=Scenario(
                    arguments=(
                        (
                            "index",
                            CaptureValue(tag="sequence", value=(CaptureValue(tag="text", value="id"),)),
                        ),
                        (
                            "on",
                            CaptureValue(
                                tag="sequence",
                                value=(
                                    CaptureValue(tag="text", value="x"),
                                    CaptureValue(tag="text", value="y"),
                                ),
                            ),
                        ),
                        (
                            "value_name",
                            CaptureValue(tag="text", value="value"),
                        ),
                        (
                            "variable_name",
                            CaptureValue(tag="text", value="variable"),
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
                                        "id",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="1"),
                                                CaptureValue(tag="integer", value="2"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "x",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="10"),
                                                CaptureValue(tag="integer", value="20"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "y",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="30"),
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
                                        CaptureValue(tag="text", value="to_dicts"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
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
                                CaptureValue(
                                    tag="text",
                                    value="result_sorted == [{'id': 1, 'variable': 'x', 'value': 10}, {'id': 1, 'variable': 'y', 'value': 30}, {'id': 2, 'variable': 'x', 'value': 20}, {'id': 2, 'variable': 'y', 'value': 40}]",
                                ),
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
                            value="ibis-sqlite lacks array/pivot relational translations: drop_nans, unpivot/melt raise OperationNotDefinedError",
                        ),
                    ),
                ),
            ),
            impact="Relation.drop_nans()/unpivot()/melt() raise on ibis-sqlite; other backends compute them",
            since="2026-08-06",
            workaround="Use ibis-duckdb or a polars/narwhals backend for these relational ops",
            issue="IB-REL-10",
        ),
    ),
    changes=(),
)
