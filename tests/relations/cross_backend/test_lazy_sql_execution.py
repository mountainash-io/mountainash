"""Public phase and result regressions for deferred Ibis SQL operations."""

from __future__ import annotations

import ibis
import pytest

import mountainash as ma


_SQLITE_ROWS = [(1, 10), (2, 20), (3, 30), (4, 40)]


def _observed_duckdb_relation(reads: list[int], *, rows: int = 4):
    """Create a lazy native source whose side-effecting UDF records reads."""
    import duckdb

    conn = ibis.duckdb.connect()
    conn.con.create_function(
        "ma_observe_lazy_sql", lambda value: (reads.append(value) or value),
        [duckdb.sqltypes.BIGINT], duckdb.sqltypes.BIGINT, side_effects=True,
    )
    table = conn.sql(
        f"SELECT ma_observe_lazy_sql(i) AS id, "
        f"ma_observe_lazy_sql(i * 10) AS paired FROM range(1, {rows + 1}) t(i)"
    )
    return conn, table


def _sqlite_relation(table_name: str, rows: list[tuple[int, int]]):
    conn = ibis.sqlite.connect(":memory:")
    conn.con.execute(f"CREATE TABLE {table_name} (id INTEGER, paired INTEGER)")
    conn.con.executemany(f"INSERT INTO {table_name} VALUES (?, ?)", rows)
    table = conn.table(table_name)
    table.schema()
    reads: list[str] = []
    conn.con.set_trace_callback(
        lambda sql: reads.append(sql)
        if table_name.lower() in sql.lower() and sql.lstrip().lower().startswith("select")
        else None
    )
    return conn, table, reads


@pytest.mark.parametrize("rows", [0, 4])
@pytest.mark.parametrize("n", [0, 2, 10, 2**100])
def test_duckdb_sample_count_is_deferred_and_exact(rows, n):
    reads: list[int] = []
    conn, native = _observed_duckdb_relation(reads, rows=rows)
    try:
        query = ma.relation(native).sample(n=n)
        query.schema
        query.explain()
        query.compile()
        assert reads == []

        result = query.to_dicts()
        assert len(result) == min(n, rows)
        assert len({row["id"] for row in result}) == len(result)
        assert all(row["paired"] == 10 * row["id"] for row in result)
        assert {row["id"] for row in result} <= set(range(1, rows + 1))
        if rows and n:
            assert reads
    finally:
        conn.disconnect()


@pytest.mark.parametrize("backend", ["duckdb", "sqlite"])
@pytest.mark.parametrize("rows", [[], _SQLITE_ROWS])
@pytest.mark.parametrize("n", [0, 2, 10])
def test_sql_tail_is_deferred_and_returns_last_rows(backend, rows, n):
    reads: list[int] | list[str] = []
    if backend == "duckdb":
        conn, native = _observed_duckdb_relation(reads, rows=len(rows))
    else:
        conn, native, reads = _sqlite_relation("tail_source", rows)
    try:
        query = ma.relation(native).sort("id").tail(n)
        query.schema
        query.explain()
        query.compile()
        assert reads == []

        result = query.to_dicts()
        expected = rows[-n:] if n else []
        assert result == [{"id": row[0], "paired": row[1]} for row in expected]
        if rows and n:
            assert reads
    finally:
        conn.disconnect()


@pytest.mark.parametrize("rows", [[], _SQLITE_ROWS])
@pytest.mark.parametrize("n", [0, 2, 10, 2**100])
def test_sqlite_sample_count_is_deferred_and_exact(rows, n):
    conn, native, reads = _sqlite_relation("sample_source", rows)
    try:
        query = ma.relation(native).sample(n=n)
        query.schema
        query.explain()
        query.compile()
        assert reads == []

        result = query.to_dicts()
        assert len(result) == min(n, len(rows))
        assert len({row["id"] for row in result}) == len(result)
        assert all(row["paired"] == 10 * row["id"] for row in result)
        if n:
            assert reads
    finally:
        conn.disconnect()


def test_trusted_duckdb_seeded_count_bypass_executes_deferred_result():
    reads: list[int] = []
    conn, native = _observed_duckdb_relation(reads)
    try:
        with ma.capability_policy(ma.CapabilityPolicy.trusted()):
            query = ma.relation(native).sample(n=2, seed=0)
            query.schema
            query.explain()
            query.compile()
            assert reads == []
            result = query.to_dicts()
        assert len(result) == 2
        assert len({row["id"] for row in result}) == 2
        assert all(row["paired"] == 10 * row["id"] for row in result)
        assert reads
    finally:
        conn.disconnect()
