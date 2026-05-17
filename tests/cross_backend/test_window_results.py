"""Cross-backend result verification for window operations.

Verifies that window expressions produce identical results across all 7
backends. Window functions require .over() context for partitioned operations.

Test data uses unique sort keys to ensure deterministic output ordering.

Known divergences:
- ibis-polars: No translation rule for WindowFunction (Ibis Polars backend limitation)
- ibis-duckdb/ibis-sqlite: Return 0-based ranks instead of 1-based (off-by-one)
- rank() default method='average': Not supported on Ibis (no SQL equivalent)
"""

from __future__ import annotations

import pytest

import mountainash as ma


ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals-polars",
    "narwhals-pandas",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]

IBIS_BACKENDS = {"ibis-polars", "ibis-duckdb", "ibis-sqlite"}


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowRank:
    """Test rank(method='min') — equivalent to SQL RANK()."""

    def test_rank_basic(self, backend_name, backend_factory):
        if backend_name == "ibis-polars":
            pytest.xfail("ibis-polars: no translation rule for WindowFunction")
        if backend_name in ("ibis-duckdb", "ibis-sqlite"):
            pytest.xfail("ibis-duckdb/sqlite: rank() returns 0-based values")
        data = {"group": ["A", "A", "A", "B", "B"],
                "score": [10, 30, 20, 15, 25]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").rank(method="min").over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), expr.alias("rnk"))
            .sort("group", "score")
            .to_dict()
        )
        # A: scores [10,20,30] -> ranks [1,2,3]; B: scores [15,25] -> ranks [1,2]
        assert result["rnk"] == [1, 2, 3, 1, 2]

    def test_rank_with_ties(self, backend_name, backend_factory):
        if backend_name == "ibis-polars":
            pytest.xfail("ibis-polars: no translation rule for WindowFunction")
        if backend_name in ("ibis-duckdb", "ibis-sqlite"):
            pytest.xfail("ibis-duckdb/sqlite: rank() returns 0-based values")
        data = {"group": ["A", "A", "A", "A"],
                "score": [10, 20, 20, 30],
                "id": [1, 2, 3, 4]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").rank(method="min").over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), ma.col("id"), expr.alias("rnk"))
            .sort("group", "score", "id")
            .to_dict()
        )
        # Tied scores get same rank; next rank skips: [1, 2, 2, 4]
        assert result["rnk"] == [1, 2, 2, 4]

    def test_rank_single_row_partition(self, backend_name, backend_factory):
        if backend_name == "ibis-polars":
            pytest.xfail("ibis-polars: no translation rule for WindowFunction")
        if backend_name in ("ibis-duckdb", "ibis-sqlite"):
            pytest.xfail("ibis-duckdb/sqlite: rank() returns 0-based values")
        data = {"group": ["A"], "score": [99]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").rank(method="min").over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), expr.alias("rnk"))
            .to_dict()
        )
        assert result["rnk"] == [1]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowDenseRank:
    """Test dense_rank() — equivalent to SQL DENSE_RANK()."""

    def test_dense_rank_basic(self, backend_name, backend_factory):
        if backend_name == "ibis-polars":
            pytest.xfail("ibis-polars: no translation rule for WindowFunction")
        if backend_name in ("ibis-duckdb", "ibis-sqlite"):
            pytest.xfail("ibis-duckdb/sqlite: dense_rank() returns 0-based values")
        data = {"group": ["A", "A", "A", "B", "B"],
                "score": [10, 30, 20, 15, 25]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").dense_rank().over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), expr.alias("drnk"))
            .sort("group", "score")
            .to_dict()
        )
        assert result["drnk"] == [1, 2, 3, 1, 2]

    def test_dense_rank_with_ties(self, backend_name, backend_factory):
        if backend_name == "ibis-polars":
            pytest.xfail("ibis-polars: no translation rule for WindowFunction")
        if backend_name in ("ibis-duckdb", "ibis-sqlite"):
            pytest.xfail("ibis-duckdb/sqlite: dense_rank() returns 0-based values")
        data = {"group": ["A", "A", "A", "A"],
                "score": [10, 20, 20, 30],
                "id": [1, 2, 3, 4]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").dense_rank().over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), ma.col("id"), expr.alias("drnk"))
            .sort("group", "score", "id")
            .to_dict()
        )
        # Dense rank: no gaps -> [1, 2, 2, 3]
        assert result["drnk"] == [1, 2, 2, 3]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowRowNumber:
    """Test row_number() — equivalent to SQL ROW_NUMBER()."""

    def test_row_number_basic(self, backend_name, backend_factory):
        if backend_name == "ibis-polars":
            pytest.xfail("ibis-polars: no translation rule for WindowFunction")
        if backend_name in ("ibis-duckdb", "ibis-sqlite"):
            pytest.xfail("ibis-duckdb/sqlite: row_number() returns 0-based values")
        data = {"group": ["A", "A", "A", "B", "B"],
                "score": [10, 30, 20, 15, 25]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").row_number().over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), expr.alias("rn"))
            .sort("group", "score")
            .to_dict()
        )
        assert result["rn"] == [1, 2, 3, 1, 2]

    def test_row_number_single_partition(self, backend_name, backend_factory):
        if backend_name == "ibis-polars":
            pytest.xfail("ibis-polars: no translation rule for WindowFunction")
        if backend_name in ("ibis-duckdb", "ibis-sqlite"):
            pytest.xfail("ibis-duckdb/sqlite: row_number() returns 0-based values")
        data = {"group": ["A", "A", "A"],
                "score": [30, 10, 20]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").row_number().over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), expr.alias("rn"))
            .sort("group", "score")
            .to_dict()
        )
        assert result["rn"] == [1, 2, 3]
