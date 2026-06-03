"""Tests for RelationDAG core (Task 16)."""
from __future__ import annotations

import pytest
import mountainash as ma
from mountainash.relations.dag.dag import RelationDAG


def test_empty_dag():
    dag = RelationDAG()
    assert dag.relations == {}
    assert dag.dependency_edges == set()
    assert dag.constraint_edges == set()


def test_add_named_relation():
    dag = RelationDAG()
    dag.add("orders", ma.relation([{"id": 1}]))
    assert "orders" in dag.relations


def test_duplicate_add_raises():
    dag = RelationDAG()
    dag.add("orders", ma.relation([{"id": 1}]))
    with pytest.raises(ValueError, match="already in DAG"):
        dag.add("orders", ma.relation([{"id": 2}]))


def test_ref_creates_dependency_edge():
    dag = RelationDAG()
    dag.add("orders", ma.relation([{"id": 1}]))
    dag.add("active_orders", dag.ref("orders").filter(ma.col("id").gt(0)))
    assert ("orders", "active_orders") in dag.dependency_edges


def test_source_registers_relation_and_returns_ref():
    from mountainash.relations.core.relation_nodes.extensions_mountainash import RefRelNode

    dag = RelationDAG()
    raw = dag.source("raw", [{"id": 1, "status": "active"}])

    assert "raw" in dag.relations
    assert isinstance(raw._node, RefRelNode)
    assert raw._node.name == "raw"


def test_source_returned_ref_records_dependency_when_derived_relation_added():
    dag = RelationDAG()
    raw = dag.source("raw", [{"id": 1, "status": "active"}])
    dag.add("active", raw.filter(ma.col("status").eq("active")))

    assert ("raw", "active") in dag.dependency_edges


def test_add_discovers_ref_under_conform_node():
    from mountainash.relations.core.relation_api.relation import Relation
    from mountainash.relations.core.relation_nodes.extensions_mountainash import (
        ConformRelNode,
    )

    dag = RelationDAG()
    dag.add("raw", ma.relation([{"id": 1}]))
    dag.add("conformed", Relation(ConformRelNode(input=dag.ref("raw")._node, spec={})))

    assert ("raw", "conformed") in dag.dependency_edges


def test_topological_order_simple_chain():
    dag = RelationDAG()
    dag.add("a", ma.relation([{"x": 1}]))
    dag.add("b", dag.ref("a"))
    dag.add("c", dag.ref("b"))
    assert dag.topological_order("c") == ["a", "b", "c"]


def test_topological_order_unrelated_nodes_excluded():
    dag = RelationDAG()
    dag.add("a", ma.relation([{"x": 1}]))
    dag.add("b", ma.relation([{"x": 2}]))   # unrelated
    dag.add("c", dag.ref("a"))
    assert dag.topological_order("c") == ["a", "c"]  # b excluded


def test_cycle_raises():
    dag = RelationDAG()
    dag.add("a", ma.relation([{"x": 1}]))
    dag.add("b", dag.ref("a"))
    dag.dependency_edges.add(("b", "a"))  # forced cycle
    with pytest.raises(ValueError, match="cycle"):
        dag.topological_order("b")
