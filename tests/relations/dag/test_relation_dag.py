"""Tests for RelationDAG core (Task 16)."""
from __future__ import annotations

import pytest
import mountainash as ma
from mountainash.relations import LogicalTerminalRequired
from mountainash.relations.dag.dag import RelationDAG

from fixtures.backend_registry import ALL_BACKENDS


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
    # Message comes from the shared mountainash.graph.topological_order
    # ("Cycle detected: ..."); match case-insensitively on the leading word.
    with pytest.raises(ValueError, match="[Cc]ycle detected"):
        dag.topological_order("b")


# ---------------------------------------------------------------------------
# Task 9 step 2/6: complete native DAG terminal matrix -- dag.collect() and
# dag.collect_with_drift() fail closed for an applied structured transport
# (spec 12.4's requires_logical_terminal), across the full backend matrix,
# and never call materialize_native() for the failing requested resource.
# ---------------------------------------------------------------------------


def _json_dag(
    backend_name, backend_factory, *, action: str = "coerce", apply_value_transforms: bool = True
):
    from mountainash.typespec.spec import FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    df = backend_factory.create({"payload": ["[1,2]", "[3]"]}, backend_name)
    spec = TypeSpec(fields_match="open", fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)])
    rel = ma.relation(df).conform(
        spec, contract={"data_type": action}, apply_value_transforms=apply_value_transforms
    )
    dag = RelationDAG()
    dag.add("resource", rel)
    return dag


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestNativeDAGTerminalFailsClosed:
    @pytest.mark.parametrize("terminal", ["collect", "collect_with_drift"])
    def test_raises_logical_terminal_required(self, backend_name, backend_factory, terminal):
        dag = _json_dag(backend_name, backend_factory)
        with pytest.raises(LogicalTerminalRequired):
            getattr(dag, terminal)("resource")

    def test_zero_materialize_native_calls(self, backend_name, backend_factory, monkeypatch):
        import mountainash.relations.core.materialization as materialization_module

        dag = _json_dag(backend_name, backend_factory)
        calls = []
        original = materialization_module.materialize_native

        def spy(*args, **kwargs):
            calls.append(1)
            return original(*args, **kwargs)

        monkeypatch.setattr(materialization_module, "materialize_native", spy)

        with pytest.raises(LogicalTerminalRequired):
            dag.collect("resource")
        assert calls == []


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestNativeDAGTerminalSuccess:
    def test_dependent_that_drops_the_field_still_collects(self, backend_name, backend_factory):
        """Task 9 step 6: only the REQUESTED resource's own plans are
        guarded. ``resource`` still carries the un-decodable JSON field and
        would itself raise if requested directly, but ``derived`` (which
        depends on it) drops that field before its own output -- so
        requesting ``derived`` collects natively without ever decoding."""
        dag = _json_dag(backend_name, backend_factory)
        dag.add("derived", dag.ref("resource").drop("payload").with_columns(ma.lit(1).alias("n")))
        result = dag.collect("derived")
        assert result is not None
        with pytest.raises(LogicalTerminalRequired):
            dag.collect("resource")

    def test_evolve_collects_natively(self, backend_name, backend_factory):
        dag = _json_dag(backend_name, backend_factory, action="evolve")
        result = dag.collect("resource")
        assert result is not None

    def test_structural_only_collects_natively(self, backend_name, backend_factory):
        dag = _json_dag(backend_name, backend_factory, apply_value_transforms=False)
        result = dag.collect("resource")
        assert result is not None
