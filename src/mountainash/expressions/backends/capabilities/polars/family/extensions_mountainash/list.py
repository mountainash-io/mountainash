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
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_LIST

SEGMENT = CapabilitySegment(
    domain=Domain.LIST,
    capabilities=(),
    manifestations=(
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_SCALAR_LIST.EXPLODE),
                scenario=Scenario(
                    arguments=(
                        (
                            "x",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="arr"),
                                    ),
                                ),
                            ),
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
                                        "arr",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="10"),
                                                        CaptureValue(tag="integer", value="20"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence", value=(CaptureValue(tag="integer", value="30"),)
                                                ),
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="40"),
                                                        CaptureValue(tag="integer", value="50"),
                                                        CaptureValue(tag="integer", value="60"),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                    (
                                        "id",
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
                            CaptureValue(tag="text", value="relation_select_to_dict"),
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
                                    "id",
                                    CaptureValue(
                                        tag="sequence",
                                        value=(
                                            CaptureValue(tag="integer", value="1"),
                                            CaptureValue(tag="integer", value="1"),
                                            CaptureValue(tag="integer", value="2"),
                                            CaptureValue(tag="integer", value="3"),
                                            CaptureValue(tag="integer", value="3"),
                                            CaptureValue(tag="integer", value="3"),
                                        ),
                                    ),
                                ),
                                (
                                    "val",
                                    CaptureValue(
                                        tag="sequence",
                                        value=(
                                            CaptureValue(tag="integer", value="10"),
                                            CaptureValue(tag="integer", value="20"),
                                            CaptureValue(tag="integer", value="30"),
                                            CaptureValue(tag="integer", value="40"),
                                            CaptureValue(tag="integer", value="50"),
                                            CaptureValue(tag="integer", value="60"),
                                        ),
                                    ),
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
                            tag="text",
                            value="Polars expression-level explode changes row count beside an un-exploded sibling.",
                        ),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="historical-declaration"),
                    ),
                ),
            ),
            impact="The multi-column projection raises ShapeError on eager and lazy Polars.",
            since="2026-08-06",
            workaround="Explode without a mismatched sibling column, or use an Ibis backend",
            issue=None,
        ),
    ),
    changes=(),
)
