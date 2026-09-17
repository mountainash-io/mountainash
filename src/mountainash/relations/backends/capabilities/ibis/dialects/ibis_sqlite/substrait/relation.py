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
from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_SUBSTRAIT_REL

SEGMENT = CapabilitySegment(
    domain=Domain.RELATION,
    capabilities=(),
    manifestations=(
        DivergenceManifestation(
            key=ManifestationKey(
                target=OperationTarget(operation=RKEY_SUBSTRAIT_REL.JOIN),
                scenario=Scenario(
                    arguments=(
                        (
                            "join_type",
                            CaptureValue(
                                tag="enum",
                                value=(
                                    "mountainash.core.constants",
                                    "JoinType",
                                    "CROSS",
                                ),
                            ),
                        ),
                        (
                            "left_on",
                            CaptureValue(tag="null", value=""),
                        ),
                        (
                            "on",
                            CaptureValue(tag="null", value=""),
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
                            "right_on",
                            CaptureValue(tag="null", value=""),
                        ),
                        (
                            "suffix",
                            CaptureValue(tag="text", value="_right"),
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
                                                    "b",
                                                    CaptureValue(
                                                        tag="sequence",
                                                        value=(
                                                            CaptureValue(tag="integer", value="4"),
                                                            CaptureValue(tag="integer", value="5"),
                                                            CaptureValue(tag="integer", value="6"),
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
                                                    "c",
                                                    CaptureValue(
                                                        tag="sequence",
                                                        value=(
                                                            CaptureValue(tag="integer", value="10"),
                                                            CaptureValue(tag="integer", value="20"),
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
                            "public_call",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "kwargs",
                                        CaptureValue(
                                            tag="mapping",
                                            value=(
                                                (
                                                    "how",
                                                    CaptureValue(tag="text", value="cross"),
                                                ),
                                            ),
                                        ),
                                    ),
                                    (
                                        "method",
                                        CaptureValue(tag="text", value="join"),
                                    ),
                                ),
                            ),
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
                        CaptureValue(tag="sequence", value=(CaptureValue(tag="text", value="cross == join_cross"),)),
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
                            value="cross_join between two same-named tables from different Ibis connections raises a column-binding error on ibis SQL backends (ibis-duckdb BinderException, ibis-sqlite OperationalError)",
                        ),
                    ),
                ),
            ),
            impact="Relation.cross_join() raises on ibis-duckdb/ibis-sqlite; polars/narwhals and ibis-polars compute it",
            since="2026-08-06",
            workaround="Use a polars/narwhals backend or ibis-polars for cross joins",
            issue="IB-REL-12",
        ),
    ),
    changes=(),
)
