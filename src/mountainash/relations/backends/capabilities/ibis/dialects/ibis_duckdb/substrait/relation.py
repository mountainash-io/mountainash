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
                target=OperationTarget(operation=RKEY_SUBSTRAIT_REL.FILTER),
                scenario=Scenario(
                    arguments=(
                        (
                            "predicate",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "operands",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="mapping",
                                                    value=(
                                                        (
                                                            "operands",
                                                            CaptureValue(
                                                                tag="sequence",
                                                                value=(
                                                                    CaptureValue(
                                                                        tag="mapping",
                                                                        value=(
                                                                            (
                                                                                "left",
                                                                                CaptureValue(
                                                                                    tag="mapping",
                                                                                    value=(
                                                                                        (
                                                                                            "field",
                                                                                            CaptureValue(
                                                                                                tag="text", value="age"
                                                                                            ),
                                                                                        ),
                                                                                    ),
                                                                                ),
                                                                            ),
                                                                            (
                                                                                "operator",
                                                                                CaptureValue(tag="text", value="gte"),
                                                                            ),
                                                                            (
                                                                                "right",
                                                                                CaptureValue(
                                                                                    tag="mapping",
                                                                                    value=(
                                                                                        (
                                                                                            "literal",
                                                                                            CaptureValue(
                                                                                                tag="integer",
                                                                                                value="18",
                                                                                            ),
                                                                                        ),
                                                                                    ),
                                                                                ),
                                                                            ),
                                                                        ),
                                                                    ),
                                                                    CaptureValue(
                                                                        tag="mapping",
                                                                        value=(
                                                                            (
                                                                                "left",
                                                                                CaptureValue(
                                                                                    tag="mapping",
                                                                                    value=(
                                                                                        (
                                                                                            "field",
                                                                                            CaptureValue(
                                                                                                tag="text",
                                                                                                value="score",
                                                                                            ),
                                                                                        ),
                                                                                    ),
                                                                                ),
                                                                            ),
                                                                            (
                                                                                "operator",
                                                                                CaptureValue(tag="text", value="gte"),
                                                                            ),
                                                                            (
                                                                                "right",
                                                                                CaptureValue(
                                                                                    tag="mapping",
                                                                                    value=(
                                                                                        (
                                                                                            "literal",
                                                                                            CaptureValue(
                                                                                                tag="integer",
                                                                                                value="80",
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
                                                        (
                                                            "operator",
                                                            CaptureValue(tag="text", value="and"),
                                                        ),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="mapping",
                                                    value=(
                                                        (
                                                            "operands",
                                                            CaptureValue(
                                                                tag="sequence",
                                                                value=(
                                                                    CaptureValue(
                                                                        tag="mapping",
                                                                        value=(
                                                                            (
                                                                                "left",
                                                                                CaptureValue(
                                                                                    tag="mapping",
                                                                                    value=(
                                                                                        (
                                                                                            "field",
                                                                                            CaptureValue(
                                                                                                tag="text",
                                                                                                value="premium",
                                                                                            ),
                                                                                        ),
                                                                                    ),
                                                                                ),
                                                                            ),
                                                                            (
                                                                                "operator",
                                                                                CaptureValue(tag="text", value="eq"),
                                                                            ),
                                                                            (
                                                                                "right",
                                                                                CaptureValue(
                                                                                    tag="mapping",
                                                                                    value=(
                                                                                        (
                                                                                            "literal",
                                                                                            CaptureValue(
                                                                                                tag="bool", value="true"
                                                                                            ),
                                                                                        ),
                                                                                    ),
                                                                                ),
                                                                            ),
                                                                        ),
                                                                    ),
                                                                    CaptureValue(
                                                                        tag="mapping",
                                                                        value=(
                                                                            (
                                                                                "left",
                                                                                CaptureValue(
                                                                                    tag="mapping",
                                                                                    value=(
                                                                                        (
                                                                                            "field",
                                                                                            CaptureValue(
                                                                                                tag="text",
                                                                                                value="score",
                                                                                            ),
                                                                                        ),
                                                                                    ),
                                                                                ),
                                                                            ),
                                                                            (
                                                                                "operator",
                                                                                CaptureValue(tag="text", value="gte"),
                                                                            ),
                                                                            (
                                                                                "right",
                                                                                CaptureValue(
                                                                                    tag="mapping",
                                                                                    value=(
                                                                                        (
                                                                                            "literal",
                                                                                            CaptureValue(
                                                                                                tag="integer",
                                                                                                value="85",
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
                                                        (
                                                            "operator",
                                                            CaptureValue(tag="text", value="and"),
                                                        ),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                    (
                                        "operator",
                                        CaptureValue(tag="text", value="or"),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(),
                    input_schema=(
                        (
                            "age",
                            CaptureValue(tag="text", value="integer"),
                        ),
                        (
                            "premium",
                            CaptureValue(tag="text", value="boolean"),
                        ),
                        (
                            "score",
                            CaptureValue(tag="text", value="integer"),
                        ),
                    ),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "age",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="17"),
                                                CaptureValue(tag="integer", value="25"),
                                                CaptureValue(tag="integer", value="35"),
                                                CaptureValue(tag="integer", value="30"),
                                                CaptureValue(tag="integer", value="22"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "applicant",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="text", value="Alice"),
                                                CaptureValue(tag="text", value="Bob"),
                                                CaptureValue(tag="text", value="Charlie"),
                                                CaptureValue(tag="text", value="David"),
                                                CaptureValue(tag="text", value="Eve"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "premium",
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
                                        "score",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="95"),
                                                CaptureValue(tag="integer", value="70"),
                                                CaptureValue(tag="integer", value="85"),
                                                CaptureValue(tag="integer", value="90"),
                                                CaptureValue(tag="integer", value="88"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "order_sensitive_oracle",
                            CaptureValue(tag="bool", value="true"),
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
                                        CaptureValue(tag="text", value="to_dict"),
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
                        CaptureValue(
                            tag="sequence",
                            value=(CaptureValue(tag="text", value="actual == ['Alice', 'Charlie', 'David', 'Eve']"),),
                        ),
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
                            value="DuckDB does not guarantee physical row order for a filtered scan; some OR-of-AND boolean predicates compile to a query plan that reorders matching rows relative to the left input, even though polars/narwhals/ibis-polars/ibis-sqlite all preserve input row order through filter",
                        ),
                    ),
                ),
            ),
            impact="Relation.filter() with certain compound boolean predicates may return rows in a different order than the input on ibis-duckdb; matched VALUES are always correct, only row position differs",
            since="2026-09-03",
            workaround="Use polars, narwhals, ibis-polars, or ibis-sqlite if exact input row order must be preserved through filter, or add an explicit .sort() after filter",
            issue=None,
        ),
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
