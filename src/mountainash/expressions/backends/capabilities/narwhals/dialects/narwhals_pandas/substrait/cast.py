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
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_CAST

SEGMENT = CapabilitySegment(
    domain=Domain.CAST,
    capabilities=(),
    manifestations=(
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_CAST.CAST),
                scenario=Scenario(
                    arguments=(),
                    options=(),
                    input_schema=(
                        (
                            "relation_contract",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "fields",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="text", value="a"),
                                                        CaptureValue(tag="text", value="integer"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="text", value="b"),
                                                        CaptureValue(tag="text", value="boolean"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                    (
                                        "fields_match",
                                        CaptureValue(tag="text", value="open"),
                                    ),
                                    (
                                        "missing_columns",
                                        CaptureValue(tag="text", value="null_fill"),
                                    ),
                                ),
                            ),
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
                            "mode",
                            CaptureValue(tag="text", value="relation_conform_to_polars"),
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
                        "outcome",
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
                                    "b_all_null",
                                    CaptureValue(tag="bool", value="true"),
                                ),
                                (
                                    "b_dtype",
                                    CaptureValue(tag="text", value="Boolean"),
                                ),
                                (
                                    "b_exists",
                                    CaptureValue(tag="bool", value="true"),
                                ),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text", value="All-NULL casts to non-nullable numpy int64/bool raise or corrupt nulls."
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="Pandas-backed integer casts raise and boolean casts can map None to False.",
            since="2026-07-05",
            workaround="Use polars, narwhals-polars, narwhals-lazy, or an Ibis backend",
            issue="MA-TYPE-02",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_CAST.CAST),
                scenario=Scenario(
                    arguments=(),
                    options=(),
                    input_schema=(
                        (
                            "relation_contract",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "fields",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="text", value="a"),
                                                        CaptureValue(tag="text", value="integer"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="text", value="b"),
                                                        CaptureValue(tag="text", value="integer"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                    (
                                        "fields_match",
                                        CaptureValue(tag="text", value="open"),
                                    ),
                                    (
                                        "missing_columns",
                                        CaptureValue(tag="text", value="null_fill"),
                                    ),
                                ),
                            ),
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
                            "mode",
                            CaptureValue(tag="text", value="relation_conform_to_polars"),
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
                        "outcome",
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
                                    "b_all_null",
                                    CaptureValue(tag="bool", value="true"),
                                ),
                                (
                                    "b_dtype",
                                    CaptureValue(tag="text", value="Int64"),
                                ),
                                (
                                    "b_exists",
                                    CaptureValue(tag="bool", value="true"),
                                ),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="text", value="All-NULL casts to non-nullable numpy int64/bool raise or corrupt nulls."
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="Pandas-backed integer casts raise and boolean casts can map None to False.",
            since="2026-07-05",
            workaround="Use polars, narwhals-polars, narwhals-lazy, or an Ibis backend",
            issue="MA-TYPE-02",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_CAST.CAST),
                scenario=Scenario(
                    arguments=(
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="value"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(
                        (
                            "dtype",
                            CaptureValue(
                                tag="enum",
                                value=(
                                    "mountainash.core.dtypes.canonical",
                                    "MountainashDtype",
                                    "I64",
                                ),
                            ),
                        ),
                        (
                            "failure_behavior",
                            CaptureValue(
                                tag="enum",
                                value=(
                                    "mountainash.expressions.core.expression_protocols.api_builders.substrait.prtcl_api_bldr_cast",
                                    "CaseFailureBehaviour",
                                    "NULL",
                                ),
                            ),
                        ),
                    ),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "value",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="1"),
                                                CaptureValue(tag="text", value="1x"),
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
                            "mode",
                            CaptureValue(tag="text", value="collect_expr"),
                        ),
                        (
                            "stage",
                            CaptureValue(tag="text", value="materialization"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="integer", value="1"),
                                CaptureValue(tag="null", value=""),
                                CaptureValue(tag="integer", value="3"),
                            ),
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-source-assertion"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(tag="text", value="Narwhals has no try-cast failure-behavior parameter."),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="NULL-on-cast-failure cannot materialize on the marked provider.",
            since="2026-08-06",
            workaround="Use a polars or ibis-polars/ibis-duckdb backend for null-on-cast-failure semantics",
            issue=None,
        ),
    ),
    changes=(),
)
