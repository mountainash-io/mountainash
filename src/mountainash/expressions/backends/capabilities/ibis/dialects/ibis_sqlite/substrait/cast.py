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
                            tag="mapping",
                            value=(
                                (
                                    "raises",
                                    CaptureValue(tag="text", value="Exception"),
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
                        CaptureValue(tag="text", value="SQLite CAST is lenient and parses CAST('1x' AS INTEGER) as 1."),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="Strict casts do not raise for malformed input on ibis-sqlite.",
            since="2026-07-05",
            workaround="Validate malformed input via conform/typespec or use another Ibis backend",
            issue="IB-CAST-03",
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
                        CaptureValue(tag="text", value="ibis-sqlite has no SQL compilation rule for TryCast."),
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
                                    "THROW",
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
                            tag="mapping",
                            value=(
                                (
                                    "raises",
                                    CaptureValue(tag="text", value="Exception"),
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
                        CaptureValue(tag="text", value="SQLite CAST is lenient and parses CAST('1x' AS INTEGER) as 1."),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="Strict casts do not raise for malformed input on ibis-sqlite.",
            since="2026-07-05",
            workaround="Validate malformed input via conform/typespec or use another Ibis backend",
            issue="IB-CAST-03",
        ),
    ),
    changes=(),
)
