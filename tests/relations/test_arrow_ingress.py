"""Public ingestion fidelity and ownership for the two qualified targets.

These exercise source ingestion, not new expression semantics. Native Arrow
inspection avoids coupling ingress qualification to Mountainash's export path.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
import gc
import importlib

import ibis
import polars as pl
import pyarrow as pa
import pytest

import mountainash as ma
from mountainash.core.types import BackendCapabilityError
from mountainash.relations.backends.relation_systems.ibis._physical import adopt_connection
from mountainash.relations.core.owned_copy import drain_pending_drops


def arrow_sample():
    schema = pa.schema([
        ("id", pa.int64()), ("money", pa.decimal128(18, 2)),
        ("day", pa.date32()), ("truth", pa.int8()),
        ("labels", pa.list_(pa.string())),
        ("amounts", pa.list_(pa.decimal128(18, 2))),
        ("meta", pa.string()), ("all_null_meta", pa.string()),
        ("stamp", pa.timestamp("us")),
    ])
    return pa.Table.from_pylist([
        dict(id=1, money=Decimal("12.30"), day=date(2026, 10, 21),
             truth=-1, labels=["x", None], amounts=[Decimal("1.20"), None],
             meta=None, all_null_meta=None, stamp=datetime(2026, 10, 21)),
        dict(id=2, money=None, day=None, truth=0, labels=[], amounts=[],
             meta="m", all_null_meta=None, stamp=None),
        dict(id=3, money=Decimal("-2.50"), day=date(2026, 1, 1),
             truth=1, labels=None, amounts=None, meta="", all_null_meta=None,
             stamp=datetime(2026, 1, 1)),
    ], schema=schema)


@pytest.fixture
def connection():
    con = ibis.duckdb.connect()
    try:
        yield con
    finally:
        gc.collect()
        drain_pending_drops(con)
        con.disconnect()


@pytest.fixture(params=["polars", "ibis-duckdb"])
def target(request):
    return None if request.param == "polars" else request.getfixturevalue("connection")


def native_arrow(rel, con):
    native = rel.compile()
    if con is None:
        return native.collect().to_arrow()
    assert native.get_backend() is con
    return native.to_pyarrow()


def expected_schema(source, con):
    if con is not None:
        return source.schema
    replacements = {
        "labels": pa.large_list(pa.large_string()),
        "amounts": pa.large_list(pa.decimal128(18, 2)),
        "meta": pa.large_string(), "all_null_meta": pa.large_string(),
    }
    return pa.schema([
        pa.field(f.name, replacements.get(f.name, f.type)) for f in source.schema
    ])


@pytest.mark.parametrize("empty", [False, True])
def test_public_arrow_ingestion_fidelity(target, empty, monkeypatch):
    source = arrow_sample()
    if empty:
        source = source.slice(0, 0)
    if target is not None:
        def forbidden(*args, **kwargs):
            raise AssertionError("Ibis ingestion used Polars")
        monkeypatch.setattr(pl, "from_arrow", forbidden)
        monkeypatch.setattr(pl.DataFrame, "__init__", forbidden)
    rel = ma.from_arrow(source, target=target)
    expected = source.to_pylist()
    physical_schema = expected_schema(source, target)
    for _ in range(2):
        actual = native_arrow(rel, target)
        assert actual.schema == physical_schema
        assert actual.to_pylist() == expected
    projected = rel.select("id", "money").sort("id")
    assert native_arrow(projected, target).to_pylist() == [
        {"id": row["id"], "money": row["money"]} for row in expected
    ]


def caller_sentinel(con):
    con.raw_sql("CREATE TEMP TABLE caller_kept AS SELECT 42 AS marker")
    return set(con.list_tables())


@pytest.mark.parametrize("owner_kind", ["relation", "native"])
def test_ingested_data_survives_input_and_initial_owner(target, owner_kind):
    baseline = caller_sentinel(target) if target is not None else None
    source = arrow_sample()
    expected = source.select(["id", "money"]).to_pylist()
    rel = ma.from_arrow(source, target=target)
    if target is not None:
        imported_catalogue = set(target.list_tables())
        assert len(imported_catalogue - baseline) == 1
    derived = rel.select("id", "money").sort("id")
    held = derived if owner_kind == "relation" else derived.compile()
    del source, rel, derived
    gc.collect()
    if target is not None:
        drain_pending_drops(target)
    for _ in range(2):
        native = held.compile() if owner_kind == "relation" else held
        if target is None:
            actual = native.collect().to_arrow()
        else:
            assert native.get_backend() is target
            actual = native.to_pyarrow()
            assert set(target.list_tables()) == imported_catalogue
        assert actual.to_pylist() == expected
        del native
    del held
    gc.collect()
    if target is not None:
        drain_pending_drops(target)
        assert set(target.list_tables()) == baseline
        assert target.table("caller_kept").to_pyarrow().to_pylist() == [{"marker": 42}]


def test_ingestion_preserves_caller_transaction(connection):
    connection.raw_sql("CREATE TEMP TABLE caller_tx (marker INTEGER)")
    connection.raw_sql("BEGIN TRANSACTION")
    try:
        connection.raw_sql("INSERT INTO caller_tx VALUES (7)")
        with pytest.raises(BackendCapabilityError):
            ma.from_arrow(arrow_sample(), target=connection)
        assert connection.table("caller_tx").to_pyarrow().to_pylist() == [{"marker": 7}]
    finally:
        connection.raw_sql("ROLLBACK")
    assert connection.table("caller_tx").to_pyarrow().to_pylist() == []


@pytest.mark.parametrize("stage", ["creation", "registration", "publication"])
def test_failed_ingestion_releases_only_imported_storage(connection, monkeypatch, stage):
    baseline = caller_sentinel(connection)
    failure = RuntimeError("injected import failure")

    def fail(*args, **kwargs):
        raise failure

    with monkeypatch.context() as patch:
        if stage == "creation":
            with adopt_connection(connection) as backend:
                adapter_type = type(backend)
            create = adapter_type.create_table

            def create_then_fail(self, *args, **kwargs):
                create(self, *args, **kwargs)
                raise failure

            patch.setattr(adapter_type, "create_table", create_then_fail)
        elif stage == "registration":
            module = importlib.import_module("mountainash.relations.core.owned_copy")
            patch.setattr(module, "register_owned_ibis_table", fail)
        else:
            module = importlib.import_module("mountainash.relations.core.relation_api.relation")
            patch.setattr(module, "relation", fail)
        with pytest.raises(RuntimeError) as caught:
            ma.from_arrow(arrow_sample(), target=connection)
        assert caught.value is failure
    gc.collect()
    drain_pending_drops(connection)
    assert set(connection.list_tables()) == baseline
    assert connection.table("caller_kept").to_pyarrow().to_pylist() == [{"marker": 42}]
