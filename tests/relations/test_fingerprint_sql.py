"""Physical SQL sessions own transaction and stream-failure qualification."""
from __future__ import annotations

import uuid
import datetime as dt
from decimal import Decimal

import ibis
import polars as pl
import pytest

import mountainash as ma
from mountainash.core.backend_detection import identify_backend_identity
from mountainash.core.types import BackendCapabilityError
from mountainash.relations.core.batch_materialization import consume_native_batches

pytest_plugins = ("fixtures.ibis_physical",)


def test_sql_selection_and_caller_rollback(connection):
    if connection.name != "duckdb":
        source = connection.sql("SELECT 1 AS k, 7 AS v")
        with pytest.raises(BackendCapabilityError, match="bounded"):
            ma.relation(source).fingerprint(keys=["k"], columns=["v"])
        return
    name = "fp_" + uuid.uuid4().hex
    driver = connection.con
    driver.execute(f"CREATE TEMP TABLE {name} (a BIGINT, b BIGINT, v BIGINT, ignored BIGINT)")
    driver.execute(f"INSERT INTO {name} VALUES (42,101,7,0),(42,102,8,0),(43,101,9,0)")
    source = connection.sql(f"SELECT * FROM {name}", schema={"a": "int64", "b": "int64", "v": "int64", "ignored": "int64"})
    rel = ma.relation(source).filter(ma.col("a") == 42)
    base = rel.fingerprint(keys=["a", "b"], columns=["v"], batch_size=1)
    expected = ma.relation(pl.DataFrame({"a": [42,42], "b": [101,102], "v": [7,8]})).fingerprint(keys=["a", "b"], columns=["v"])
    assert base.equals(expected)
    driver.execute("BEGIN")
    try:
        driver.execute(f"UPDATE {name} SET ignored=99")
        driver.execute(f"UPDATE {name} SET v=99 WHERE a=43")
        assert rel.fingerprint(keys=["a", "b"], columns=["v"]).equals(base)
        driver.execute(f"UPDATE {name} SET v=88 WHERE a=42 AND b=101")
        changed = rel.fingerprint(keys=["a", "b"], columns=["v"])
        assert changed.row(0) == base.row(0)
        assert changed.row(1) != base.row(1)
        driver.execute(f"INSERT INTO {name} SELECT * FROM {name} WHERE a=42 AND b=101")
        assert rel.fingerprint(keys=["a", "b"], columns=["v"])["row_count"].to_list() == [3, 3]
    finally:
        driver.execute("ROLLBACK")
    assert rel.fingerprint(keys=["a", "b"], columns=["v"]).equals(base)


@pytest.fixture
def duckdb_connection():
    con = ibis.duckdb.connect()
    try:
        yield con
    finally:
        con.disconnect()


def test_early_consumer_failure_preserves_caller_work(duckdb_connection):
    connection = duckdb_connection
    driver = connection.con
    name = "fp_marker_" + uuid.uuid4().hex
    driver.execute(f"CREATE TEMP TABLE {name} (k BIGINT)")
    driver.execute("BEGIN")
    driver.execute(f"INSERT INTO {name} VALUES (7)")
    source = connection.sql("SELECT i::bigint AS k, i::bigint AS v FROM generate_series(1,20000) AS s(i)", schema={"k": "int64", "v": "int64"})
    sizes = []
    original = ValueError("consumer failed after a successful prefix")
    def fail(batch):
        sizes.append(batch.height)
        if len(sizes) == 2:
            raise original
    try:
        with pytest.raises(ValueError) as caught:
            consume_native_batches(source, compiler_identity=identify_backend_identity(source),
                                   batch_size=5000, on_schema=lambda schema: None, on_batch=fail)
        assert caught.value is original
        assert sizes == [5000, 5000]
        assert driver.execute(f"SELECT k FROM {name}").fetchall() == [(7,)]
    finally:
        driver.execute("ROLLBACK")
    assert driver.execute(f"SELECT k FROM {name}").fetchall() == []


@pytest.mark.parametrize("empty", [False, True])
def test_duckdb_typed_values_match_native_polars(duckdb_connection, empty):
    """SQL transport fidelity owns this fixture; profile tests own local hashing."""
    frame = pl.DataFrame({
        "k": [1, 2, 3],
        "amount": pl.Series([Decimal("123456789012345678901234.01"), None, Decimal("0.00")], dtype=pl.Decimal(38, 2)),
        "clock": pl.Series([dt.time(1, 2, 3, 456789), None, dt.time(0)], dtype=pl.Time),
        "instant": pl.Series([dt.datetime(2026, 1, 1), None, dt.datetime(2026, 1, 2)], dtype=pl.Datetime("us")),
        "items": pl.Series([[float("nan"), -0.0, None], [], None], dtype=pl.List(pl.Float64)),
        "record": pl.Series([{"x": [0.0, float("nan")], "s": "é"}, None, {"x": [], "s": ""}],
                            dtype=pl.Struct({"x": pl.List(pl.Float64), "s": pl.String})),
    })
    native = duckdb_connection.create_table("typed_fingerprint", frame.to_arrow(), temp=True)
    values = frame.columns[1:]
    def calculate(source):
        rel = ma.relation(source)
        if empty:
            rel = rel.filter(ma.col("k") < 0)
        return rel.fingerprint(keys=["k"], columns=values, batch_size=1)
    assert calculate(native).equals(calculate(frame))
