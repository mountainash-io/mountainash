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
@pytest.mark.parametrize("batch", [False, True])
def test_snapshot_preserves_native_structured_restrictions_and_cuts_producer(backend_name, monkeypatch, batch):
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
        if batch:
            with ma.materialization_scope() as scope:
                saved, sibling = scope.capture(rel, rel.select("id"))
                saved = scope.detach(saved)
            del sibling
        else:
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


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_capture_empty_single_batch_and_detached_bundle(backend_name):
    rel = ma.relation(REGISTRY[backend_name].build({"x": [7]}, "capture_source"))
    with capture_conversion_trace() as trace:
        with ma.materialization_scope() as scope:
            assert scope.capture() == ()
            single, = scope.capture(rel)
            copies = scope.capture(rel, rel, rel, rel.head(0))
            assert single.to_dicts() == [{"x": 7}]
            assert copies[-1].schema == copies[0].schema
            saved = scope.detach(ma.concat(copies))
    assert sum(r.boundary_key is BoundaryKey.OWNED_COPY for r in trace.records) == 5
    assert saved.to_dicts() == [{"x": 7}, {"x": 7}, {"x": 7}]


@pytest.mark.parametrize("failure_at", ["insert", "bind", "completion"])
def test_capture_failure_publishes_nothing_and_never_replays_source(connection, monkeypatch, failure_at):
    from contextlib import contextmanager
    from mountainash_data import IbisBackend
    from mountainash.relations.core.owned_copy import drain_pending_drops
    with adopt_connection(connection) as backend:
        with owned_transaction(backend):
            backend.create_table("source", ibis.memtable({"x": [7]}), temp=True)
            source = backend.table("source")
    rel = ma.relation(source)
    insert, table, transaction = IbisBackend.insert, IbisBackend.table, IbisBackend.transaction
    calls = []
    failure = RuntimeError("batch failed")

    def insert_failure(self, name, *args, **kwargs):
        if name.startswith("ma_owned_"):
            calls.append(name)
            if len(calls) == 2 and failure_at == "insert":
                raise failure
        return insert(self, name, *args, **kwargs)

    def bind_failure(self, name, *args, **kwargs):
        if name.startswith("ma_owned_") and len(calls) == 2 and failure_at == "bind":
            raise failure
        return table(self, name, *args, **kwargs)

    @contextmanager
    def completion_failure(self, *args, **kwargs):
        with transaction(self, *args, **kwargs) as current:
            yield current
        if len(calls) == 2 and failure_at == "completion":
            raise failure

    with ma.materialization_scope() as scope:
        prior = scope.snapshot(rel)
        with monkeypatch.context() as patch:
            patch.setattr(IbisBackend, "insert", insert_failure)
            patch.setattr(IbisBackend, "table", bind_failure)
            patch.setattr(IbisBackend, "transaction", completion_failure)
            with pytest.raises(RuntimeError) as caught:
                scope.capture(rel, rel)
            assert caught.value is failure
        drain_pending_drops(connection)
        assert len(calls) == 2
        with adopt_connection(connection) as backend:
            with owned_transaction(backend):
                assert not set(calls) & set(backend.list_tables())
                assert backend.run_expr(prior._node.dataframe)["x"].tolist() == [7]
        keep = scope.detach(prior)
    assert keep is prior


def test_capture_finishing_failure_preserves_earlier_scope_holdings(checked_year):
    connection = ibis.duckdb.connect()
    try:
        good = connection.create_table("good", {"id": [1], "year": ["2024"]})
        bad = connection.create_table("bad", {"id": [2], "year": ["bad"]})
        with ma.materialization_scope() as scope:
            prior = scope.snapshot(ma.relation(good))
            before = set(connection.list_tables())
            with pytest.raises(BackendCapabilityError):
                scope.capture(ma.relation(good).conform(checked_year), ma.relation(bad).conform(checked_year))
            assert set(connection.list_tables()) == before
            assert prior.item("id") == 1
    finally:
        connection.disconnect()


