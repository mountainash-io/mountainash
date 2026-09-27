"""DAG roots use prepared physical placement, not ref spelling."""
from __future__ import annotations

import pytest
import ibis
import pyarrow as pa

import mountainash as ma
from fixtures.backend_registry import REGISTRY
from mountainash.relations.core.errors import CompileRequiresExecutionError, UnresolvedExecutionLocationError


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
    assert len(calls) == 1


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
