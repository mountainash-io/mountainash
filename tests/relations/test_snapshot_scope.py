"""Public snapshots: independent results, scope closure and dependency lifetime."""
from __future__ import annotations

import gc
import weakref
import ibis
import polars as pl
import pytest

import mountainash as ma
from fixtures.backend_registry import ALL_BACKENDS, REGISTRY
from mountainash.core.transit import BoundaryKey, capture_conversion_trace
from mountainash.core.types import BackendCapabilityError
from mountainash.relations.core.errors import MaterializationScopeClosedError
from mountainash.relations.backends.relation_systems.ibis._physical import adopt_connection, owned_transaction

pytest_plugins = ("fixtures.ibis_physical",)


@pytest.fixture
def checked_year():
    """A real source residue rule, shared by single/batch finishing witnesses."""
    from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry
    from mountainash.core.capabilities.applicability import unbounded
    from mountainash.core.capabilities.declarations import BoundSegment, CapabilityKey, CapabilityPolicyRule, CapabilitySegment, Domain
    from mountainash.core.capabilities.identity import Dialect, Scope
    from mountainash.core.capabilities.schema import PolicyAction, PolicyConsumer
    from mountainash.core.constants import CONST_BACKEND
    from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_DATETIME as FK
    from mountainash.typespec import FieldSpec, TypeSpec, UniversalType
    prior = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.reset()
        CapabilityRegistry.register_segment(BoundSegment(
            "mountainash.expressions.backends.capabilities.ibis.dialects.ibis_duckdb.extensions_mountainash.datetime",
            Scope(CONST_BACKEND.IBIS, Dialect("ibis-duckdb")),
            CapabilitySegment(Domain.DATETIME, policies=(CapabilityPolicyRule(
                key=CapabilityKey(FK.PARSE_XSD_PARTIAL_DATE, "*"), level=CapabilityLevel.UNSUPPORTED,
                message="year residue", consumer=PolicyConsumer.RESULT_PROTECTION,
                action=PolicyAction.DETECT_NON_NULL_TO_NULL, applicability=unbounded,
            ),)),
        ))
        with ma.capability_policy(ma.CapabilityPolicy.checked()):
            yield TypeSpec(fields_match="open", fields=[FieldSpec(name="year", type=UniversalType.YEAR)])
    finally:
        CapabilityRegistry.restore(prior)


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_scope_invalidates_escaped_relation_but_not_detached_relation(backend_name):
    source = REGISTRY[backend_name].build({"x": [7]}, "scope_source")
    with ma.materialization_scope() as scope:
        escaped = scope.snapshot(ma.relation(source)).filter(ma.col("x") > 0)
        keep = scope.detach(scope.snapshot(ma.relation(source)))
    with pytest.raises(MaterializationScopeClosedError):
        escaped.to_dicts()
    assert keep.to_dicts() == [{"x": 7}]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_snapshot_method_obeys_current_scope_and_nested_scopes(backend_name):
    rel = ma.relation(REGISTRY[backend_name].build({"x": [7]}, "nested"))
    independent = rel.snapshot()
    with ma.materialization_scope():
        first = rel.snapshot()
        with ma.materialization_scope():
            inner = rel.snapshot()
        with pytest.raises(MaterializationScopeClosedError):
            inner.compile()
        assert first.item("x") == 7
        last = rel.snapshot()
    for escaped in (first, last):
        with pytest.raises(MaterializationScopeClosedError):
            escaped.count_rows()
    assert independent.item("x") == 7


@pytest.mark.parametrize("policy,expected", [("every", 5), ("two", 2), ("never", 0)])
def test_checkpoint_frequency_and_skipped_self_replacement(policy, expected):
    """Polars witnesses the backend-independent stage counter."""
    policy = {"every": ma.CheckpointPolicy.EVERY_STAGE, "two": ma.CheckpointPolicy.every(2),
              "never": ma.CheckpointPolicy.NEVER}[policy]
    rel = ma.relation(pl.DataFrame({"x": [0]}))
    with capture_conversion_trace() as trace:
        with ma.materialization_scope(checkpoint=policy) as scope:
            for _ in range(5):
                rel = scope.checkpoint(rel.with_columns((ma.col("x") + 1).alias("x")), replaces=rel)
            assert rel.to_dicts() == [{"x": 5}]
    assert sum(r.boundary_key is BoundaryKey.OWNED_COPY for r in trace.records) == expected
    with ma.materialization_scope(checkpoint=ma.CheckpointPolicy.NEVER) as scope:
        same = scope.snapshot(ma.relation(pl.DataFrame({"x": [7]})))
        assert scope.checkpoint(same, replaces=same).item("x") == 7
    with pytest.raises(MaterializationScopeClosedError):
        same.item("x")


