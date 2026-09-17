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
                                                CaptureValue(tag="float", value="-0x1.e666666666666p+0"),
                                                CaptureValue(tag="float", value="-0x1.0cccccccccccdp+1"),
                                                CaptureValue(tag="float", value="-0x1.c000000000000p+1"),
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
            kind=DivergenceKind.PRECISION,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="integer", value="-1"),
                                CaptureValue(tag="integer", value="-2"),
                                CaptureValue(tag="integer", value="-3"),
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
                        CaptureValue(tag="text", value="DuckDB uses IEEE 754 half-to-even float-to-integer casting."),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="Tests expecting truncation-on-cast produce different results on ibis-duckdb.",
            since="2026-07-05",
            workaround="Explicit floor()/ceil() before cast, or use ibis-sqlite/polars",
            issue="IB-CAST-01",
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
                                                CaptureValue(tag="float", value="0x1.199999999999ap+0"),
                                                CaptureValue(tag="float", value="0x1.7333333333333p+1"),
                                                CaptureValue(tag="float", value="0x1.c000000000000p+1"),
                                                CaptureValue(tag="float", value="-0x1.b333333333333p+0"),
                                                CaptureValue(tag="float", value="-0x1.2666666666666p+1"),
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
            kind=DivergenceKind.PRECISION,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="integer", value="1"),
                                CaptureValue(tag="integer", value="2"),
                                CaptureValue(tag="integer", value="3"),
                                CaptureValue(tag="integer", value="-1"),
                                CaptureValue(tag="integer", value="-2"),
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
                        CaptureValue(tag="text", value="DuckDB uses IEEE 754 half-to-even float-to-integer casting."),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="Tests expecting truncation-on-cast produce different results on ibis-duckdb.",
            since="2026-07-05",
            workaround="Explicit floor()/ceil() before cast, or use ibis-sqlite/polars",
            issue="IB-CAST-01",
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
                                tag="mapping",
                                value=(
                                    (
                                        "python_type",
                                        CaptureValue(tag="text", value="builtins.int"),
                                    ),
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
                                                CaptureValue(tag="float", value="0x1.8000000000000p+0"),
                                                CaptureValue(tag="float", value="0x1.4000000000000p+1"),
                                                CaptureValue(tag="float", value="0x1.c000000000000p+1"),
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
            kind=DivergenceKind.PRECISION,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
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
                        CaptureValue(tag="text", value="DuckDB uses IEEE 754 half-to-even float-to-integer casting."),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="Tests expecting truncation-on-cast produce different results on ibis-duckdb.",
            since="2026-07-05",
            workaround="Explicit floor()/ceil() before cast, or use ibis-sqlite/polars",
            issue="IB-CAST-01",
        ),
    ),
    changes=(),
)
