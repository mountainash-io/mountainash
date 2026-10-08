"""SQL-only adapter contracts: real connections, public upstream fault boundaries."""
from __future__ import annotations

from contextlib import contextmanager
import datetime as dt
import uuid

import ibis
import pytest
from mountainash_data import IbisBackend
from mountainash_data.core.errors import TransactionPoisonedError

import mountainash as ma
from mountainash.core.types import BackendCapabilityError
from mountainash.relations.backends.relation_systems.ibis._physical import (
    adopt_connection,
    drop_owned_tables,
    owned_transaction,
    require_idle,
)


pytest_plugins = ("fixtures.ibis_physical",)


def _name():
    return "ma_owned_" + uuid.uuid4().hex


def _caller_sql(connection, statement):
    """Simulate caller work on the test-owned driver, never in production."""
    if connection.name == "postgres":
        with connection.con.cursor() as cursor:
            cursor.execute(statement)
    else:
        connection.con.execute(statement)


@pytest.mark.parametrize("state", [True, None])
def test_unavailable_state_refuses_before_body(connection, monkeypatch, state):
    with adopt_connection(connection) as backend:
        monkeypatch.setattr(backend, "native_transaction_open", lambda: state)
        with pytest.raises(BackendCapabilityError):
            with owned_transaction(backend):
                pytest.fail("unavailable state admitted a physical operation")


def test_probe_error_preserves_cause(connection, monkeypatch):
    failure = RuntimeError("probe unavailable")

    def fail():
        raise failure

    with adopt_connection(connection) as backend:
        monkeypatch.setattr(backend, "native_transaction_open", fail)
        with pytest.raises(BackendCapabilityError) as caught:
            require_idle(backend)
    assert caught.value.__cause__ is failure


@pytest.mark.parametrize("body_fails", [False, True])
def test_nonowning_adoption_preserves_connection(connection, body_fails):
    failure = RuntimeError("body failed")
    try:
        with adopt_connection(connection) as backend:
            assert backend.raw_driver_connection() is connection.con
            with owned_transaction(backend):
                assert int(backend.run_expr(ibis.literal(7))) == 7
                if body_fails:
                    raise failure
    except RuntimeError as caught:
        assert body_fails and caught is failure
    # Re-adoption exercises the original caller connection after wrapper release.
    with adopt_connection(connection) as backend:
        with owned_transaction(backend):
            assert int(backend.run_expr(ibis.literal(8))) == 8


def test_inprocess_ibis_backend_is_not_a_sql_copy_route():
    con = ibis.polars.connect()
    try:
        with pytest.raises(BackendCapabilityError, match="unsupported SQL dialect"):
            with adopt_connection(con):
                pytest.fail("Ibis-Polars must keep its in-process copy route")
    finally:
        con.disconnect()


def test_committed_deletion_is_idempotent(connection):
    name = _name()
    with adopt_connection(connection) as b:
        with owned_transaction(b):
            b.create_table(name, ibis.memtable({"x": [7]}), temp=True)
    assert drop_owned_tables(connection, (name,)) is True
    assert drop_owned_tables(connection, (name,)) is True
    with adopt_connection(connection) as b:
        with owned_transaction(b):
            assert name not in b.list_tables()


@pytest.mark.parametrize("first_idle", [False, True], ids=["initial-observation", "final-observation"])
@pytest.mark.parametrize("unavailable", [True, None, "error"], ids=["active", "unknown", "failed-probe"])
def test_cleanup_unavailable_observation_defers(connection, monkeypatch, first_idle, unavailable):
    name = _name()
    with adopt_connection(connection) as b:
        with owned_transaction(b):
            b.create_table(name, ibis.memtable({"x": [7]}), temp=True)
    observations = iter(([False] if first_idle else []) + [unavailable])

    def observe(self):
        value = next(observations)
        if value == "error":
            raise RuntimeError("probe unavailable")
        return value

    with monkeypatch.context() as patch:
        patch.setattr(IbisBackend, "native_transaction_open", observe)
        assert drop_owned_tables(connection, (name,)) is False
    with adopt_connection(connection) as b:
        with owned_transaction(b):
            assert b.run_expr(b.table(name))["x"].tolist() == [7]
    assert drop_owned_tables(connection, (name,)) is True