def test_capture_refuses_mixed_connections_and_unbound_parameters_before_effects():
    left = REGISTRY["ibis-duckdb"].build({"x": [7]}, "capture_left")
    right = REGISTRY["ibis-sqlite"].build({"x": [8]}, "capture_right")
    with ma.materialization_scope() as scope:
        with pytest.raises(BackendCapabilityError):
            scope.capture(ma.relation(left), ma.relation(right))
        parameterized = left.filter(left.x > ibis.param("int64"))
        with pytest.raises(BackendCapabilityError):
            scope.capture(ma.relation(left), ma.relation(parameterized))
    for table in (left, right):
        assert not any(n.startswith("ma_owned_") for n in table._find_backend(use_default=False).list_tables())


def test_inprocess_failed_second_copy_leaves_no_partial_ownership():
    import pandas as pd
    good = ma.relation(pd.DataFrame({"x": [7]}))
    bad = ma.relation(pd.DataFrame({"x": [[7]]}))
    with ma.materialization_scope() as scope:
        prior = scope.snapshot(good)
        with pytest.raises(TypeError):
            scope.capture(good, bad)
        assert scope.detach(prior).item("x") == 7


@pytest.mark.parametrize("backend_name", ["ibis-duckdb", "ibis-sqlite", "ibis-polars"])
def test_recognized_native_alias_retains_physical_table(backend_name):
    from mountainash.relations.core.owned_copy import drain_pending_drops
    source = REGISTRY[backend_name].build({"x": [7]}, "alias_source")
    connection = source._find_backend(use_default=False)
    saved = ma.relation(source).snapshot()
    name = saved.compile().op().name
    alias = ma.relation(connection.table(name)).filter(ma.col("x") > 0)
    assert alias.to_dicts() == [{"x": 7}]
    del saved
    gc.collect()
    drain_pending_drops(connection)
    assert alias.to_dicts() == [{"x": 7}]
    del alias
    gc.collect()
    drain_pending_drops(connection)
    assert name not in connection.list_tables()


def test_capture_typed_revisions_survive_source_deletion(connection, monkeypatch):
    from datetime import date
    from mountainash_data import IbisBackend
    schema = ibis.schema({"id": "int64", "flag": "boolean", "day": "date", "x": "int64"})
    initial = {"id": [1, 2], "flag": [True, None], "day": [date(2026, 10, 8), None], "x": [7, None]}
    later = {"id": [1, 2], "flag": [False, None], "day": [date(2026, 10, 9), None], "x": [88, None]}
    with adopt_connection(connection) as backend:
        with owned_transaction(backend):
            backend.create_table("typed_source", ibis.memtable(initial, schema=schema), temp=True)
            source = backend.table("typed_source")
    memory = ibis.memtable({"id": [3], "flag": [False], "day": [None], "x": [5]}, schema=schema)
    rel = ma.concat([ma.relation(source), ma.relation(memory)]).with_columns(
        (ma.col("x") + 1).alias("computed"))
    insert = IbisBackend.insert
    evaluated = []

    def record(self, name, *args, **kwargs):
        if name.startswith("ma_owned_"):
            evaluated.append(name)
        return insert(self, name, *args, **kwargs)

    monkeypatch.setattr(IbisBackend, "insert", record)
    with ma.materialization_scope() as scope:
        first, empty = scope.capture(rel, rel.head(0))
        with adopt_connection(connection) as backend:
            with owned_transaction(backend):
                backend.drop_table("typed_source")
                backend.create_table("typed_source", ibis.memtable(later, schema=schema), temp=True)
        second, = scope.capture(rel)
        with adopt_connection(connection) as backend:
            with owned_transaction(backend):
                backend.drop_table("typed_source")
        assert first.sort("id").to_dicts() == [
            {"id": 1, "flag": True, "day": date(2026, 10, 8), "x": 7, "computed": 8},
            {"id": 2, "flag": None, "day": None, "x": None, "computed": None},
            {"id": 3, "flag": False, "day": None, "x": 5, "computed": 6},
        ]
        assert second.filter(ma.col("id") == 1).item("computed") == 89
        assert empty.to_dicts() == []
        assert empty.schema == first.schema == second.schema
        assert len(evaluated) == 3


