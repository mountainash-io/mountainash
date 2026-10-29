"""A native read's eligibility is engine state and can change after preparation.

Another read on the shared DuckDB database may add a caller secret (here an HTTP
secret, so the source is no longer anonymous) between preparation and the read.
The reader then takes its faithful fallback; the borrowed result must still get the
anchor preparation plans for any borrowed leaf, exactly as when the secret already
existed at preparation.
"""

import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import ibis
import pytest

import mountainash as ma
from mountainash.relations.core.errors import CompileRequiresExecutionError
from mountainash.relations.core.execution.compilation import CompilationSession
from mountainash.relations.core.execution.preparation import ExecutionPhase, prepare_execution

CALLER_HTTP_SECRET = (
    "CREATE SECRET caller_http (TYPE http, EXTRA_HTTP_HEADERS MAP {'X-Caller': '1'}, "
    "SCOPE 'http://127.0.0.1')"
)


@pytest.fixture
def connection():
    con = ibis.duckdb.connect()
    try:
        con.raw_sql("INSTALL httpfs")
        con.raw_sql("LOAD httpfs")
        yield con
    finally:
        con.disconnect()


@pytest.fixture
def remote_rows(tmp_path, schema_resource_http_url):
    (tmp_path / "rows.csv").write_text("v\n11\n12\n")
    return ma.ResourceRef(
        ma.DataResource(name="rows", path=schema_resource_http_url, format="csv")
    ).relation()


@pytest.fixture
def counted_remote_rows(tmp_path):
    requests = []

    class Handler(SimpleHTTPRequestHandler):
        def log_request(self, *args):
            requests.append(self.path)

    (tmp_path / "rows.csv").write_text("v\n11\n12\n")
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, directory=str(tmp_path)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield ma.ResourceRef(ma.DataResource(
            name="rows", path=f"http://127.0.0.1:{server.server_port}/rows.csv", format="csv",
        )).relation(), requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def _owned(prepared):
    return [key for key, requirement in prepared.transfers.items() if requirement.owned]


def test_native_route_lost_after_preparation_keeps_the_anchor_on_the_selected_connection(
    connection, remote_rows,
):
    prepared = prepare_execution(remote_rows._node, phase=ExecutionPhase.EXECUTE, target=connection)
    assert prepared.locations["root"].binding == "bound"
    assert _owned(prepared) == []

    connection.raw_sql(CALLER_HTTP_SECRET)
    session = CompilationSession(prepared)
    try:
        envelope, _ = session.compile_root()
        value = envelope.value
        assert _owned(prepared) == ["root"]
        assert value._find_backend(use_default=False) is connection
        assert value.to_pyarrow().to_pylist() == [{"v": 11}, {"v": 12}]
    finally:
        session.close(release_owned=True)


def test_native_route_lost_after_compile_preparation_requires_execution_before_any_read(
    connection, counted_remote_rows,
):
    relation, requests = counted_remote_rows
    prepared = prepare_execution(relation._node, phase=ExecutionPhase.COMPILE, target=connection)

    connection.raw_sql(CALLER_HTTP_SECRET)
    with pytest.raises(CompileRequiresExecutionError):
        CompilationSession(prepared).compile_root()
    assert requests == []
