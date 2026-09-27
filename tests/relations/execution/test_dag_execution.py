"""DAG roots use prepared physical placement, not ref spelling."""
from __future__ import annotations

import pytest
import ibis
import pyarrow as pa

import mountainash as ma
from fixtures.backend_registry import REGISTRY
from mountainash.core.capabilities.policy import CapabilityPolicy
from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry
from mountainash.core.capabilities.declarations import (
    BoundSegment, CapabilityKey, CapabilityPolicyRule, CapabilitySegment, Domain,
)
from mountainash.core.capabilities.identity import Dialect, Scope
from mountainash.core.capabilities.schema import PolicyAction, PolicyConsumer
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.types import BackendCapabilityError
from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_SUBSTRAIT_REL
from mountainash.relations.core.errors import (
    CompileRequiresExecutionError, ConflictingExecutionTargetError,
    UnresolvedExecutionLocationError,
)


@pytest.mark.parametrize("registered", [False, True])
@pytest.mark.parametrize("reverse_names", [False, True])
def test_root_target_is_independent_of_ref_names(registered, reverse_names):
    left = REGISTRY["ibis-duckdb"].build({"id": [1, 2]}, "a")
    right = REGISTRY["ibis-sqlite"].build({"id": [2]}, "b")
    dag = ma.RelationDAG()
    left_name, right_name = ("zzz_left", "aaa_right") if reverse_names else ("aaa_left", "zzz_right")
    dag.add(left_name, ma.relation(left))
    dag.add(right_name, ma.relation(right))
    rel = dag.ref(left_name).join(dag.ref(right_name), on="id", execute_on="right")
    if registered:
        dag.add("result", rel)
        result = dag.collect("result")
    else:
        before = dict(dag.relations)
        result = rel.collect()
        assert dag.relations == before
    assert result._find_backend(use_default=False) is right._find_backend(use_default=False)
    assert ma.relation(result).to_dict() == {"id": [2]}


def test_explicit_backend_cannot_override_nested_dag_join_target():
    a = REGISTRY["polars"].build({"id": [1]}, "a")
    b = REGISTRY["ibis-duckdb"].build({"id": [1]}, "b")
    dag = ma.RelationDAG()
    dag.add("a", ma.relation(a))
    dag.add("b", ma.relation(b))
    dag.add("target", dag.ref("a").join(dag.ref("b"), on="id", execute_on="right").select("id"))
    with pytest.raises(ConflictingExecutionTargetError):
        dag.collect("target", backend="polars")


def test_resource_ref_with_ibis_family_override_keeps_declared_read_location():
    from mountainash.relations.core.relation_api.relation import Relation
    from mountainash.relations.core.relation_nodes.extensions_mountainash import ResourceReadRelNode
    from mountainash.typespec.datapackage import DataResource

    dag = ma.RelationDAG()
    dag.add("inline", Relation(ResourceReadRelNode(resource=DataResource(
        name="inline", data=[{"id": 1}, {"id": 2}],
    ))))
    dag.add("projected", dag.ref("inline").select("id"))
    assert dag.collect("projected", backend="ibis").collect().to_dict(as_series=False) == {
        "id": [1, 2],
    }


def test_compile_rejects_late_ref_transfer_before_canonical_cache(monkeypatch):
    left = REGISTRY["ibis-duckdb"].build({"id": [1]}, "early")
    right = REGISTRY["ibis-sqlite"].build({"id": [2]}, "late")
    dag = ma.RelationDAG()
    dag.add("early", ma.relation(left))
    dag.add("late", ma.relation(right))
    rel = ma.concat([dag.ref("early"), dag.ref("late")])

    def forbidden(*args, **kwargs):
        raise AssertionError("compiled before whole-tree phase check")

    monkeypatch.setattr(type(left), "cache", forbidden)
    monkeypatch.setattr(type(left), "to_pyarrow", forbidden)
    with pytest.raises(CompileRequiresExecutionError):
        rel.compile()