@pytest.mark.parametrize("interval", [0, -1, 1.5, True, "2"])
def test_invalid_checkpoint_interval(interval):
    with pytest.raises((ValueError, TypeError)):
        ma.CheckpointPolicy.every(interval)


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_detach_reaches_two_copies_through_union(backend_name):
    rel = ma.relation(REGISTRY[backend_name].build({"x": [7]}, "bundle"))
    with ma.materialization_scope() as scope:
        left = scope.snapshot(rel)
        right = scope.snapshot(rel)
        bundle = scope.detach(ma.concat([left, right]).filter(ma.col("x") > 0))
        with pytest.raises(ValueError):
            scope.detach(bundle)
        with pytest.raises(ValueError):
            scope.detach(rel)
    assert bundle.to_dicts() == [{"x": 7}, {"x": 7}]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_closed_snapshot_cannot_hide_behind_dag_ref(backend_name):
    rel = ma.relation(REGISTRY[backend_name].build({"x": [7]}, "dag_scope"))
    dag = ma.RelationDAG()
    with ma.materialization_scope() as scope:
        dag.add("saved", scope.snapshot(rel))
        kept = scope.detach(dag.ref("saved").snapshot())
        assert kept.item("x") == 7
    for terminal in ("compile", "to_dicts", "explain", "count_rows"):
        with pytest.raises(MaterializationScopeClosedError):
            getattr(dag.ref("saved").filter(ma.col("x") > 0), terminal)()
    assert kept.item("x") == 7


def test_checkpoint_replacement_keeps_sibling_and_bounds_linear_storage(connection):
    from mountainash.relations.core.owned_copy import drain_pending_drops
    with adopt_connection(connection) as backend:
        with owned_transaction(backend):
            backend.create_table("seed", ibis.memtable({"x": [0]}), temp=True)
            source = backend.table("seed")
    with ma.materialization_scope() as scope:
        rel = scope.snapshot(ma.relation(source))
        sibling = rel.filter(ma.col("x") == 0)
        rel = scope.checkpoint(rel.with_columns((ma.col("x") + 1).alias("x")), replaces=rel)
        assert sibling.item("x") == 0
        del sibling
        for _ in range(63):
            rel = scope.checkpoint(rel.with_columns((ma.col("x") + 1).alias("x")), replaces=rel)
            gc.collect()
            drain_pending_drops(connection)
            with adopt_connection(connection) as backend:
                with owned_transaction(backend):
                    assert len([n for n in backend.list_tables() if n.startswith("ma_owned_")]) <= 2
        assert rel.item("x") == 64


@pytest.mark.parametrize("backend_name", ["polars", "narwhals-polars", "ibis-duckdb", "ibis-polars"])
def test_snapshot_preserves_native_structured_restrictions_and_cuts_producer(backend_name, monkeypatch):
    """Native-array carriers; pandas object cells are explicitly unownable."""
    from mountainash.conform.errors import UnsupportedStructuredTransportUse
    from mountainash.typespec import FieldSpec, TypeSpec, UniversalType
    from mountainash.relations.core.relation_api.relation import Relation

    source = REGISTRY[backend_name].build({"id": [1], "payload": [[1, 2]]}, "structured_snapshot")
    rel = ma.relation(source).conform(TypeSpec(fields_match="open", fields=[
        FieldSpec(name="payload", type=UniversalType.ARRAY)]))
    refs = [weakref.ref(rel._node)]
    original = Relation._compile_and_execute_with_visitor

    def observe(self, *args, **kwargs):
        value, visitor = original(self, *args, **kwargs)
        refs.extend((weakref.ref(visitor), weakref.ref(visitor._execution_session)))
        return value, visitor

    with monkeypatch.context() as patch:
        patch.setattr(Relation, "_compile_and_execute_with_visitor", observe)
        saved = rel.snapshot()
    del rel, source
    gc.collect()
    assert all(ref() is None for ref in refs)
    renamed = saved.select("id", ma.col("payload").alias("body"))
    dag = ma.RelationDAG()
    dag.add("saved", renamed)
    dag.add("alias", dag.ref("saved"))
    for candidate, column in ((saved, "payload"), (renamed, "body"), (dag.ref("alias"), "body")):
        with pytest.raises(UnsupportedStructuredTransportUse):
            candidate.sort(column).compile()
        assert candidate.drop(column).to_dicts() == [{"id": 1}]
    again = saved.snapshot()
    assert ma.concat([saved, again]).to_dicts() == [
        {"id": 1, "payload": [1, 2]}, {"id": 1, "payload": [1, 2]},
    ]


