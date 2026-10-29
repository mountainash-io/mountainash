"""Shared fixtures for relation tests."""

import pytest
import polars as pl
import pandas as pd
import pyarrow as pa


@pytest.fixture
def sample_data():
    return {
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "category": ["A", "B", "A", "C", "B"],
        "value": [100.5, 200.7, 300.9, 400.2, 500.8],
        "score": [85, 92, 78, 95, 88],
        "active": [True, False, True, True, False],
    }


@pytest.fixture
def polars_df(sample_data):
    return pl.DataFrame(sample_data)


@pytest.fixture
def pandas_df(sample_data):
    return pd.DataFrame(sample_data)


@pytest.fixture
def pyarrow_table(sample_data):
    return pa.table(sample_data)


@pytest.fixture
def checked_year():
    """Real source residue rule shared by snapshot and fingerprint terminals."""
    import mountainash as ma
    from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry
    from mountainash.core.capabilities.applicability import unbounded
    from mountainash.core.capabilities.declarations import BoundSegment, CapabilityKey, CapabilityPolicyRule, CapabilitySegment, Domain
    from mountainash.core.capabilities.identity import Dialect, Scope
    from mountainash.core.capabilities.schema import PolicyAction, PolicyConsumer
    from mountainash.core.constants import CONST_BACKEND
    from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_DATETIME as FK
    from mountainash.typespec import FieldDefinition, TableSchema, UniversalType
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
            yield TableSchema(fields_match="open", fields={"year": FieldDefinition(type=UniversalType.YEAR)})
    finally:
        CapabilityRegistry.restore(prior)


@pytest.fixture
def join_data():
    return {
        "id": [1, 2, 3],
        "label": ["x", "y", "z"],
    }


@pytest.fixture
def polars_join_df(join_data):
    return pl.DataFrame(join_data)


@pytest.fixture
def schema_resource_http_url(tmp_path):
    from functools import partial
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
    from threading import Thread

    class RangeHandler(SimpleHTTPRequestHandler):
        def end_headers(self):
            self.send_header("Accept-Ranges", "bytes")
            super().end_headers()

        def do_GET(self):
            requested = self.headers.get("Range")
            if requested is None:
                return super().do_GET()
            from pathlib import Path

            path = Path(self.translate_path(self.path))
            size = path.stat().st_size
            left, right = requested.removeprefix("bytes=").split("-")
            start = int(left) if left else max(0, size - int(right))
            end = min(int(right), size - 1) if left and right else size - 1
            if start >= size:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.end_headers()
                return
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.send_header("Content-Length", str(end - start + 1))
            self.end_headers()
            with path.open("rb") as stream:
                stream.seek(start)
                self.wfile.write(stream.read(end - start + 1))

    handler = partial(RangeHandler, directory=str(tmp_path))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/rows.csv"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