def test_same_connection_ref_compile_does_not_cache(monkeypatch):
    table = REGISTRY["ibis-duckdb"].build({"id": [1, 2]}, "source")
    dag = ma.RelationDAG()
    dag.add("source", ma.relation(table))

    def forbidden(*args, **kwargs):
        raise AssertionError("compile-only invoked eager cache")

    monkeypatch.setattr(type(table), "cache", forbidden)
    plan = dag.ref("source").filter(ma.col("id") > 1).compile()
    assert plan._find_backend(use_default=False) is table._find_backend(use_default=False)


def test_explain_ref_transfer_never_materializes_canonical(monkeypatch):
    a = REGISTRY["ibis-duckdb"].build({"id": [1]}, "early")
    b = REGISTRY["ibis-sqlite"].build({"id": [1]}, "late")
    dag = ma.RelationDAG()
    dag.add("early", ma.relation(a))
    dag.add("late", ma.relation(b))

    def forbidden(*args, **kwargs):
        raise AssertionError("explain executed a named dependency")

    monkeypatch.setattr(type(a), "cache", forbidden)
    monkeypatch.setattr(type(a), "to_pyarrow", forbidden)
    explanation = dag.ref("early").join(dag.ref("late"), on="id").explain()
    assert "transfer" in explanation.lower()
    assert "ibis-sqlite" in explanation


def test_named_ibis_dependency_is_cached_once_when_collected(monkeypatch):
    table = REGISTRY["ibis-duckdb"].build({"id": [1, 2]}, "source")
    dag = ma.RelationDAG()
    dag.add("source", ma.relation(table).filter(ma.col("id") > 0))
    dag.add("target", ma.concat([dag.ref("source"), dag.ref("source")]))
    original = type(table).cache
    calls = []

    def counted(self, *args, **kwargs):
        calls.append(self)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(type(table), "cache", counted)
    result = dag.collect("target")
    assert sorted(ma.relation(result).to_dict()["id"]) == [1, 1, 2, 2]
    assert len(calls) == 2  # one named source and one named result


def test_named_ibis_root_is_materialized_at_canonical_boundary(monkeypatch):
    table = REGISTRY["ibis-duckdb"].build({"id": [1]}, "root")
    dag = ma.RelationDAG()
    dag.add("root", ma.relation(table).filter(ma.col("id") > 0))
    original = type(table).cache
    calls = []

    def counted(self, *args, **kwargs):
        calls.append(self)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(type(table), "cache", counted)
    assert ma.relation(dag.collect("root")).to_dict() == {"id": [1]}
    assert len(calls) == 1


def test_repeated_named_ref_prepares_original_plan_once(monkeypatch):
    from mountainash.relations.dag.materialization import DAGMaterializationSession

    dag = ma.RelationDAG()
    dag.add("source", ma.relation(REGISTRY["polars"].build({"id": [1]}, "s")))
    dag.add("target", ma.concat([dag.ref("source"), dag.ref("source")]))
    original = DAGMaterializationSession._node_for
    calls = []

    def counted(self, name):
        calls.append(name)
        return original(self, name)

    monkeypatch.setattr(DAGMaterializationSession, "_node_for", counted)
    assert dag.collect("target").collect().to_dict(as_series=False) == {"id": [1, 1]}
    assert calls.count("source") == 1


def test_ref_child_adopts_source_conform_diagnostics():
    import polars as pl

    from mountainash.typespec.spec import FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    dag = ma.RelationDAG()
    spec = TypeSpec(fields_match="open", fields=[
        FieldSpec(name="payload", type=UniversalType.OBJECT),
    ])
    source = ma.relation(pl.DataFrame({
        "id": [1], "payload": ['{"k": 1}'],
    })).conform(spec, contract={"data_type": "coerce"})
    _, source_visitor = source._compile_and_execute_with_visitor()
    assert any(trace.records for trace in source_visitor.diagnostic_traces.values())
    dag.add("source", source)
    rel = dag.ref("source").select("id")
    result, visitor = dag._execute_with_visitor(
        rel, execution_policy=CapabilityPolicy.trusted(),
    )
    assert result.collect().to_dict(as_series=False) == {"id": [1]}
    assert any(trace.records for trace in visitor.diagnostic_traces.values())


