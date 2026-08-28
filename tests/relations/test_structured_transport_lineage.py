"""Closed lineage rules for structured physical transport."""
from __future__ import annotations

from enum import Enum
from types import MappingProxyType, SimpleNamespace

import pytest

import mountainash as ma
from mountainash.conform.errors import UnsupportedStructuredTransportUse
from mountainash.conform.structured_transport import (
    StructuredCarrier,
    StructuredFieldPlan,
    StructuredRoot,
)
from mountainash.relations.core.relation_system.relation_keys.enums import (
    RKEY_MOUNTAINASH_REL as RM,
    RKEY_SUBSTRAIT_REL as RS,
)
from mountainash.relations.core.relation_system.relation_mapping.registry import (
    RelationOperationRegistry,
)
from mountainash.relations.core.structured_lineage import (
    TRANSPORT_LINEAGE_POLICIES,
    propagate_structured_plans,
)


def transport_plan(name: str = "payload") -> StructuredFieldPlan:
    return StructuredFieldPlan(
        field_name=name,
        root=StructuredRoot.ARRAY,
        carrier=StructuredCarrier.JSON_TEXT,
        configured_action="coerce",
        apply_value_transforms=True,
        missing_values=(),
        null_fill=None,
        declaration_fingerprint="schema",
        origin_node_id="conform",
    )


def node(operation_key, **attrs):
    return SimpleNamespace(operation_key=operation_key, **attrs)


def test_every_relation_operation_declares_transport_lineage():
    """The policy registry closes over the runtime operation registry."""
    assert set(RelationOperationRegistry.list_all()) == set(TRANSPORT_LINEAGE_POLICIES)


@pytest.mark.parametrize("operation", [RS.FETCH, RM.SAMPLE, RM.WITH_ROW_INDEX, RM.FETCH_FROM_END])
def test_preserving_operations_retain_transport_plans(operation):
    """Row-preserving operations do not consume a carried structured field."""
    plans = MappingProxyType({"payload": transport_plan()})

    result = propagate_structured_plans(node(operation), [plans], MappingProxyType({}))

    assert result == plans
    assert result is not plans


def test_direct_project_select_and_alias_preserve_transport_plan():
    """A direct field carriage preserves tags under its final output name."""
    plans = MappingProxyType({"payload": transport_plan()})

    selected = propagate_structured_plans(
        node(RS.PROJECT_SELECT, expressions=["payload"]), [plans], MappingProxyType({})
    )
    aliased = propagate_structured_plans(
        node(RS.PROJECT_SELECT, expressions=[ma.col("payload").alias("body")]),
        [plans],
        MappingProxyType({}),
    )

    assert set(selected) == {"payload"}
    assert set(aliased) == {"body"}
    assert aliased["body"].field_name == "body"


def test_project_drop_and_rename_update_transport_field_names():
    """Field-removing and field-renaming projections update plan keys exactly."""
    plans = MappingProxyType({"payload": transport_plan()})

    dropped = propagate_structured_plans(
        node(RS.PROJECT_DROP, expressions=["payload"]), [plans], MappingProxyType({})
    )
    renamed = propagate_structured_plans(
        node(RS.PROJECT_RENAME, rename_mapping={"payload": "body"}),
        [plans],
        MappingProxyType({}),
    )

    assert dropped == {}
    assert set(renamed) == {"body"}
    assert renamed["body"].field_name == "body"


def test_scalar_expression_reading_transported_field_is_rejected_before_compile():
    """A physical JSON carrier cannot enter an arbitrary scalar expression."""
    plans = MappingProxyType({"payload": transport_plan()})

    with pytest.raises(UnsupportedStructuredTransportUse, match="payload"):
        propagate_structured_plans(
            node(RS.PROJECT_SELECT, expressions=[ma.col("payload").str.length()]),
            [plans],
            MappingProxyType({}),
        )


def test_untagged_projection_expression_does_not_disrupt_transport_plans():
    """Expressions over ordinary fields are safe while a tag is carried elsewhere."""
    plans = MappingProxyType({"payload": transport_plan()})

    result = propagate_structured_plans(
        node(RS.PROJECT_WITH_COLUMNS, expressions=[ma.col("name").str.to_uppercase()]),
        [plans],
        MappingProxyType({}),
    )

    assert result == plans


def test_native_ibis_deferred_without_structured_plan_is_ignored():
    """A raw Ibis deferred must not recurse during lineage inspection."""
    import ibis

    result = propagate_structured_plans(
        node(RS.FILTER, predicate=ibis._.col > 1),
        [MappingProxyType({})],
        MappingProxyType({}),
    )

    assert result == {}


@pytest.mark.parametrize(
    ("operation", "attrs"),
    [
        (RS.FILTER, {"predicate": ma.col("payload").is_not_null()}),
        (RS.SORT, {"sort_fields": ["payload"]}),
        (RM.DROP_NULLS, {"options": {"subset": ["payload"]}}),
        (RM.TOP_K, {"options": {"by": "payload"}}),
        (RM.EXPLODE, {"options": {"columns": ["payload"]}}),
        (RM.UNNEST, {"options": {"columns": ["payload"]}}),
        (RS.AGGREGATE, {"keys": [ma.col("payload")], "measures": []}),
    ],
)
def test_structured_consumers_reject_tagged_input(operation, attrs):
    """Operations that inspect a physical carrier fail before native execution."""
    with pytest.raises(UnsupportedStructuredTransportUse, match="payload"):
        propagate_structured_plans(
            node(operation, **attrs),
            [MappingProxyType({"payload": transport_plan()})],
            MappingProxyType({}),
        )


