"""Item 46 (c): structured FK metadata beside constraint_edges."""
from __future__ import annotations
from copy import deepcopy

import polars as pl
import pytest

import mountainash as ma
from mountainash.relations.dag.dag import RelationDAG
from mountainash.relations.dag.packaging import resource_to_relation
from mountainash.typespec.datapackage import DataPackage, DataResource
from mountainash.typespec.spec import ForeignKey, ForeignKeyReference


def _fk(fields, resource, ref_fields):
    return ForeignKey(
        fields=list(fields),
        reference=ForeignKeyReference(resource=resource, fields=list(ref_fields)),
    )


def _dag_two_relations():
    dag = RelationDAG()
    dag.add("customers", ma.relation(pl.DataFrame({"id": [1]})))
    dag.add("orders", ma.relation(pl.DataFrame({"id": [1], "customer_id": [1]})))
    return dag


class TestAddConstraint:
    def test_populates_edge_and_metadata_never_dependencies(self):
        dag = _dag_two_relations()
        fk = _fk(["customer_id"], "customers", ["id"])
        dag.add_constraint("orders", fk)
        assert ("customers", "orders") in dag.constraint_edges
        assert dag.constraint_metadata[("customers", "orders")] == [fk]
        assert dag.dependency_edges == set()  # two-edge separation

    def test_unknown_child_raises_keyerror(self):
        dag = _dag_two_relations()
        with pytest.raises(KeyError):
            dag.add_constraint("nope", _fk(["x"], "customers", ["id"]))

    def test_unknown_target_raises_valueerror(self):
        dag = _dag_two_relations()
        with pytest.raises(ValueError):
            dag.add_constraint("orders", _fk(["x"], "ghost", ["id"]))

    def test_empty_reference_normalises_to_self_edge(self):
        dag = _dag_two_relations()
        dag.add_constraint("orders", _fk(["parent_id"], None, ["id"]))
        assert ("orders", "orders") in dag.constraint_edges
        assert ("orders", "orders") in dag.constraint_metadata

    def test_pass_through_child_rejected(self):
        dag = RelationDAG()
        res = DataResource(
            name="raw", path="raw.csv", type="table",
            table_schema={"fields": [{"name": "id", "type": "integer"}]},
        )
        dag.add("raw", resource_to_relation(res))
        with pytest.raises(ValueError, match="table_schema"):
            dag.add_constraint("raw", _fk(["id"], None, ["id"]))

    def test_repeated_identical_fk_is_idempotent(self):
        dag = _dag_two_relations()
        dag.add_constraint("orders", _fk(["customer_id"], "customers", ["id"]))
        dag.add_constraint("orders", _fk(["customer_id"], "customers", ["id"]))
        assert len(dag.constraint_metadata[("customers", "orders")]) == 1

    def test_metadata_keys_subset_of_edges_invariant(self):
        dag = _dag_two_relations()
        dag.add_constraint("orders", _fk(["customer_id"], "customers", ["id"]))
        dag.constraint_edges.add(("customers", "customers"))  # topology-only edge
        assert set(dag.constraint_metadata.keys()) <= dag.constraint_edges


class TestConstraintsFor:
    def test_aggregates_across_targets_in_insertion_order(self):
        dag = _dag_two_relations()
        dag.add("items", ma.relation(pl.DataFrame({"order_id": [1], "customer_id": [1]})))
        fk1 = _fk(["order_id"], "orders", ["id"])
        fk2 = _fk(["customer_id"], "customers", ["id"])
        dag.add_constraint("items", fk1)
        dag.add_constraint("items", fk2)
        assert dag.constraints_for("items") == [fk1, fk2]

    def test_topology_only_edge_contributes_nothing(self):
        dag = _dag_two_relations()
        dag.constraint_edges.add(("customers", "orders"))
        assert dag.constraints_for("orders") == []


def test_distinct_foreign_keys_share_edge_and_keep_order():
    package = DataPackage(
        resources=[
            DataResource(
                name="parent",
                path="parent.csv",
                type="table",
                table_schema={"fields": [{"name": "id", "type": "integer"}]},
            ),
            DataResource(
                name="child",
                path="child.csv",
                type="table",
                table_schema={
                    "fields": [
                        {"name": "a", "type": "integer"},
                        {"name": "b", "type": "integer"},
                    ],
                    "foreignKeys": [
                        {
                            "fields": ["a"],
                            "reference": {"resource": "parent", "fields": ["id"]},
                        },
                        {
                            "fields": ["b"],
                            "reference": {"resource": "parent", "fields": ["id"]},
                        },
                    ],
                },
            ),
        ]
    )
    dag = package.to_relation_dag()
    edge = ("parent", "child")
    assert dag.constraint_edges == {edge}
    assert [fk.fields for fk in dag.constraint_metadata[edge]] == [["a"], ["b"]]


