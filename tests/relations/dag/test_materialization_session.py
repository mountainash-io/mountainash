"""DAGMaterializationSession structural behavior tests (Task 7, spec section 10)."""
from __future__ import annotations

import pandas as pd
import polars as pl
import pytest

import mountainash as ma
from mountainash.core.capabilities.policy import CapabilityPolicy, _new_execution_context
from mountainash.core.constants import CONST_BACKEND
from mountainash.relations.core.materialization import DiagnosticFrameView
from mountainash.relations.core.execution.location import IdentityTokens, LocationResolver
from mountainash.relations.core.execution.metadata import MetadataSession
from mountainash.relations.core.execution.transport import TransportSession
from mountainash.relations.dag import DAGMaterializationSession, RelationDAG
from fixtures.backend_registry import REGISTRY

# Trigger backend registration (side-effect imports)
import mountainash.relations.backends  # noqa: F401
import mountainash.expressions.backends  # noqa: F401


def test_session_compiles_each_resource_once_and_memoizes_consumer_coercion(monkeypatch):
    dag = RelationDAG()
    source_relation = ma.relation(pd.DataFrame({"id": [1, 2]}))
    dag.add("source", source_relation)
    dag.add("target", dag.ref("source").select("id"))
    source_node = source_relation._node
    source_node_type = type(source_node)
    original_accept = source_node_type.accept
    compile_calls = 0

    def counted_accept(self, visitor):
        nonlocal compile_calls
        if self is source_node:
            compile_calls += 1
        return original_accept(self, visitor)

    monkeypatch.setattr(source_node_type, "accept", counted_accept)
    policy = CapabilityPolicy.trusted()
    session = DAGMaterializationSession(dag, execution_policy=policy, backend="polars")
    first, visitor = session.compile_registered("target")
    consumer_context = visitor.execution_context
    second = session.resolve("source", consumer_context)
    third = session.resolve("source", consumer_context)

    assert first.value_identity.family is CONST_BACKEND.POLARS
    assert second is third
    assert compile_calls == 1
    assert session.canonical_keys == frozenset({"source", "target"})
    assert session.coercion_keys == frozenset(
        {("source", consumer_context.target.token, consumer_context.observations)}
    )
    assert all(not isinstance(value, DiagnosticFrameView) for value in session.cached_values)
    session.close(release_owned=False)


def test_same_family_same_dialect_ref_is_not_coerced():
    dag = RelationDAG()
    dag.add("source", ma.relation(pl.DataFrame({"id": [1, 2]})))
    dag.add("target", dag.ref("source").select("id"))

    policy = CapabilityPolicy.trusted()
    session = DAGMaterializationSession(dag, execution_policy=policy, backend="polars")
    native, _visitor = session.compile_registered("target")
    assert native.value_identity.family is CONST_BACKEND.POLARS
    # No coercion needed: source is already polars/polars, matching target's
    # own resolved identity -- the coercion cache stays empty.
    assert session.coercion_keys == frozenset()
    session.close(release_owned=False)


def test_resolve_before_compile_registered_still_memoizes():
    dag = RelationDAG()
    dag.add("source", ma.relation(pl.DataFrame({"id": [1, 2]})))

    policy = CapabilityPolicy.trusted()
    session = DAGMaterializationSession(dag, execution_policy=policy)
    consumer_context = _new_execution_context(
        None, family_override=CONST_BACKEND.POLARS, policy=policy,
    )
    value = session.resolve("source", consumer_context)
    assert value is not None
    assert session.canonical_keys == frozenset({"source"})
    session.close(release_owned=False)


def test_diagnostic_view_is_polars_frame_and_not_reused_by_resolve():
    dag = RelationDAG()
    dag.add("source", ma.relation(pl.DataFrame({"id": [1, 2]})))

    session = DAGMaterializationSession(dag, execution_policy=CapabilityPolicy.trusted())
    session.compile_registered("source")
    view = session.diagnostic_view("source")
    assert isinstance(view, DiagnosticFrameView)
    assert view.frame.to_dict(as_series=False) == {"id": [1, 2]}
    # The ref resolver's own cache never contains a DiagnosticFrameView.
    assert all(not isinstance(v, DiagnosticFrameView) for v in session.cached_values)
    session.close(release_owned=False)


def test_diagnostic_view_unknown_name_returns_none():
    dag = RelationDAG()
    dag.add("source", ma.relation(pl.DataFrame({"id": [1]})))
    session = DAGMaterializationSession(dag, execution_policy=CapabilityPolicy.trusted())
    assert session.diagnostic_view("source") is None
    session.close(release_owned=False)


def test_unknown_ref_name_raises():
    dag = RelationDAG()
    policy = CapabilityPolicy.trusted()
    session = DAGMaterializationSession(dag, execution_policy=policy)
    consumer_context = _new_execution_context(
        None, family_override=CONST_BACKEND.POLARS, policy=policy,
    )
    with pytest.raises(Exception, match="not in DAG"):
        session.resolve("missing", consumer_context)
    session.close(release_owned=False)


def test_close_is_idempotent():
    dag = RelationDAG()
    dag.add("source", ma.relation(pl.DataFrame({"id": [1]})))
    session = DAGMaterializationSession(dag, execution_policy=CapabilityPolicy.trusted())
    session.compile_registered("source")
    session.close(release_owned=True)
    session.close(release_owned=True)  # no error on second close


def test_connectionless_plan_is_compiled_once_per_physical_binding():
    import ibis

    memory = ibis.memtable({"id": [1, 2]})
    dag = RelationDAG()
    dag.add("memory", ma.relation(memory).filter(ma.col("id") > 0))
    a = REGISTRY["ibis-duckdb"].build({"id": [1]}, "a")
    b = REGISTRY["ibis-duckdb"].build({"id": [2]}, "b")
    tokens = IdentityTokens()
    location = LocationResolver(tokens)
    session = DAGMaterializationSession(dag, execution_policy=CapabilityPolicy.trusted())
    session._execution_tokens = tokens
    session._execution_metadata = MetadataSession(tokens)
    session._execution_transport = TransportSession(tokens)
    try:
        first = session.resolve_at("memory", location.resolve(ma.relation(a)._node))
        assert session.resolve_at("memory", location.resolve(ma.relation(a)._node)) is first
        second = session.resolve_at("memory", location.resolve(ma.relation(b)._node))
        assert second is not first
        assert len(session._bound) == 2
        assert session.canonical_keys == frozenset({"memory"})
        assert session._canonical == {}
        assert sorted(ma.relation(a.join(first, "id")).to_dict()["id"]) == [1]
        assert sorted(ma.relation(b.join(second, "id")).to_dict()["id"]) == [2]
    finally:
        session._execution_transport.close(release_owned=False)
        session.close(release_owned=False)
