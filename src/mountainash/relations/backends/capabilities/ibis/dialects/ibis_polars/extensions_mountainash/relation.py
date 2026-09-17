"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import DivergenceManifestation
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

from mountainash.core.capabilities.declarations import Domain
from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_MOUNTAINASH_REL
from mountainash.core.capabilities.declarations import CapabilityKey
from mountainash.core.capabilities.schema import CapabilityLevel


from mountainash.core.capabilities.declarations import CapabilityAssertion
from mountainash.core.capabilities.schema import ClauseOp
from mountainash.core.capabilities.schema import Clause
from mountainash.core.capabilities.schema import Predicate
from mountainash.core.capabilities.declarations import Selector
from mountainash.core.capabilities.declarations import CapabilitySegment

SEGMENT = CapabilitySegment(
    domain=Domain.RELATION,
    capabilities=(
        CapabilityAssertion(
            key=CapabilityKey(operation=RKEY_MOUNTAINASH_REL.WITH_ROW_INDEX, subject="*"),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-01",
            message="with_row_index lowers to a window function (row_number); the ibis Polars backend has no WindowFunction translation rule.",
            workaround="Use ibis-duckdb/ibis-sqlite, or polars/narwhals backends.",
            issue="IB-REL-01",
            probe_exempt="relation op-level gap; covered by relation with_row_index cross-backend tests",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=RKEY_MOUNTAINASH_REL.JOIN_ASOF,
                subject="strategy",
                selector=Selector(
                    kind="predicate",
                    value=Predicate(
                        clauses=(
                            Clause(
                                path="strategy",
                                op=ClauseOp.IN,
                                operand=frozenset(
                                    (
                                        "forward",
                                        "nearest",
                                    )
                                ),
                            ),
                        )
                    ),
                ),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-18",
            message="join_asof forward/nearest lowers to a non-equality candidate join; the ibis Polars backend rejects non-equality join predicates (TypeError: Only equality join predicates supported with pandas).",
            workaround="Use ibis-duckdb/ibis-sqlite, or polars/narwhals backends.",
            issue="IB-REL-15",
        ),
    ),
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
                            CaptureValue(tag="text", value="forward"),
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
                                                            CaptureValue(tag="integer", value="1"),
                                                            CaptureValue(tag="integer", value="3"),
                                                            CaptureValue(tag="integer", value="5"),
                                                            CaptureValue(tag="integer", value="7"),
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
                                                            CaptureValue(tag="text", value="c"),
                                                            CaptureValue(tag="text", value="d"),
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
                                                            CaptureValue(tag="integer", value="20"),
                                                            CaptureValue(tag="integer", value="40"),
                                                            CaptureValue(tag="integer", value="60"),
                                                        ),
                                                    ),
                                                ),
                                                (
                                                    "t",
                                                    CaptureValue(
                                                        tag="sequence",
                                                        value=(
                                                            CaptureValue(tag="integer", value="2"),
                                                            CaptureValue(tag="integer", value="4"),
                                                            CaptureValue(tag="integer", value="6"),
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
                            tag="sequence", value=(CaptureValue(tag="text", value="result == Polars join_asof oracle"),)
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
                            value="ibis-polars rejects the emulation's non-equality candidate join (TypeError: Only equality join predicates supported with pandas, probe-confirmed); forward/nearest strategies are permanently capability-gated there",
                        ),
                    ),
                ),
            ),
            impact="Relation.join_asof(strategy='forward'|'nearest') raises BackendCapabilityError on ibis-polars; backward is native and unaffected",
            since="2026-08-18",
            workaround="Use ibis-duckdb, ibis-sqlite, polars, or narwhals for forward/nearest asof joins",
            issue="IB-REL-15",
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
                                                            CaptureValue(tag="integer", value="1"),
                                                            CaptureValue(tag="integer", value="3"),
                                                            CaptureValue(tag="integer", value="5"),
                                                            CaptureValue(tag="integer", value="7"),
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
                                                            CaptureValue(tag="text", value="c"),
                                                            CaptureValue(tag="text", value="d"),
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
                                                            CaptureValue(tag="integer", value="20"),
                                                            CaptureValue(tag="integer", value="40"),
                                                            CaptureValue(tag="integer", value="60"),
                                                        ),
                                                    ),
                                                ),
                                                (
                                                    "t",
                                                    CaptureValue(
                                                        tag="sequence",
                                                        value=(
                                                            CaptureValue(tag="integer", value="2"),
                                                            CaptureValue(tag="integer", value="4"),
                                                            CaptureValue(tag="integer", value="6"),
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
                            tag="sequence", value=(CaptureValue(tag="text", value="result == Polars join_asof oracle"),)
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
                            value="ibis-polars rejects the emulation's non-equality candidate join (TypeError: Only equality join predicates supported with pandas, probe-confirmed); forward/nearest strategies are permanently capability-gated there",
                        ),
                    ),
                ),
            ),
            impact="Relation.join_asof(strategy='forward'|'nearest') raises BackendCapabilityError on ibis-polars; backward is native and unaffected",
            since="2026-08-18",
            workaround="Use ibis-duckdb, ibis-sqlite, polars, or narwhals for forward/nearest asof joins",
            issue="IB-REL-15",
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
                                                            CaptureValue(tag="integer", value="1"),
                                                            CaptureValue(tag="integer", value="5"),
                                                        ),
                                                    ),
                                                ),
                                                (
                                                    "val",
                                                    CaptureValue(
                                                        tag="sequence",
                                                        value=(
                                                            CaptureValue(tag="text", value="L1"),
                                                            CaptureValue(tag="text", value="L5"),
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
                                                    "t",
                                                    CaptureValue(
                                                        tag="sequence",
                                                        value=(
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
                                                            CaptureValue(tag="text", value="R3"),
                                                            CaptureValue(tag="text", value="R4"),
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
                            tag="sequence", value=(CaptureValue(tag="text", value="result == Polars join_asof oracle"),)
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
                            value="ibis-polars rejects the emulation's non-equality candidate join (TypeError: Only equality join predicates supported with pandas, probe-confirmed); forward/nearest strategies are permanently capability-gated there",
                        ),
                    ),
                ),
            ),
            impact="Relation.join_asof(strategy='forward'|'nearest') raises BackendCapabilityError on ibis-polars; backward is native and unaffected",
            since="2026-08-18",
            workaround="Use ibis-duckdb, ibis-sqlite, polars, or narwhals for forward/nearest asof joins",
            issue="IB-REL-15",
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
                                                        tag="sequence", value=(CaptureValue(tag="integer", value="5"),)
                                                    ),
                                                ),
                                                (
                                                    "val",
                                                    CaptureValue(
                                                        tag="sequence", value=(CaptureValue(tag="text", value="x"),)
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
                                                            CaptureValue(tag="integer", value="40"),
                                                            CaptureValue(tag="integer", value="60"),
                                                        ),
                                                    ),
                                                ),
                                                (
                                                    "t",
                                                    CaptureValue(
                                                        tag="sequence",
                                                        value=(
                                                            CaptureValue(tag="integer", value="4"),
                                                            CaptureValue(tag="integer", value="6"),
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
                            tag="sequence", value=(CaptureValue(tag="text", value="result == Polars join_asof oracle"),)
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
                            value="ibis-polars rejects the emulation's non-equality candidate join (TypeError: Only equality join predicates supported with pandas, probe-confirmed); forward/nearest strategies are permanently capability-gated there",
                        ),
                    ),
                ),
            ),
            impact="Relation.join_asof(strategy='forward'|'nearest') raises BackendCapabilityError on ibis-polars; backward is native and unaffected",
            since="2026-08-18",
            workaround="Use ibis-duckdb, ibis-sqlite, polars, or narwhals for forward/nearest asof joins",
            issue="IB-REL-15",
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
                                                        tag="sequence", value=(CaptureValue(tag="integer", value="5"),)
                                                    ),
                                                ),
                                                (
                                                    "val",
                                                    CaptureValue(
                                                        tag="sequence", value=(CaptureValue(tag="text", value="x"),)
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
                                                            CaptureValue(tag="integer", value="51"),
                                                            CaptureValue(tag="integer", value="52"),
                                                            CaptureValue(tag="integer", value="70"),
                                                        ),
                                                    ),
                                                ),
                                                (
                                                    "t",
                                                    CaptureValue(
                                                        tag="sequence",
                                                        value=(
                                                            CaptureValue(tag="integer", value="5"),
                                                            CaptureValue(tag="integer", value="5"),
                                                            CaptureValue(tag="integer", value="7"),
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
                            tag="sequence", value=(CaptureValue(tag="text", value="result == Polars join_asof oracle"),)
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
                            value="ibis-polars rejects the emulation's non-equality candidate join (TypeError: Only equality join predicates supported with pandas, probe-confirmed); forward/nearest strategies are permanently capability-gated there",
                        ),
                    ),
                ),
            ),
            impact="Relation.join_asof(strategy='forward'|'nearest') raises BackendCapabilityError on ibis-polars; backward is native and unaffected",
            since="2026-08-18",
            workaround="Use ibis-duckdb, ibis-sqlite, polars, or narwhals for forward/nearest asof joins",
            issue="IB-REL-15",
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
                            tag="sequence", value=(CaptureValue(tag="text", value="result == Polars join_asof oracle"),)
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
                            value="ibis-polars rejects the emulation's non-equality candidate join (TypeError: Only equality join predicates supported with pandas, probe-confirmed); forward/nearest strategies are permanently capability-gated there",
                        ),
                    ),
                ),
            ),
            impact="Relation.join_asof(strategy='forward'|'nearest') raises BackendCapabilityError on ibis-polars; backward is native and unaffected",
            since="2026-08-18",
            workaround="Use ibis-duckdb, ibis-sqlite, polars, or narwhals for forward/nearest asof joins",
            issue="IB-REL-15",
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
    ),
)
