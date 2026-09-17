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
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_NULL

SEGMENT = CapabilitySegment(
    domain=Domain.NULL,
    capabilities=(),
    manifestations=(
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=FKEY_MOUNTAINASH_NULL.FILL_NAN),
                scenario=Scenario(
                    arguments=(
                        (
                            "input",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "field",
                                        CaptureValue(tag="text", value="val"),
                                    ),
                                ),
                            ),
                        ),
                        (
                            "replacement",
                            CaptureValue(tag="float", value="0x0.0p+0"),
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
                {"claim_status": "retained_public_oracle", "outcome": [1.0, 0.0, None], "observation_layer": "public"}
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
    ),
    changes=(),
)
