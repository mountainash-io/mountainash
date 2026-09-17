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
from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_MOUNTAINASH_REL

SEGMENT = CapabilitySegment(
    domain=Domain.RELATION,
    capabilities=(),
    manifestations=(
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
                target=OperationTarget(operation=RKEY_MOUNTAINASH_REL.WITH_ROW_INDEX),
                scenario=Scenario(
                    arguments=(
                        (
                            "name",
                            CaptureValue(tag="text", value="idx"),
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
                                        "name",
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
                                        CaptureValue(tag="text", value="collect"),
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
                            tag="sequence", value=(CaptureValue(tag="text", value="idx_values == [0, 1, 2, 3]"),)
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
                            value="narwhals-lazy with_row_index() requires an explicit order_by= (row order over a LazyFrame is undefined); calling it without one raises TypeError",
                        ),
                    ),
                ),
            ),
            impact="Relation.with_row_index() raises on narwhals-lazy; eager narwhals/polars and ibis-duckdb/ibis-sqlite assign a 0..N-1 index",
            since="2026-08-06",
            workaround="Use an eager backend, or pass an explicit order before the lazy row index",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=RKEY_MOUNTAINASH_REL.WITH_ROW_INDEX),
                scenario=Scenario(
                    arguments=(
                        (
                            "name",
                            CaptureValue(tag="text", value="index"),
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
                                    value="result == [{'index': 0, 'a': 10}, {'index': 1, 'a': 20}, {'index': 2, 'a': 30}]",
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
                            value="narwhals-lazy with_row_index() requires an explicit order_by= (row order over a LazyFrame is undefined); calling it without one raises TypeError",
                        ),
                    ),
                ),
            ),
            impact="Relation.with_row_index() raises on narwhals-lazy; eager narwhals/polars and ibis-duckdb/ibis-sqlite assign a 0..N-1 index",
            since="2026-08-06",
            workaround="Use an eager backend, or pass an explicit order before the lazy row index",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=RKEY_MOUNTAINASH_REL.WITH_ROW_INDEX),
                scenario=Scenario(
                    arguments=(
                        (
                            "name",
                            CaptureValue(tag="text", value="row_num"),
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
                                    value="result == [{'row_num': 0, 'a': 10}, {'row_num': 1, 'a': 20}, {'row_num': 2, 'a': 30}]",
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
                            value="narwhals-lazy with_row_index() requires an explicit order_by= (row order over a LazyFrame is undefined); calling it without one raises TypeError",
                        ),
                    ),
                ),
            ),
            impact="Relation.with_row_index() raises on narwhals-lazy; eager narwhals/polars and ibis-duckdb/ibis-sqlite assign a 0..N-1 index",
            since="2026-08-06",
            workaround="Use an eager backend, or pass an explicit order before the lazy row index",
            issue=None,
        ),
    ),
    changes=(),
)
