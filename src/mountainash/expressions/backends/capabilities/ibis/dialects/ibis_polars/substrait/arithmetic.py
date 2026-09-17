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
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

SEGMENT = CapabilitySegment(
    domain=Domain.ARITHMETIC,
    capabilities=(),
    manifestations=(
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOSH),
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
                                        "val",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="float", value="0x1.0000000000000p+0"),
                                                CaptureValue(tag="float", value="0x1.0000000000000p+1"),
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
                            CaptureValue(tag="text", value="collect expression"),
                        ),
                    ),
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
                                CaptureValue(tag="float", value="0x0.0p+0"),
                                CaptureValue(tag="text", value="math.acosh(2.0)"),
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
                        CaptureValue(tag="text", value="historical unsupported native function"),
                    ),
                ),
            ),
            impact="hyperbolic functions raise on ibis-polars and ibis-duckdb",
            since="2026-08-06",
            workaround="Use a polars backend for hyperbolic functions",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASINH),
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
                                        "val",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="float", value="0x0.0p+0"),
                                                CaptureValue(tag="float", value="0x1.0000000000000p+0"),
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
                            CaptureValue(tag="text", value="collect expression"),
                        ),
                    ),
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
                                CaptureValue(tag="float", value="0x0.0p+0"),
                                CaptureValue(tag="text", value="math.asinh(1.0)"),
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
                        CaptureValue(tag="text", value="historical unsupported native function"),
                    ),
                ),
            ),
            impact="hyperbolic functions raise on ibis-polars and ibis-duckdb",
            since="2026-08-06",
            workaround="Use a polars backend for hyperbolic functions",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATANH),
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
                                        "val",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="float", value="0x0.0p+0"),
                                                CaptureValue(tag="float", value="0x1.0000000000000p-1"),
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
                            CaptureValue(tag="text", value="collect expression"),
                        ),
                    ),
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
                                CaptureValue(tag="float", value="0x0.0p+0"),
                                CaptureValue(tag="text", value="math.atanh(0.5)"),
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
                        CaptureValue(tag="text", value="historical unsupported native function"),
                    ),
                ),
            ),
            impact="hyperbolic functions raise on ibis-polars and ibis-duckdb",
            since="2026-08-06",
            workaround="Use a polars backend for hyperbolic functions",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COSH),
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
                                        "val",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="float", value="0x0.0p+0"),
                                                CaptureValue(tag="float", value="0x1.0000000000000p+0"),
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
                            CaptureValue(tag="text", value="collect expression"),
                        ),
                    ),
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
                                CaptureValue(tag="float", value="0x1.0000000000000p+0"),
                                CaptureValue(tag="text", value="math.cosh(1.0)"),
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
                        CaptureValue(tag="text", value="historical unsupported native function"),
                    ),
                ),
            ),
            impact="hyperbolic functions raise on ibis-polars and ibis-duckdb",
            since="2026-08-06",
            workaround="Use a polars backend for hyperbolic functions",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SINH),
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
                                        "val",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="float", value="0x0.0p+0"),
                                                CaptureValue(tag="float", value="0x1.0000000000000p+0"),
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
                            CaptureValue(tag="text", value="collect expression"),
                        ),
                    ),
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
                                CaptureValue(tag="float", value="0x0.0p+0"),
                                CaptureValue(tag="text", value="math.sinh(1.0)"),
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
                        CaptureValue(tag="text", value="historical unsupported native function"),
                    ),
                ),
            ),
            impact="hyperbolic functions raise on ibis-polars and ibis-duckdb",
            since="2026-08-06",
            workaround="Use a polars backend for hyperbolic functions",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TANH),
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
                                        "val",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="float", value="0x0.0p+0"),
                                                CaptureValue(tag="float", value="0x1.0000000000000p+0"),
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
                            CaptureValue(tag="text", value="collect expression"),
                        ),
                    ),
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
                                CaptureValue(tag="float", value="0x0.0p+0"),
                                CaptureValue(tag="text", value="math.tanh(1.0)"),
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
                        CaptureValue(tag="text", value="historical unsupported native function"),
                    ),
                ),
            ),
            impact="hyperbolic functions raise on ibis-polars and ibis-duckdb",
            since="2026-08-06",
            workaround="Use a polars backend for hyperbolic functions",
            issue=None,
        ),
    ),
    changes=(),
)