def test_authored_typespec_foreign_keys_are_routed_to_dag():
    from mountainash.typespec.spec import FieldSpec, TypeSpec

    package = DataPackage(
        resources=[
            DataResource(
                name="parent",
                path="parent.csv",
                type="table",
                table_schema=TypeSpec(
                    fields=[FieldSpec(name="id", type="integer")]
                ),
            ),
            DataResource(
                name="child",
                path="child.csv",
                type="table",
                table_schema=TypeSpec(
                    fields=[
                        FieldSpec(name="parent_id", type="integer"),
                    ],
                    foreign_keys=[
                        _fk(["parent_id"], "parent", ["id"]),
                    ],
                ),
            ),
        ]
    )
    dag = package.to_relation_dag()
    assert ("parent", "child") in dag.constraint_edges
    assert dag.constraints_for("child")[0].fields == ["parent_id"]


def test_non_tabular_target_raises_without_phantom_constraint():
    from mountainash.typespec.errors import InvalidDescriptorRelationship

    package = DataPackage(
        resources=[
            DataResource(
                name="asset",
                path="asset.png",
                format="png",
            ),
            DataResource(
                name="child",
                path="child.csv",
                type="table",
                table_schema={
                    "fields": [{"name": "asset_id", "type": "integer"}],
                    "foreignKeys": [
                        {
                            "fields": ["asset_id"],
                            "reference": {"resource": "asset", "fields": ["id"]},
                        }
                    ],
                },
            ),
        ]
    )
    with pytest.raises(
        InvalidDescriptorRelationship,
        match="foreign key between tabular package resources",
    ) as exc_info:
        package.to_relation_dag()
    assert (
        exc_info.value.descriptor_path
        == "$.resources[1].schema.foreignKeys[0].reference.resource"
    )
    assert exc_info.value.required_form == "foreign key between tabular package resources"
    assert exc_info.value.rejected_value == "asset"



def test_equal_raw_foreign_key_declarations_deduplicate_operational_metadata():
    raw = {
        "resources": [
            {
                "name": "parent",
                "path": "parent.csv",
                "type": "table",
                "schema": {"fields": [{"name": "id", "type": "integer"}]},
            },
            {
                "name": "child",
                "path": "child.csv",
                "type": "table",
                "schema": {
                    "fields": [{"name": "parent_id", "type": "integer"}],
                    "foreignKeys": [
                        {
                            "fields": ["parent_id"],
                            "reference": {"resource": "parent", "fields": ["id"]},
                        },
                        {
                            "fields": ["parent_id"],
                            "reference": {"resource": "parent", "fields": ["id"]},
                        },
                    ],
                },
            },
        ]
    }
    package = DataPackage.from_descriptor(deepcopy(raw))
    dag = package.to_relation_dag()
    assert len(dag.constraint_metadata[("parent", "child")]) == 1
    assert package.to_descriptor() == raw


def test_non_tabular_child_raises_without_phantom_constraint():
    from mountainash.typespec.errors import InvalidDescriptorRelationship

    package = DataPackage(
        resources=[
            DataResource(
                name="parent",
                path="parent.csv",
                type="table",
                table_schema={"fields": [{"name": "id", "type": "integer"}]},
            ),
            DataResource(
                name="asset",
                path="asset.png",
                format="png",
                table_schema={
                    "fields": [{"name": "parent_id", "type": "integer"}],
                    "foreignKeys": [
                        {
                            "fields": ["parent_id"],
                            "reference": {"resource": "parent", "fields": ["id"]},
                        }
                    ],
                },
            ),
        ]
    )
    with pytest.raises(
        InvalidDescriptorRelationship,
        match="foreign key between tabular package resources",
    ) as exc_info:
        package.to_relation_dag()
    assert (
        exc_info.value.descriptor_path
        == "$.resources[1].schema.foreignKeys[0]"
    )
    assert exc_info.value.required_form == "foreign key between tabular package resources"
    assert exc_info.value.rejected_value == "asset"


class TestTwoEdgeModelGuard:
    def test_no_union_accessor(self):
        dag = RelationDAG()
        with pytest.raises(AttributeError):
            dag.edges
        with pytest.raises(AttributeError):
            dag.all_edges()
