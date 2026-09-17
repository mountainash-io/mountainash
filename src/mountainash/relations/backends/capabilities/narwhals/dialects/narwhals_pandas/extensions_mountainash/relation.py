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
                                                CaptureValue(tag="text", value="RowRule"),
                                            ),
                                            (
                                                "method",
                                                CaptureValue(tag="text", value="ge"),
                                            ),
                                            (
                                                "other",
                                                CaptureValue(tag="integer", value="0"),
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
                                                    CaptureValue(tag="text", value="integer"),
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
                                                CaptureValue(tag="integer", value="30"),
                                                CaptureValue(tag="integer", value="-1"),
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
                        "fail_count",
                        CaptureValue(tag="integer", value="1"),
                    ),
                    (
                        "failure_outcomes",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="text", value="fail"),
                                CaptureValue(tag="text", value="unknown"),
                            ),
                        ),
                    ),
                    (
                        "historical",
                        CaptureValue(tag="bool", value="true"),
                    ),
                    (
                        "pass_count",
                        CaptureValue(tag="integer", value="1"),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="failed"),
                    ),
                    (
                        "total_rows",
                        CaptureValue(tag="integer", value="3"),
                    ),
                    (
                        "unknown_count",
                        CaptureValue(tag="integer", value="1"),
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
                        "null_comparison",
                        CaptureValue(tag="text", value="collapsed-to-false"),
                    ),
                ),
            ),
            impact="validation outcome-model tests expecting an 'unknown' verdict from a null comparison diverge on pandas/narwhals-pandas",
            since="2026-08-06",
            workaround="Use a polars, narwhals-polars, or ibis backend for three-way null outcome semantics",
            issue=None,
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
                                                CaptureValue(tag="text", value="RowRule"),
                                            ),
                                            (
                                                "method",
                                                CaptureValue(tag="text", value="ge"),
                                            ),
                                            (
                                                "other",
                                                CaptureValue(tag="integer", value="0"),
                                            ),
                                        ),
                                    ),
                                    CaptureValue(
                                        tag="mapping",
                                        value=(
                                            (
                                                "booleanizer",
                                                CaptureValue(tag="text", value="t_maybe_true"),
                                            ),
                                            (
                                                "column",
                                                CaptureValue(tag="text", value="age"),
                                            ),
                                            (
                                                "kind",
                                                CaptureValue(tag="text", value="RowRule"),
                                            ),
                                            (
                                                "method",
                                                CaptureValue(tag="text", value="ge"),
                                            ),
                                            (
                                                "other",
                                                CaptureValue(tag="integer", value="0"),
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
                                                    CaptureValue(tag="text", value="integer"),
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
                                                CaptureValue(tag="integer", value="1"),
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
                        "default_status",
                        CaptureValue(tag="text", value="failed"),
                    ),
                    (
                        "historical",
                        CaptureValue(tag="bool", value="true"),
                    ),
                    (
                        "maybe_true_status",
                        CaptureValue(tag="text", value="passed"),
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
                        "null_comparison",
                        CaptureValue(tag="text", value="collapsed-to-false"),
                    ),
                ),
            ),
            impact="validation outcome-model tests expecting an 'unknown' verdict from a null comparison diverge on pandas/narwhals-pandas",
            since="2026-08-06",
            workaround="Use a polars, narwhals-polars, or ibis backend for three-way null outcome semantics",
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
                            value=(
                                CaptureValue(tag="text", value="id == [1,3,4] and n == [1.0,None,3.0]"),
                                CaptureValue(tag="text", value="id == [1,3,4] and n == [1.0,None,3.0]"),
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
                            value=(
                                CaptureValue(tag="text", value="result pid == [1,2] and columns == ['pid']"),
                                CaptureValue(tag="text", value="result pid == [1,2] and columns == ['pid']"),
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
                            tag="sequence",
                            value=(
                                CaptureValue(tag="text", value="result['pid'].to_list() == [1, 2]"),
                                CaptureValue(tag="text", value="result['pid'].to_list() == [1, 2]"),
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
                                                            CaptureValue(tag="null", value=""),
                                                            CaptureValue(tag="integer", value="3"),
                                                        ),
                                                    ),
                                                ),
                                                (
                                                    "val",
                                                    CaptureValue(
                                                        tag="sequence",
                                                        value=(
                                                            CaptureValue(tag="text", value="n"),
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
                                                            CaptureValue(tag="integer", value="99"),
                                                            CaptureValue(tag="integer", value="20"),
                                                        ),
                                                    ),
                                                ),
                                                (
                                                    "t",
                                                    CaptureValue(
                                                        tag="sequence",
                                                        value=(
                                                            CaptureValue(tag="null", value=""),
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
                                    tag="text", value="sorted_dicts(result, val) == sorted_dicts(Polars oracle, val)"
                                ),
                                CaptureValue(
                                    tag="text", value="sorted_dicts(result, val) == sorted_dicts(Polars oracle, val)"
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
                            value="pandas merge_asof raises ValueError on null as-of keys (left or right side); narwhals-polars/narwhals-lazy compute no-match rows like Polars",
                        ),
                    ),
                ),
            ),
            impact="Relation.join_asof() with null keys raises on narwhals-pandas and the 'pandas' test backend; polars/narwhals-polars/narwhals-lazy/ibis compute no-match rows",
            since="2026-08-18",
            workaround="Use a polars, narwhals-polars, narwhals-lazy, or ibis backend for asof joins over null keys",
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
                            tag="sequence",
                            value=(
                                CaptureValue(tag="text", value="result == Polars join_asof oracle"),
                                CaptureValue(tag="text", value="result == Polars join_asof oracle"),
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
                            tag="sequence",
                            value=(
                                CaptureValue(tag="text", value="result == Polars join_asof oracle"),
                                CaptureValue(tag="text", value="result == Polars join_asof oracle"),
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
                            tag="sequence",
                            value=(
                                CaptureValue(tag="text", value="result == Polars oracle (last duplicate score 52)"),
                                CaptureValue(tag="text", value="result == Polars oracle (last duplicate score 52)"),
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
                            value="narwhals-pandas nearest may pick a different duplicate right row than Polars on a duplicate-right-key tie (Polars keeps the last of a tied group; the portable forward-wins fix inherits pandas merge_asof's own first-of-duplicates convention within each of its two internal legs) — the genuine cross-side tie (forward candidate vs a DIFFERENT-valued backward candidate) is unaffected and matches Polars",
                        ),
                    ),
                ),
            ),
            impact="Relation.join_asof(strategy='nearest') on narwhals-pandas/'pandas' may select a different (but still equally-near) right row than Polars when the right frame has duplicate keys at the winning distance",
            since="2026-08-19",
            workaround="Use polars, narwhals-polars, narwhals-lazy, or an ibis backend for exact duplicate-tie parity under nearest",
            issue=None,
        ),
    ),
    changes=(),
)