def test_capture_executes_each_inprocess_lazy_source_once():
    """Polars map_batches runs at physical evaluation, unlike a wrapper spy."""
    calls = []

    def evaluated(frame):
        calls.append(frame["x"].to_list())
        return frame

    source = pl.DataFrame({"x": [7]}).lazy().map_batches(evaluated, schema={"x": pl.Int64})
    with ma.materialization_scope() as scope:
        left, right = scope.capture(ma.relation(source), ma.relation(source))
        assert calls == [[7], [7]]
        assert left.to_dicts() == right.to_dicts() == [{"x": 7}]
        assert calls == [[7], [7]]


def test_capture_registration_failure_restores_previous_holdings(connection, monkeypatch):
    from mountainash.relations.core.materialization import MaterializationScope
    with adopt_connection(connection) as backend:
        with owned_transaction(backend):
            backend.create_table("registration_source", ibis.memtable({"x": [7]}), temp=True)
            source = backend.table("registration_source")
    rel = ma.relation(source)
    original = MaterializationScope.own
    registered = []
    failure = RuntimeError("registration failed after accepting owner")

    def fail_second(self, release, *, owner=None):
        original(self, release, owner=owner)
        registered.append(owner)
        if len(registered) == 2:
            raise failure

    with ma.materialization_scope() as scope:
        prior = scope.snapshot(rel)
        with adopt_connection(connection) as backend:
            with owned_transaction(backend):
                before = set(backend.list_tables())
        with monkeypatch.context() as patch:
            patch.setattr(MaterializationScope, "own", fail_second)
            with pytest.raises(RuntimeError) as caught:
                scope.capture(rel, rel)
            assert caught.value is failure
        with adopt_connection(connection) as backend:
            with owned_transaction(backend):
                assert set(backend.list_tables()) == before
        assert scope.detach(prior).item("x") == 7
    assert prior.item("x") == 7


def test_capture_failed_rollback_keeps_pending_ownership(connection, monkeypatch):
    from contextlib import contextmanager
    from mountainash_data import IbisBackend
    from mountainash.relations.core.owned_copy import drain_pending_drops
    with adopt_connection(connection) as backend:
        with owned_transaction(backend):
            backend.create_table("rollback_source", ibis.memtable({"x": [7]}), temp=True)
            source = backend.table("rollback_source")
    transaction, insert = IbisBackend.transaction, IbisBackend.insert
    failure = RuntimeError("second source failed")
    rollback_failure = RuntimeError("rollback unavailable")
    combined = ExceptionGroup("body and rollback", [failure, rollback_failure])
    attempted, held = [], []

    def fail_second(self, name, *args, **kwargs):
        if name.startswith("ma_owned_"):
            attempted.append(name)
            if len(attempted) == 2:
                raise failure
        return insert(self, name, *args, **kwargs)

    @contextmanager
    def leave_active(self, **kwargs):
        manager = transaction(self, **kwargs)
        manager.__enter__()
        held.append(manager)
        try:
            yield
        except RuntimeError as error:
            assert error is failure
            raise combined
        else:
            manager.__exit__(None, None, None)

    try:
        with monkeypatch.context() as patch:
            patch.setattr(IbisBackend, "transaction", leave_active)
            patch.setattr(IbisBackend, "insert", fail_second)
            with ma.materialization_scope() as scope:
                with pytest.raises(ExceptionGroup) as caught:
                    scope.capture(ma.relation(source), ma.relation(source))
                assert caught.value is combined
            with adopt_connection(connection) as backend:
                assert backend.native_transaction_open() is True
    finally:
        for manager in held:
            manager.__exit__(type(failure), failure, failure.__traceback__)
    dropped = []
    drop = IbisBackend.drop_table

    def record_drop(self, name, **kwargs):
        dropped.append(name)
        return drop(self, name, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(IbisBackend, "drop_table", record_drop)
        drain_pending_drops(connection)
    assert set(attempted) <= set(dropped)
    assert len(attempted) == 2
    with adopt_connection(connection) as backend:
        with owned_transaction(backend):
            assert not set(attempted) & set(backend.list_tables())
