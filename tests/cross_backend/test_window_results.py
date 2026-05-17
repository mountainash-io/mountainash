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
NARWHALS_BACKENDS = {"pandas", "narwhals-polars", "narwhals-pandas"}


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


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowLead:
    """Test lead(n) — next value in partition."""

    def test_lead_basic(self, backend_name, backend_factory):
        if backend_name in IBIS_BACKENDS:
            pytest.xfail("ibis: no translation rule for WindowFunction")
        data = {"group": ["A", "A", "A", "B", "B", "B"],
                "score": [10, 20, 30, 15, 25, 35]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").lead(1).over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), expr.alias("lead_val"))
            .sort("group", "score")
            .to_dict()
        )
        assert result["lead_val"] == [20, 30, None, 25, 35, None]

    def test_lead_n2(self, backend_name, backend_factory):
        if backend_name in IBIS_BACKENDS:
            pytest.xfail("ibis: no translation rule for WindowFunction")
        data = {"group": ["A", "A", "A", "A"],
                "score": [10, 20, 30, 40]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").lead(2).over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), expr.alias("lead_val"))
            .sort("group", "score")
            .to_dict()
        )
        assert result["lead_val"] == [30, 40, None, None]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowLag:
    """Test lag(n) — previous value in partition."""

    def test_lag_basic(self, backend_name, backend_factory):
        if backend_name in IBIS_BACKENDS:
            pytest.xfail("ibis: no translation rule for WindowFunction")
        data = {"group": ["A", "A", "A", "B", "B", "B"],
                "score": [10, 20, 30, 15, 25, 35]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").lag(1).over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), expr.alias("lag_val"))
            .sort("group", "score")
            .to_dict()
        )
        assert result["lag_val"] == [None, 10, 20, None, 15, 25]

    def test_lag_n2(self, backend_name, backend_factory):
        if backend_name in IBIS_BACKENDS:
            pytest.xfail("ibis: no translation rule for WindowFunction")
        data = {"group": ["A", "A", "A", "A"],
                "score": [10, 20, 30, 40]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").lag(2).over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), expr.alias("lag_val"))
            .sort("group", "score")
            .to_dict()
        )
        assert result["lag_val"] == [None, None, 10, 20]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowShift:
    """Test shift(n) — shift values in partition (positive=lag, negative=lead)."""

    def test_shift_forward(self, backend_name, backend_factory):
        if backend_name in IBIS_BACKENDS:
            pytest.xfail("ibis: no translation rule for WindowFunction")
        data = {"group": ["A", "A", "A", "A", "A"],
                "score": [10, 20, 30, 40, 50]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").shift(1).over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), expr.alias("shifted"))
            .sort("group", "score")
            .to_dict()
        )
        assert result["shifted"] == [None, 10, 20, 30, 40]

    def test_shift_backward(self, backend_name, backend_factory):
        if backend_name in IBIS_BACKENDS:
            pytest.xfail("ibis: no translation rule for WindowFunction")
        data = {"group": ["A", "A", "A", "A", "A"],
                "score": [10, 20, 30, 40, 50]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").shift(-1).over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), expr.alias("shifted"))
            .sort("group", "score")
            .to_dict()
        )
        assert result["shifted"] == [20, 30, 40, 50, None]

    def test_shift_n2(self, backend_name, backend_factory):
        if backend_name in IBIS_BACKENDS:
            pytest.xfail("ibis: no translation rule for WindowFunction")
        data = {"group": ["A", "A", "A", "A", "A"],
                "score": [10, 20, 30, 40, 50]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").shift(2).over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), expr.alias("shifted"))
            .sort("group", "score")
            .to_dict()
        )
        assert result["shifted"] == [None, None, 10, 20, 30]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowFirstValue:
    """Test first_value() — first value in partition."""

    def test_first_value_basic(self, backend_name, backend_factory):
        if backend_name in IBIS_BACKENDS:
            pytest.xfail("ibis: no translation rule for WindowFunction")
        data = {"group": ["A", "A", "A", "B", "B"],
                "score": [10, 20, 30, 15, 25]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").first_value().over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), expr.alias("fv"))
            .sort("group", "score")
            .to_dict()
        )
        assert result["fv"] == [10, 10, 10, 15, 15]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowLastValue:
    """Test last_value() — last value in partition."""

    def test_last_value_basic(self, backend_name, backend_factory):
        if backend_name in IBIS_BACKENDS:
            pytest.xfail("ibis: no translation rule for WindowFunction")
        data = {"group": ["A", "A", "A", "B", "B"],
                "score": [10, 20, 30, 15, 25]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").last_value().over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), expr.alias("lv"))
            .sort("group", "score")
            .to_dict()
        )
        assert result["lv"] == [30, 30, 30, 25, 25]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowNtile:
    """Test ntile(n) — divide partition into n roughly equal buckets."""

    def test_ntile_2(self, backend_name, backend_factory):
        if backend_name in IBIS_BACKENDS:
            pytest.xfail("ibis: no translation rule for WindowFunction")
        if backend_name in NARWHALS_BACKENDS:
            pytest.xfail("narwhals: ntile() not supported")
        data = {"group": ["A", "A", "A", "A"],
                "score": [10, 20, 30, 40]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").ntile(2).over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), expr.alias("bucket"))
            .sort("group", "score")
            .to_dict()
        )
        assert result["bucket"] == [1, 1, 2, 2]

    def test_ntile_3(self, backend_name, backend_factory):
        if backend_name in IBIS_BACKENDS:
            pytest.xfail("ibis: no translation rule for WindowFunction")
        if backend_name in NARWHALS_BACKENDS:
            pytest.xfail("narwhals: ntile() not supported")
        data = {"group": ["A", "A", "A", "A", "A", "A"],
                "score": [10, 20, 30, 40, 50, 60]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").ntile(3).over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), expr.alias("bucket"))
            .sort("group", "score")
            .to_dict()
        )
        assert result["bucket"] == [1, 1, 2, 2, 3, 3]
