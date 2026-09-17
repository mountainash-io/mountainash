"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import DivergenceManifestation
from mountainash.core.capabilities.declarations import ManifestationKey
from mountainash.core.capabilities.schema import CaptureValue
from mountainash.core.capabilities.schema import DivergenceKind
from mountainash.core.capabilities.schema import OperationTarget
from mountainash.core.capabilities.schema import Scenario

from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING
from mountainash.core.capabilities.declarations import CapabilityKey
from mountainash.core.capabilities.schema import CapabilityLevel


from mountainash.core.capabilities.declarations import CapabilityAssertion
from mountainash.core.capabilities.declarations import CapabilitySegment

SEGMENT = CapabilitySegment(
    domain=Domain.STRING,
    capabilities=(
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS, subject="substring"),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-05",
            message="fixed upstream on the polars-backed narwhals path",
            issue="NW-STR-01",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.REPLACE, subject="replacement"),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-05",
            message="fixed upstream on the polars-backed narwhals path",
            issue="NW-STR-03",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_REPLACE, subject="replacement"),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-05",
            message="fixed upstream on the polars-backed narwhals path",
            issue="NW-STR-05",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.STARTS_WITH, subject="substring"),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-05",
            message="fixed upstream on the polars-backed narwhals path",
            issue="NW-STR-01",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_SUBSTRAIT_SCALAR_STRING.ENDS_WITH, subject="substring"),
            level=CapabilityLevel.EXPR_CAPABLE,
            since="2026-07-05",
            message="fixed upstream on the polars-backed narwhals path",
            issue="NW-STR-01",
        ),
    ),
    manifestations=(
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_STRING.LTRIM),
                scenario=Scenario(
                    arguments=(
                        (
                            "input",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "column",
                                        CaptureValue(tag="text", value="s"),
                                    ),
                                    (
                                        "expression",
                                        CaptureValue(tag="text", value="field"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(
                        (
                            "columns",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "s",
                                        CaptureValue(
                                            tag="mapping",
                                            value=(
                                                (
                                                    "nullable",
                                                    CaptureValue(tag="bool", value="false"),
                                                ),
                                                (
                                                    "type",
                                                    CaptureValue(tag="text", value="text"),
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
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "s",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="  hello  "),
                                                CaptureValue(tag="text", value=" world"),
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
                            CaptureValue(
                                tag="enum",
                                value=(
                                    "mountainash.core.capabilities.schema",
                                    "EntrypointStage",
                                    "MATERIALIZATION",
                                ),
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
                        "claim_status",
                        CaptureValue(tag="text", value="historical_source_claim"),
                    ),
                    (
                        "declaration",
                        CaptureValue(tag="text", value="NW-STR-15"),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="leading-only alias trim is expected"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "claim_status",
                        CaptureValue(tag="text", value="historical_source_claim"),
                    ),
                    (
                        "declaration",
                        CaptureValue(tag="text", value="NW-STR-15"),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="directional trim strips both sides"),
                    ),
                ),
            ),
            impact="Directional trimming over-strips both ends.",
            since="2026-08-06",
            workaround="Use a polars or ibis backend for directional trimming.",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_STRING.LTRIM),
                scenario=Scenario(
                    arguments=(
                        (
                            "input",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "column",
                                        CaptureValue(tag="text", value="text"),
                                    ),
                                    (
                                        "expression",
                                        CaptureValue(tag="text", value="field"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(
                        (
                            "columns",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "text",
                                        CaptureValue(
                                            tag="mapping",
                                            value=(
                                                (
                                                    "nullable",
                                                    CaptureValue(tag="bool", value="false"),
                                                ),
                                                (
                                                    "type",
                                                    CaptureValue(tag="text", value="text"),
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
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "text",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="  hello  "),
                                                CaptureValue(tag="text", value="  world  "),
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
                            CaptureValue(
                                tag="enum",
                                value=(
                                    "mountainash.core.capabilities.schema",
                                    "EntrypointStage",
                                    "MATERIALIZATION",
                                ),
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
                        "claim_status",
                        CaptureValue(tag="text", value="historical_source_claim"),
                    ),
                    (
                        "declaration",
                        CaptureValue(tag="text", value="NW-STR-15"),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="leading-only trim is expected"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "claim_status",
                        CaptureValue(tag="text", value="historical_source_claim"),
                    ),
                    (
                        "declaration",
                        CaptureValue(tag="text", value="NW-STR-15"),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="directional trim strips both sides"),
                    ),
                ),
            ),
            impact="Directional trimming over-strips both ends.",
            since="2026-08-06",
            workaround="Use a polars or ibis backend for directional trimming.",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_STRING.RTRIM),
                scenario=Scenario(
                    arguments=(
                        (
                            "input",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "column",
                                        CaptureValue(tag="text", value="s"),
                                    ),
                                    (
                                        "expression",
                                        CaptureValue(tag="text", value="field"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(
                        (
                            "columns",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "s",
                                        CaptureValue(
                                            tag="mapping",
                                            value=(
                                                (
                                                    "nullable",
                                                    CaptureValue(tag="bool", value="false"),
                                                ),
                                                (
                                                    "type",
                                                    CaptureValue(tag="text", value="text"),
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
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "s",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="  hello  "),
                                                CaptureValue(tag="text", value="world "),
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
                            CaptureValue(
                                tag="enum",
                                value=(
                                    "mountainash.core.capabilities.schema",
                                    "EntrypointStage",
                                    "MATERIALIZATION",
                                ),
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
                        "claim_status",
                        CaptureValue(tag="text", value="historical_source_claim"),
                    ),
                    (
                        "declaration",
                        CaptureValue(tag="text", value="NW-STR-15"),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="trailing-only alias trim is expected"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "claim_status",
                        CaptureValue(tag="text", value="historical_source_claim"),
                    ),
                    (
                        "declaration",
                        CaptureValue(tag="text", value="NW-STR-15"),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="directional trim strips both sides"),
                    ),
                ),
            ),
            impact="Directional trimming over-strips both ends.",
            since="2026-08-06",
            workaround="Use a polars or ibis backend for directional trimming.",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_SUBSTRAIT_SCALAR_STRING.RTRIM),
                scenario=Scenario(
                    arguments=(
                        (
                            "input",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "column",
                                        CaptureValue(tag="text", value="text"),
                                    ),
                                    (
                                        "expression",
                                        CaptureValue(tag="text", value="field"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(
                        (
                            "columns",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "text",
                                        CaptureValue(
                                            tag="mapping",
                                            value=(
                                                (
                                                    "nullable",
                                                    CaptureValue(tag="bool", value="false"),
                                                ),
                                                (
                                                    "type",
                                                    CaptureValue(tag="text", value="text"),
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
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "text",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="  hello  "),
                                                CaptureValue(tag="text", value="  world  "),
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
                            CaptureValue(
                                tag="enum",
                                value=(
                                    "mountainash.core.capabilities.schema",
                                    "EntrypointStage",
                                    "MATERIALIZATION",
                                ),
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
                        "claim_status",
                        CaptureValue(tag="text", value="historical_source_claim"),
                    ),
                    (
                        "declaration",
                        CaptureValue(tag="text", value="NW-STR-15"),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="trailing-only trim is expected"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "claim_status",
                        CaptureValue(tag="text", value="historical_source_claim"),
                    ),
                    (
                        "declaration",
                        CaptureValue(tag="text", value="NW-STR-15"),
                    ),
                    (
                        "statement",
                        CaptureValue(tag="text", value="directional trim strips both sides"),
                    ),
                ),
            ),
            impact="Directional trimming over-strips both ends.",
            since="2026-08-06",
            workaround="Use a polars or ibis backend for directional trimming.",
            issue=None,
        ),
    ),
)