def test_typed_copy_survives_source_mutation_and_deletion(connection):
    source, copy = _name(), _name()
    schema = ibis.schema({"id": "int64", "flag": "boolean", "day": "date", "value": "int64"})
    mem = ibis.memtable(
        {"id": [1, 2], "flag": [True, None], "day": [dt.date(2026, 10, 8), None], "value": [7, None]},
        schema=schema,
    )
    with adopt_connection(connection) as b:
        with owned_transaction(b):
            b.create_table(source, mem, temp=True)
            expr = ma.relation(b.table(source)).filter(ma.col("id") > 0).compile()
            b.create_table(copy, None, schema=expr.schema(), temp=True)
            b.insert(copy, expr)
            assert b.table(copy).schema() == schema
        with owned_transaction(b):
            _caller_sql(connection, f'UPDATE "{source}" SET value = 88 WHERE id = 1')
            b.drop_table(source)
            frame = b.run_expr(b.table(copy).order_by("id"))
            assert frame["id"].tolist() == [1, 2]
            assert frame["value"].iloc[0] == 7
            assert bool(frame["flag"].iloc[0]) is True
            assert frame["day"].iloc[0].date() == dt.date(2026, 10, 8)
            assert frame[["flag", "day", "value"]].isna().all(axis=1).tolist() == [False, True]
            assert b.table(copy).schema() == schema
    assert drop_owned_tables(connection, (copy,)) is True


@pytest.mark.parametrize("caught_inside", [False, True], ids=["propagated", "poisoned"])
def test_failed_batch_rolls_back_copies_and_source(connection, caught_inside):
    source, first, second, missing = (_name() for _ in range(4))
    operation_errors = []
    with adopt_connection(connection) as b:
        with owned_transaction(b):
            b.create_table(source, ibis.memtable({"x": [7]}), temp=True)
        with pytest.raises(Exception) as failure:
            with owned_transaction(b):
                expr = b.table(source)
                b.create_table(first, expr, temp=True)
                b.create_table(second, expr, temp=True)
                _caller_sql(connection, f'UPDATE "{source}" SET x = 99')
                try:
                    b.drop_table(missing)
                except Exception as exc:
                    operation_errors.append(exc)
                    if not caught_inside:
                        raise
        assert len(operation_errors) == 1
        if caught_inside:
            assert isinstance(failure.value, TransactionPoisonedError)
        else:
            assert failure.value is operation_errors[0]
        assert b.native_transaction_open() is False
        with owned_transaction(b):
            assert b.run_expr(b.table(source))["x"].tolist() == [7]
            tables = b.list_tables()
            assert first not in tables and second not in tables
    assert drop_owned_tables(connection, (source, first, second)) is True


@pytest.mark.parametrize("completion,expected", [("COMMIT", 88), ("ROLLBACK", 7)])
def test_caller_transaction_is_refused_without_ending_it(connection, completion, expected):
    source = _name()
    with adopt_connection(connection) as b:
        with owned_transaction(b):
            b.create_table(source, ibis.memtable({"x": [7]}), temp=True)
        _caller_sql(connection, "BEGIN")
        _caller_sql(connection, f'UPDATE "{source}" SET x = 88')
        with pytest.raises(BackendCapabilityError):
            with owned_transaction(b):
                pytest.fail("caller transaction admitted")
        assert drop_owned_tables(connection, (source,)) is False
        assert b.native_transaction_open() is True
        _caller_sql(connection, completion)
        assert b.native_transaction_open() is False
        with owned_transaction(b):
            assert b.run_expr(b.table(source))["x"].tolist() == [expected]
    assert drop_owned_tables(connection, (source,)) is True


