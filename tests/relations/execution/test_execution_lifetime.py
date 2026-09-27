"""Returned native graphs outlive execution sessions; independent calls do not share state."""

from concurrent.futures import ThreadPoolExecutor
import gc

import pytest

import mountainash as ma
from fixtures.backend_registry import REGISTRY


IBIS = [name for name, spec in REGISTRY.items() if spec.family == "ibis"]


@pytest.mark.parametrize("backend_name", IBIS)
@pytest.mark.parametrize("dag_bound", [False, True])
def test_native_result_survives_gc_with_foreign_and_canonical_dependencies(backend_name, dag_bound):
    def build():
        left = REGISTRY["ibis-duckdb"].build({"id": [1, 2], "value": [10, 20]}, "source")
        right = REGISTRY[backend_name].build({"id": [2]}, "target")
        if dag_bound:
            dag = ma.RelationDAG()
            dag.add("source", ma.relation(left))
            dag.add("target", ma.relation(right))
            result = dag.ref("source").join(dag.ref("target"), on="id", execute_on="right").collect()
        else:
            result = ma.relation(left).join(right, on="id", execute_on="right").collect()
        return result, right._find_backend(use_default=False)

    native, connection = build()
    gc.collect()
    assert native._find_backend(use_default=False) is connection
    assert ma.relation(native).to_dicts() == [{"id": 2, "value": 20}]


@pytest.mark.parametrize("backend_name", IBIS)
def test_same_connection_dag_canonical_result_survives_gc(backend_name, backend_factory):
    def build():
        left, right = backend_factory.create_pair(
            {"id": [1, 2], "payload": [10, 20]}, {"id": [2]}, backend_name,
        )
        dag = ma.RelationDAG()
        dag.add("source", ma.relation(left))
        dag.add("target", ma.relation(right))
        native = dag.ref("source").join(dag.ref("target"), on="id").collect()
        return native, left._find_backend(use_default=False)

    native, connection = build()
    gc.collect()
    assert native._find_backend(use_default=False) is connection
    assert ma.relation(native).to_dicts() == [{"id": 2, "payload": 20}]


@pytest.mark.parametrize("backend_name", IBIS)
def test_successful_transfer_never_releases_caller_tables_or_connections(backend_name, monkeypatch):
    left = REGISTRY["ibis-duckdb"].build({"id": [2]}, "source")
    right = REGISTRY[backend_name].build({"id": [2]}, "target")
    caller_releases = []
    with monkeypatch.context() as guard:
        guard.setattr(type(left), "release", lambda *_: caller_releases.append("table"), raising=False)
        guard.setattr(type(left._find_backend(use_default=False)), "disconnect",
                      lambda *_: caller_releases.append("source connection"))
        guard.setattr(type(right._find_backend(use_default=False)), "disconnect",
                      lambda *_: caller_releases.append("destination connection"))
        native = ma.relation(left).join(right, on="id", execute_on="right").collect()
        gc.collect()
        assert ma.relation(native).to_dicts() == [{"id": 2}]
        assert caller_releases == []


@pytest.mark.parametrize("backend_name", IBIS)
def test_two_independent_native_sessions_remain_isolated(backend_name):
    def execute(value):
        left = REGISTRY[backend_name].build({"id": [value], "payload": [value * 10]}, "same")
        right = REGISTRY[backend_name].build({"id": [value]}, "same")
        result = ma.relation(left).join(right, on="id", execute_on="right").collect()
        connection = right._find_backend(use_default=False)
        # SQLite connections are thread-affine: execute/read on the owning
        # worker, rather than accidentally testing cross-thread connection use.
        assert result._find_backend(use_default=False) is connection
        rows = ma.relation(result).to_dicts()
        return rows, connection

    with ThreadPoolExecutor(max_workers=2) as pool:
        first, second = pool.map(execute, (2, 3))
    assert first[1] is not second[1]
    assert first[0] == [{"id": 2, "payload": 20}]
    assert second[0] == [{"id": 3, "payload": 30}]


@pytest.mark.parametrize("backend_name", ["ibis-duckdb", "polars"])
def test_rules_shaped_scope_join_and_literal_free_request_grid(backend_name):
    scopes = REGISTRY[backend_name].build({"scope_id": [1, 2], "request_id": [10, 20]}, "scopes")
    context = REGISTRY[backend_name].build({"scope_id": [2, 3], "context_id": ["b", "c"]}, "context")
    joined = ma.relation(scopes).join(context, on="scope_id", execute_on="right")
    assert joined.to_dicts() == [{"scope_id": 2, "request_id": 20, "context_id": "b"}]
    if backend_name == "ibis-duckdb":
        assert joined.collect()._find_backend(use_default=False) is context._find_backend(use_default=False)

    requests = REGISTRY[backend_name].build({"request_id": [10, 20]}, "requests")
    contexts = REGISTRY[backend_name].build({"context_id": ["a", "b"]}, "contexts")
    grid = ma.relation(requests).cross_join(contexts, execute_on="right")
    assert sorted(grid.to_dicts(), key=lambda row: (row["request_id"], row["context_id"])) == [
        {"request_id": 10, "context_id": "a"},
        {"request_id": 10, "context_id": "b"},
        {"request_id": 20, "context_id": "a"},
        {"request_id": 20, "context_id": "b"},
    ]
    if backend_name == "ibis-duckdb":
        assert grid.collect()._find_backend(use_default=False) is contexts._find_backend(use_default=False)
