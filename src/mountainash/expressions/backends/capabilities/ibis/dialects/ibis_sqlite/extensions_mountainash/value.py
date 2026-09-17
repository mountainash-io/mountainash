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
            expected=CaptureValue.of(
                {
                    "claim_status": "retained_public_oracle",
                    "outcome": [True, False, None],
                    "observation_layer": "public",
                }
            ),
            observed=CaptureValue.of(
                {
                    "claim_status": "retained_native_observation",
                    "outcome": {
                        "status": "error",
                        "class": "ibis.common.exceptions.OperationNotDefinedError",
                        "message": "Compilation rule for 'IsNan' operation is not defined",
                    },
                    "observation_layer": "native",
                }
            ),
            impact="is_nan/fill_nan/NaN comparisons diverge on SQL engines.",
            since="2026-07-05",
            workaround="Use is_null/fill_null on SQL backends",
            issue="IB-TYPE-02",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=CompositionTarget(
                    surface=TargetSurface.EXPRESSION,
                    entrypoint=CallableRef(
                        module="mountainash.expressions.core.utils.temporal",
                        qualname="between_last",
                    ),
                    operations=(
                        FKEY_SUBSTRAIT_SCALAR_COMPARISON.GT,
                        FKEY_SUBSTRAIT_SCALAR_COMPARISON.LT,
                        FKEY_SUBSTRAIT_SCALAR_BOOLEAN.AND,
                    ),
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
                                        "event",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="A"),
                                                CaptureValue(tag="text", value="B"),
                                                CaptureValue(tag="text", value="C"),
                                                CaptureValue(tag="text", value="D"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "timestamp",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="now-1h"),
                                                CaptureValue(tag="text", value="now-3h"),
                                                CaptureValue(tag="text", value="now-6h"),
                                                CaptureValue(tag="text", value="now-12h"),
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
                            CaptureValue(tag="text", value="dynamic clock older=8 hours newer=2 hours"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.SEMANTICS,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="text", value="B"),
                                CaptureValue(tag="text", value="C"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_unknown",
                        CaptureValue(tag="text", value="no fresh native observation"),
                    ),
                ),
            ),
            impact="sub-day temporal arithmetic/comparison on ibis-sqlite silently diverges",
            since="2026-08-06",
            workaround="Use polars/narwhals or ibis-duckdb for sub-day datetime arithmetic",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=CompositionTarget(
                    surface=TargetSurface.EXPRESSION,
                    entrypoint=CallableRef(
                        module="mountainash.expressions.core.utils.temporal",
                        qualname="older_than",
                    ),
                    operations=(FKEY_SUBSTRAIT_SCALAR_COMPARISON.LT,),
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
                                        "message",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="Database connection failed"),
                                                CaptureValue(tag="text", value="Request processed"),
                                                CaptureValue(tag="text", value="Timeout error"),
                                                CaptureValue(tag="text", value="Slow query detected"),
                                                CaptureValue(tag="text", value="Startup complete"),
                                                CaptureValue(tag="text", value="Old error"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "timestamp",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="2026-09-15T12:29"),
                                                CaptureValue(tag="text", value="2026-09-15T12:27"),
                                                CaptureValue(tag="text", value="2026-09-15T12:25"),
                                                CaptureValue(tag="text", value="2026-09-15T12:20"),
                                                CaptureValue(tag="text", value="2026-09-15T12:00"),
                                                CaptureValue(tag="text", value="2026-09-15T10:30"),
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
                            CaptureValue(tag="text", value="fixed clock 2026-09-15T12:30, duration=1 hour"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.SEMANTICS,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="sequence", value=(CaptureValue(tag="text", value="Old error"),)),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(tag="text", value="historical sqlite returned no old log"),
                    ),
                ),
            ),
            impact="sub-day temporal arithmetic/comparison on ibis-sqlite silently diverges",
            since="2026-08-06",
            workaround="Use polars/narwhals or ibis-duckdb for sub-day datetime arithmetic",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=CompositionTarget(
                    surface=TargetSurface.EXPRESSION,
                    entrypoint=CallableRef(
                        module="mountainash.expressions.core.utils.temporal",
                        qualname="within_last",
                    ),
                    operations=(FKEY_SUBSTRAIT_SCALAR_COMPARISON.GT,),
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
                                        "level",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="ERROR"),
                                                CaptureValue(tag="text", value="INFO"),
                                                CaptureValue(tag="text", value="ERROR"),
                                                CaptureValue(tag="text", value="WARN"),
                                                CaptureValue(tag="text", value="INFO"),
                                                CaptureValue(tag="text", value="ERROR"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "message",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="Database connection failed"),
                                                CaptureValue(tag="text", value="Request processed"),
                                                CaptureValue(tag="text", value="Timeout error"),
                                                CaptureValue(tag="text", value="Slow query detected"),
                                                CaptureValue(tag="text", value="Startup complete"),
                                                CaptureValue(tag="text", value="Old error"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "timestamp",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="2026-09-15T12:29"),
                                                CaptureValue(tag="text", value="2026-09-15T12:27"),
                                                CaptureValue(tag="text", value="2026-09-15T12:25"),
                                                CaptureValue(tag="text", value="2026-09-15T12:20"),
                                                CaptureValue(tag="text", value="2026-09-15T12:00"),
                                                CaptureValue(tag="text", value="2026-09-15T10:30"),
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
                            CaptureValue(
                                tag="text", value="fixed clock 2026-09-15T12:30, error filter, duration=15 minutes"
                            ),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.SEMANTICS,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="text", value="Database connection failed"),
                                CaptureValue(tag="text", value="Timeout error"),
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
                        CaptureValue(tag="text", value="historical sqlite returned an extra Old error"),
                    ),
                ),
            ),
            impact="sub-day temporal arithmetic/comparison on ibis-sqlite silently diverges",
            since="2026-08-06",
            workaround="Use polars/narwhals or ibis-duckdb for sub-day datetime arithmetic",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=CompositionTarget(
                    surface=TargetSurface.EXPRESSION,
                    entrypoint=CallableRef(
                        module="mountainash.expressions.core.utils.temporal",
                        qualname="within_last",
                    ),
                    operations=(FKEY_SUBSTRAIT_SCALAR_COMPARISON.GT,),
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
                                        "message",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="A"),
                                                CaptureValue(tag="text", value="B"),
                                                CaptureValue(tag="text", value="C"),
                                                CaptureValue(tag="text", value="D"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "timestamp",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="now-2m"),
                                                CaptureValue(tag="text", value="now-5m"),
                                                CaptureValue(tag="text", value="now-10m"),
                                                CaptureValue(tag="text", value="now-30m"),
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
                            CaptureValue(tag="text", value="dynamic clock duration=8 minutes"),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.SEMANTICS,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_source_claim",
                        CaptureValue(
                            tag="sequence",
                            value=(
                                CaptureValue(tag="text", value="A"),
                                CaptureValue(tag="text", value="B"),
                            ),
                        ),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "historical_unknown",
                        CaptureValue(tag="text", value="no fresh native observation"),
                    ),
                ),
            ),
            impact="sub-day temporal arithmetic/comparison on ibis-sqlite silently diverges",
            since="2026-08-06",
            workaround="Use polars/narwhals or ibis-duckdb for sub-day datetime arithmetic",
            issue=None,
        ),
    ),
    changes=(),
)
