"""Item 46 (c): structured FK metadata beside constraint_edges."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.relations.dag.dag import RelationDAG
from mountainash.relations.dag.packaging import resource_to_relation
from mountainash.typespec.datapackage import DataResource
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


class TestTwoEdgeModelGuard:
    def test_no_union_accessor(self):
        dag = RelationDAG()
        with pytest.raises(AttributeError):
            dag.edges
        with pytest.raises(AttributeError):
            dag.all_edges()