@pytest.mark.parametrize("state", [True, None])
def test_snapshot_refuses_before_compilation_or_pending_cleanup(connection, monkeypatch, state):
    from mountainash_data import IbisBackend
    from mountainash.relations.core.owned_copy import owned_copy, drain_pending_drops
    from mountainash.relations.core.relation_api.relation import Relation
    with adopt_connection(connection) as backend:
        with owned_transaction(backend):
            backend.create_table("source", ibis.memtable({"x": [7]}), temp=True)
            source = backend.table("source")
    old = owned_copy(source)
    name = old.value.op().name
    del old
    gc.collect()

    def forbidden(*args, **kwargs):
        raise AssertionError("refused snapshot compiled its source")

    with monkeypatch.context() as patch:
        patch.setattr(IbisBackend, "native_transaction_open", lambda self: state)
        patch.setattr(Relation, "_compile_and_execute_with_visitor", forbidden)
        with pytest.raises(BackendCapabilityError):
            ma.relation(source).snapshot()
    with adopt_connection(connection) as backend:
        with owned_transaction(backend):
            assert name in backend.list_tables()
    drain_pending_drops(connection)


def test_snapshot_rechecks_state_after_compilation(connection, monkeypatch):
    from mountainash.relations.core.relation_api.relation import Relation
    with adopt_connection(connection) as backend:
        with owned_transaction(backend):
            backend.create_table("source", ibis.memtable({"x": [7]}), temp=True)
            source = backend.table("source")
    original = Relation._compile_and_execute_with_visitor

    def sql(text):
        if connection.name == "postgres":
            with connection.con.cursor() as cursor:
                cursor.execute(text)
        else:
            connection.con.execute(text)

    def begins(self, *args, **kwargs):
        result = original(self, *args, **kwargs)
        sql("BEGIN")
        return result

    monkeypatch.setattr(Relation, "_compile_and_execute_with_visitor", begins)
    try:
        with pytest.raises(BackendCapabilityError):
            ma.relation(source).snapshot()
        with adopt_connection(connection) as backend:
            assert backend.native_transaction_open() is True
    finally:
        sql("ROLLBACK")
    with adopt_connection(connection) as backend:
        with owned_transaction(backend):
            assert not any(n.startswith("ma_owned_") for n in backend.list_tables())


def test_body_error_survives_cleanup_error_and_retries(connection, monkeypatch):
    from mountainash_data import IbisBackend
    from mountainash.relations.core.owned_copy import drain_pending_drops
    with adopt_connection(connection) as backend:
        with owned_transaction(backend):
            backend.create_table("source", ibis.memtable({"x": [7]}), temp=True)
            source = backend.table("source")
    primary = RuntimeError("scope body")
    with monkeypatch.context() as patch:
        with pytest.raises(RuntimeError) as caught:
            with ma.materialization_scope() as scope:
                escaped = scope.snapshot(ma.relation(source))
                name = escaped._node.dataframe.op().name

                def fail(*args, **kwargs):
                    raise ValueError("drop failed")

                patch.setattr(IbisBackend, "drop_table", fail)
                raise primary
        assert caught.value is primary
        assert any("cleanup" in note for note in primary.__notes__)
        with pytest.raises(MaterializationScopeClosedError):
            escaped.compile()
    drain_pending_drops(connection)
    with adopt_connection(connection) as backend:
        with owned_transaction(backend):
            assert name not in backend.list_tables()


@pytest.mark.parametrize("year,valid", [("2024", True), ("bad", False)])
def test_snapshot_finishes_copied_value_and_preserves_user_marker(checked_year, year, valid):
    source = REGISTRY["ibis-duckdb"].build({
        "id": [1], "year": [year], "__ma_residue_conform_0_0": ["user"],
    }, "checked_source")
    connection = source._find_backend(use_default=False)
    rel = ma.relation(source).conform(checked_year)
    with ma.materialization_scope() as scope:
        if not valid:
            with pytest.raises(BackendCapabilityError):
                scope.snapshot(rel)
            assert not any(n.startswith("ma_owned_") for n in connection.list_tables())
        else:
            saved = scope.snapshot(rel)
            assert saved.to_dicts() == [{"id": 1, "year": "2024", "__ma_residue_conform_0_0": "user"}]
            connection.drop_table("checked_source")
            assert saved.select("id").to_dicts() == [{"id": 1}]