@pytest.mark.parametrize("caller_fails", [False, True], ids=["commit", "rollback"])
def test_cleanup_defers_inside_caller_public_transaction(connection, caller_fails):
    name = _name()
    caller_error = RuntimeError("caller chooses rollback")
    owner = IbisBackend.from_ibis_connection(connection, dialect=connection.name, owns_connection=False)
    try:
        with owner.transaction():
            owner.create_table(name, ibis.memtable({"x": [7]}), temp=True)
        try:
            with owner.transaction():
                _caller_sql(connection, f'UPDATE "{name}" SET x = 88')
                assert drop_owned_tables(connection, (name,)) is False
                assert owner.in_transaction() and owner.native_transaction_open() is True
                with adopt_connection(connection) as borrowed:
                    with pytest.raises(BackendCapabilityError):
                        with owned_transaction(borrowed):
                            pytest.fail("caller public transaction admitted")
                assert owner.run_expr(owner.table(name))["x"].tolist() == [88]
                if caller_fails:
                    raise caller_error
        except RuntimeError as exc:
            assert caller_fails and exc is caller_error
        with owner.transaction():
            assert owner.run_expr(owner.table(name))["x"].tolist() == [7 if caller_fails else 88]
        assert drop_owned_tables(connection, (name,)) is True
        with owner.transaction():
            assert name not in owner.list_tables()
    finally:
        owner.close()


def test_commit_ack_failure_propagates_without_replaying(connection, monkeypatch):
    name = _name()
    failure = RuntimeError("commit acknowledgement lost")
    evaluated = []
    with adopt_connection(connection) as b:
        real_transaction = b.transaction

        @contextmanager
        def failed_ack(*, required=True):
            with real_transaction(required=required):
                yield
            raise failure

        with monkeypatch.context() as patch:
            patch.setattr(b, "transaction", failed_ack)
            with pytest.raises(RuntimeError) as caught:
                with owned_transaction(b):
                    evaluated.append(True)
                    b.create_table(name, ibis.memtable({"x": [7]}), temp=True)
            assert caught.value is failure
        assert evaluated == [True]
        with owned_transaction(b):
            assert b.run_expr(b.table(name))["x"].tolist() == [7]
    assert drop_owned_tables(connection, (name,)) is True


def test_rollback_and_wrapper_release_errors_do_not_replace_body(connection, monkeypatch):
    body_error = RuntimeError("body failed")
    rollback_error = RuntimeError("rollback failed")
    combined = ExceptionGroup("body and rollback failures", [body_error, rollback_error])
    with pytest.raises(ExceptionGroup) as caught:
        with adopt_connection(connection) as b:
            real_transaction, real_close = b.transaction, b.close

            @contextmanager
            def failed_rollback(*, required=True):
                try:
                    with real_transaction(required=required):
                        yield
                except RuntimeError as exc:
                    assert exc is body_error
                    raise combined

            def failed_close():
                real_close()
                raise RuntimeError("wrapper release failed")

            monkeypatch.setattr(b, "transaction", failed_rollback)
            monkeypatch.setattr(b, "close", failed_close)
            with owned_transaction(b):
                raise body_error
    assert caught.value is combined
    assert caught.value.exceptions == (body_error, rollback_error)
    assert any("wrapper release failed" in note.lower() for note in caught.value.__notes__)
    with adopt_connection(connection) as b:
        with owned_transaction(b):
            assert int(b.run_expr(ibis.literal(7))) == 7


@pytest.mark.parametrize("failure_phase", ["drop", "completion"])
def test_cleanup_failure_is_not_acknowledged_and_can_retry(connection, monkeypatch, failure_phase):
    name = _name()
    with adopt_connection(connection) as b:
        with owned_transaction(b):
            b.create_table(name, ibis.memtable({"x": [7]}), temp=True)
    failure = BackendCapabilityError(
        "physical failure", backend=f"ibis-{connection.name}", function_key="OWNED_COPY",
    )
    real_transaction = IbisBackend.transaction

    @contextmanager
    def failed_completion(self, *, required=True):
        with real_transaction(self, required=required):
            yield
        raise failure

    def failed_drop(self, name, *, force=False):
        raise failure

    with monkeypatch.context() as patch:
        if failure_phase == "drop":
            patch.setattr(IbisBackend, "drop_table", failed_drop)
        else:
            patch.setattr(IbisBackend, "transaction", failed_completion)
        with pytest.raises(BackendCapabilityError) as caught:
            drop_owned_tables(connection, (name,))
        assert caught.value is failure
    assert drop_owned_tables(connection, (name,)) is True
    with adopt_connection(connection) as b:
        with owned_transaction(b):
            assert name not in b.list_tables()
