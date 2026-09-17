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
from mountainash.core.capabilities.schema import Scenario
from mountainash.core.capabilities.schema import TargetSurface
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_BOOLEAN
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_COMPARISON

SEGMENT = CapabilitySegment(
    domain=Domain.VALUE,
    capabilities=(),
    manifestations=(
        DivergenceManifestation(
            key=ManifestationKey(
                target=CompositionTarget(
                    surface=TargetSurface.EXPRESSION,
                    entrypoint=CallableRef(
                        module="mountainash.expressions.core.expression_api.api_builders.extensions_mountainash.api_bldr_ext_ma_scalar_comparison",
                        qualname="MountainAshScalarComparisonAPIBuilder.is_not_nan",
                    ),
                    operations=(
                        FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_NAN,
                        FKEY_SUBSTRAIT_SCALAR_BOOLEAN.NOT,
                    ),
                ),
                scenario=Scenario(
                    arguments=(),
                    options=(),
                    input_schema=(),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "val",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="float", value="0x1.0000000000000p+0"),
                                                CaptureValue(tag="float", value="nan"),
                                                CaptureValue(tag="float", value="0x1.8000000000000p+1"),
                                                CaptureValue(tag="float", value="nan"),
                                                CaptureValue(tag="float", value="0x1.4000000000000p+2"),
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
            kind=DivergenceKind.SEMANTICS,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "outcome",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="bool", value="true"),
                                CaptureValue(tag="bool", value="false"),
                                CaptureValue(tag="bool", value="true"),
                                CaptureValue(tag="bool", value="false"),
                                CaptureValue(tag="bool", value="true"),
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
                            tag="text", value="SQL engines treat NaN as NULL; NaN == NaN yields NULL rather than False."
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="is_nan/fill_nan/NaN comparisons diverge on SQL engines.",
            since="2026-07-05",
            workaround="Use is_null/fill_null on SQL backends",
            issue="IB-TYPE-02",
        ),
    ),
    changes=(),
)