def test_union_all_requires_equal_transport_declarations():
    """Union-all can preserve a tag only when every input agrees exactly."""
    plan = transport_plan()
    aligned = propagate_structured_plans(
        node(RS.UNION_ALL),
        [MappingProxyType({"payload": plan}), MappingProxyType({"payload": plan})],
        MappingProxyType({}),
    )
    assert aligned == {"payload": plan}

    with pytest.raises(UnsupportedStructuredTransportUse, match="UNION_ALL"):
        propagate_structured_plans(
            node(RS.UNION_ALL),
            [MappingProxyType({"payload": plan}), MappingProxyType({})],
            MappingProxyType({}),
        )


@pytest.mark.parametrize("operation", [RS.DISTINCT, RS.UNION_DISTINCT])
def test_equality_operations_reject_remaining_transport_plans(operation):
    """Physical JSON representation cannot participate in equality set semantics."""
    with pytest.raises(UnsupportedStructuredTransportUse):
        propagate_structured_plans(
            node(operation), [MappingProxyType({"payload": transport_plan()})], MappingProxyType({})
        )


def test_unknown_relation_operation_is_rejected_when_transport_is_present():
    """An unclassified operation fails closed instead of silently dropping transport safety."""
    class UnknownOperation(Enum):
        UNKNOWN = "unknown"

    with pytest.raises(UnsupportedStructuredTransportUse):
        propagate_structured_plans(
            node(UnknownOperation.UNKNOWN),
            [MappingProxyType({"payload": transport_plan()})],
            MappingProxyType({}),
        )


def test_filter_rejects_transport_before_backend_filter_dispatch(monkeypatch):
    """The visitor checks lineage before compiling a predicate or calling Polars."""
    import polars as pl

    from mountainash.relations.backends.relation_systems.polars import (
        PolarsRelationSystem,
    )
    from mountainash.typespec.spec import FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    def filter_must_not_run(*args, **kwargs):
        raise AssertionError("backend filter received a transported physical field")

    monkeypatch.setattr(PolarsRelationSystem, "filter", filter_must_not_run)
    relation = ma.relation(pl.DataFrame({"payload": ["[1]"]})).conform(
        TypeSpec(fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)])
    )

    with pytest.raises(UnsupportedStructuredTransportUse, match="payload"):
        relation.filter(ma.col("payload").is_not_null()).to_polars()


def test_sort_rejects_transport_before_backend_sort_dispatch(monkeypatch):
    """The visitor checks lineage on real ``SortField`` payloads before calling Polars.

    Regression coverage for item 115: the other tests in this module drive
    ``propagate_structured_plans`` directly with a synthetic ``SimpleNamespace``, so a
    real ``SortRelNode`` (whose ``sort_fields`` are genuine ``SortField`` instances,
    not bare strings) is never exercised end-to-end elsewhere.
    """
    import polars as pl

    from mountainash.relations.backends.relation_systems.polars import (
        PolarsRelationSystem,
    )
    from mountainash.typespec.spec import FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    def sort_must_not_run(*args, **kwargs):
        raise AssertionError("backend sort received a transported physical field")

    monkeypatch.setattr(PolarsRelationSystem, "sort", sort_must_not_run)
    relation = ma.relation(pl.DataFrame({"payload": ["[1]"]})).conform(
        TypeSpec(fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)])
    )

    with pytest.raises(UnsupportedStructuredTransportUse, match="payload"):
        relation.sort("payload").to_polars()


def test_aggregate_rejects_transport_before_backend_aggregate_dispatch(monkeypatch):
    """The visitor checks lineage on real ``AggregateRelNode`` keys before calling Polars.

    Regression coverage for item 115: exercises the ``_AGGREGATE`` policy's
    ``vars(node)`` walk (which includes the node's own ``input`` child relation
    alongside ``keys``/``measures``) against a real relation, not a synthetic
    ``SimpleNamespace``.
    """
    import polars as pl

    from mountainash.relations.backends.relation_systems.polars import (
        PolarsRelationSystem,
    )
    from mountainash.typespec.spec import FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    def aggregate_must_not_run(*args, **kwargs):
        raise AssertionError("backend aggregate received a transported physical field")

    monkeypatch.setattr(PolarsRelationSystem, "aggregate", aggregate_must_not_run)
    relation = ma.relation(pl.DataFrame({"payload": ["[1]"], "other": [1]})).conform(
        TypeSpec(
            fields=[
                FieldSpec(name="payload", type=UniversalType.ARRAY),
                FieldSpec(name="other", type=UniversalType.INTEGER),
            ]
        )
    )

    with pytest.raises(UnsupportedStructuredTransportUse, match="payload"):
        relation.group_by("payload").agg(ma.col("other").sum()).to_polars()
