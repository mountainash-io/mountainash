"""SQL-only adapter contracts: real connections, public upstream fault boundaries."""
from __future__ import annotations

import ibis
import pytest

from mountainash.core.types import BackendCapabilityError
from mountainash.relations.backends.relation_systems.ibis._physical import (
    adopt_connection,
    owned_transaction,
    require_idle,
)


@pytest.fixture(params=["sqlite", "duckdb"])
def connection(request):
    con = getattr(ibis, request.param).connect()
    try:
        yield con
    finally:
        con.disconnect()


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
