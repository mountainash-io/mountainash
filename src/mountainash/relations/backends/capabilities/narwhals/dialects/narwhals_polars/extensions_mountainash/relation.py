"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import CapabilitySegment
from mountainash.core.capabilities.declarations import DivergenceManifestation
from mountainash.core.capabilities.declarations import Domain
from mountainash.core.capabilities.declarations import ManifestationKey
from mountainash.core.capabilities.schema import CallableRef
from mountainash.core.capabilities.schema import CaptureValue
from mountainash.core.capabilities.schema import DivergenceKind
from mountainash.core.capabilities.schema import EntrypointStage
from mountainash.core.capabilities.schema import EntrypointStageTarget
from mountainash.core.capabilities.schema import OperationTarget
from mountainash.core.capabilities.schema import Scenario
from mountainash.core.capabilities.schema import TargetSurface
from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_MOUNTAINASH_REL

SEGMENT = CapabilitySegment(
    domain=Domain.RELATION,
    capabilities=(),
    manifestations=(
        DivergenceManifestation(
            key=ManifestationKey(
                target=EntrypointStageTarget(
                    surface=TargetSurface.RELATION,
                    entrypoint=CallableRef(
                        module="mountainash.relations.core.relation_api.relation", qualname="Relation.to_pandas"
                    ),
                    stage=EntrypointStage.MATERIALIZATION,
                ),
                scenario=Scenario(
                    arguments=(),
                    options=(),
                    input_schema=(
                        (
                            "payload",
                            CaptureValue(tag="text", value="opaque Python object; no native list schema evidence"),
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
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="1"),
                                                        CaptureValue(tag="integer", value="2"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence", value=(CaptureValue(tag="integer", value="3"),)
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
                            "egress_terminal",
                            CaptureValue(tag="text", value="to_pandas"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                        (
                            "upstream_conform",
                            CaptureValue(
                                tag="mapping",
                                value=(
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
                                                                        CaptureValue(tag="text", value="payload"),
                                                                    ),
                                                                    (
                                                                        "type",
                                                                        CaptureValue(tag="text", value="ARRAY"),
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
                            tag="sequence", value=(CaptureValue(tag="text", value="result payload values [[1,2],[3]]"),)
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
                            value="Polars Object dtype has no defined Arrow representation; Narwhals' to_arrow() serializes raw object pointers instead of the underlying value",
                        ),
                    ),
                ),
            ),
            impact="an opaque-carrier structured field (no schema evidence, already-native Python container) fails to decode through logical egress when the source is a Narwhals-wrapped Polars frame",
            since="2026-08-28",
            workaround="Use a bare Polars relation (not Narwhals-wrapped) or a pandas/narwhals-pandas source for an opaque structured field; a JSON-text or schema-proven native LIST/STRUCT carrier is unaffected",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=EntrypointStageTarget(
                    surface=TargetSurface.RELATION,
                    entrypoint=CallableRef(
                        module="mountainash.relations.core.relation_api.relation", qualname="Relation.to_polars"
                    ),
                    stage=EntrypointStage.MATERIALIZATION,
                ),
                scenario=Scenario(
                    arguments=(),
                    options=(),
                    input_schema=(
                        (
                            "payload",
                            CaptureValue(tag="text", value="opaque Python object; no native list schema evidence"),
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
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="1"),
                                                        CaptureValue(tag="integer", value="2"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence", value=(CaptureValue(tag="integer", value="3"),)
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
                            "egress_terminal",
                            CaptureValue(tag="text", value="to_polars"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                        (
                            "upstream_conform",
                            CaptureValue(
                                tag="mapping",
                                value=(
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
                                                                        CaptureValue(tag="text", value="payload"),
                                                                    ),
                                                                    (
                                                                        "type",
                                                                        CaptureValue(tag="text", value="ARRAY"),
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
                                CaptureValue(tag="text", value="result payload dtype Object and values [[1,2],[3]]"),
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
                            value="Polars Object dtype has no defined Arrow representation; Narwhals' to_arrow() serializes raw object pointers instead of the underlying value",
                        ),
                    ),
                ),
            ),
            impact="an opaque-carrier structured field (no schema evidence, already-native Python container) fails to decode through logical egress when the source is a Narwhals-wrapped Polars frame",
            since="2026-08-28",
            workaround="Use a bare Polars relation (not Narwhals-wrapped) or a pandas/narwhals-pandas source for an opaque structured field; a JSON-text or schema-proven native LIST/STRUCT carrier is unaffected",
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
                            CaptureValue(tag="integer", value="2"),
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
                                                            CaptureValue(tag="integer", value="10"),
                                                            CaptureValue(tag="integer", value="20"),
                                                            CaptureValue(tag="integer", value="30"),
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
                                                            CaptureValue(tag="integer", value="50"),
                                                            CaptureValue(tag="integer", value="270"),
                                                        ),
                                                    ),
                                                ),
                                                (
                                                    "t",
                                                    CaptureValue(
                                                        tag="sequence",
                                                        value=(
                                                            CaptureValue(tag="integer", value="5"),
                                                            CaptureValue(tag="integer", value="27"),
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
                            value="narwhals join_asof(tolerance=...) is GATE-UNSUPPORTED family-wide (capabilities/narwhals.py); a raw pandas.DataFrame is routed through the same narwhals identity at runtime",
                        ),
                    ),
                ),
            ),
            impact="Relation.join_asof(tolerance=...) raises BackendCapabilityError on all narwhals-family dialects, including the 'pandas' test backend",
            since="2026-08-18",
            workaround="Drop tolerance= or use the polars/ibis backends",
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
                            value="narwhals join_asof(tolerance=...) is GATE-UNSUPPORTED family-wide (capabilities/narwhals.py); a raw pandas.DataFrame is routed through the same narwhals identity at runtime",
                        ),
                    ),
                ),
            ),
            impact="Relation.join_asof(tolerance=...) raises BackendCapabilityError on all narwhals-family dialects, including the 'pandas' test backend",
            since="2026-08-18",
            workaround="Drop tolerance= or use the polars/ibis backends",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=RKEY_MOUNTAINASH_REL.UNNEST),
                scenario=Scenario(
                    arguments=(
                        (
                            "columns",
                            CaptureValue(tag="sequence", value=(CaptureValue(tag="text", value="info"),)),
                        ),
                        (
                            "separator",
                            CaptureValue(tag="text", value=""),
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
                                        "info",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="mapping",
                                                    value=(
                                                        (
                                                            "x",
                                                            CaptureValue(tag="integer", value="10"),
                                                        ),
                                                        (
                                                            "y",
                                                            CaptureValue(tag="text", value="a"),
                                                        ),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="mapping",
                                                    value=(
                                                        (
                                                            "x",
                                                            CaptureValue(tag="integer", value="20"),
                                                        ),
                                                        (
                                                            "y",
                                                            CaptureValue(tag="text", value="b"),
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
                                    value="result_sorted == [{'id': 1, 'x': 10, 'y': 'a'}, {'id': 2, 'x': 20, 'y': 'b'}]",
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
                        CaptureValue(tag="text", value="Narwhals does not support unnest of a struct column"),
                    ),
                ),
            ),
            impact="Relation.unnest() raises on narwhals backends; polars and ibis compute it",
            since="2026-08-06",
            workaround="Use a polars or ibis backend for unnest",
            issue=None,
        ),
    ),
    changes=(),
)