@pytest.mark.parametrize("registered", [False, True])
@pytest.mark.parametrize("nested", [False, True])
def test_late_transformed_ref_gate_precedes_canonical_cache_and_export(
    monkeypatch, registered, nested,
):
    from mountainash.relations.dag.materialization import DAGMaterializationSession

    a = REGISTRY["ibis-duckdb"].build({"id": [1]}, "early")
    b = REGISTRY["ibis-sqlite"].build({"id": [1]}, "late")
    dag = ma.RelationDAG()
    early = ma.relation(a)
    dag.add("early", early)
    dag.add("late", ma.relation(b))
    if nested:
        early = dag.ref("early").join(dag.ref("late"), on="id", execute_on="left")
    else:
        early = dag.ref("early")
    rel = early.join(dag.ref("late"), on="id", execute_on="right")
    if registered:
        dag.add("result", rel)

    original_node_for = DAGMaterializationSession._node_for

    def transformed(self, name):
        node = original_node_for(self, name)
        if name == "late":
            return ma.relation(b).filter(ma.col("id") > 0)._node
        return node

    monkeypatch.setattr(DAGMaterializationSession, "_node_for", transformed)
    exports = []

    def forbidden(*args, **kwargs):
        exports.append(True)
        raise AssertionError("native work preceded late ref preflight")

    monkeypatch.setattr(type(a), "cache", forbidden)
    monkeypatch.setattr(type(a), "to_pyarrow", forbidden)
    snapshot = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.reset()
        CapabilityRegistry.register_segment(BoundSegment(
            "mountainash.relations.backends.capabilities.ibis.dialects.ibis_sqlite.substrait.relation",
            Scope(CONST_BACKEND.IBIS, Dialect("ibis-sqlite")),
            CapabilitySegment(Domain.RELATION, policies=(CapabilityPolicyRule(
                key=CapabilityKey(RKEY_SUBSTRAIT_REL.FILTER, "*"),
                level=CapabilityLevel.UNSUPPORTED,
                since="2026-09-27", message="P3 transformed late ref gate",
                consumer=PolicyConsumer.GATE, action=PolicyAction.BLOCK,
            ),)),
        ))
        with pytest.raises(BackendCapabilityError, match="P3 transformed late ref gate"):
            if registered:
                dag.collect("result")
            else:
                rel.collect()
        assert exports == []
    finally:
        CapabilityRegistry.restore(snapshot)


@pytest.mark.parametrize("terminal", ["collect", "to_polars"])
@pytest.mark.parametrize("operation", ["join", "union_all", "union_distinct"])
@pytest.mark.parametrize("configured_default", [False, True])
def test_connectionless_authority_does_not_acquire_implicit_backend(
    monkeypatch, terminal, operation, configured_default,
):
    default = ibis.duckdb.connect() if configured_default else None
    monkeypatch.setattr(ibis.options, "default_backend", default)
    memory = ibis.memtable(pa.table({"id": [1]}))
    dag = ma.RelationDAG()
    dag.add("memory", ma.relation(memory))
    dag.add("raw", ma.relation({"id": [2]}))
    left, right = dag.ref("memory"), dag.ref("raw")
    rel = left.join(right, on="id") if operation == "join" else ma.concat(
        [left, right], distinct=operation == "union_distinct",
    )
    original = type(memory)._find_backend

    def find_without_default(self, *, use_default=False):
        assert not use_default
        return original(self, use_default=False)

    monkeypatch.setattr(type(memory), "_find_backend", find_without_default)
    try:
        with pytest.raises(UnresolvedExecutionLocationError):
            getattr(rel, terminal)()
    finally:
        if default is not None:
            default.disconnect()
