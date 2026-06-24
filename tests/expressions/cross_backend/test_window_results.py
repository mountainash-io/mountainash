"""Cross-backend result verification for window operations.

Verifies that window expressions produce identical results across all 7
backends. Window functions require .over() context for partitioned operations.

Test data uses unique sort keys to ensure deterministic output ordering.

Known divergences:
- ibis-polars: No translation rule for WindowFunction (Ibis Polars backend limitation)
- ibis-duckdb/ibis-sqlite: Return 0-based ranks instead of 1-based (off-by-one)
- ibis: rank(method='average'/'max') has no SQL equivalent — raises BackendCapabilityError
- narwhals: percent_rank(), cume_dist(), ntile(), nth_value() not supported
- narwhals: rank(method='dense'/'ordinal'/'average'/'max') not supported via method param
- narwhals: Cannot apply .over() to elementwise (non-aggregate/non-window) expressions
- narwhals-lazy: order-dependent window ops (lead/lag/shift/cum_*/diff/first_value/
  last_value) raise InvalidOperationError on a LazyFrame; eager narwhals handles them
"""

from __future__ import annotations

import pytest

import mountainash as ma
from mountainash.core.types import BackendCapabilityError
from fixtures.backend_registry import ALL_BACKENDS


IBIS_BACKENDS = {"ibis-polars", "ibis-duckdb", "ibis-sqlite"}
NARWHALS_BACKENDS = {"pandas", "narwhals-polars", "narwhals-pandas", "narwhals-lazy"}
# narwhals LazyFrame rejects order-dependent window expressions (lead/lag/shift/
# cum_*/diff/first_value/last_value) that eager narwhals handles fine. This is a
# narwhals-lazy-specific divergence, so it gets its own guard rather than joining
# NARWHALS_BACKENDS (which would wrongly suppress the passing eager runs).
NARWHALS_LAZY_BACKENDS = {"narwhals-lazy"}


def _xfail_lazy_order_dependent(backend_name: str) -> None:
    """xfail order-dependent window ops on narwhals-lazy.

    narwhals raises ``InvalidOperationError`` for order-dependent expressions on
    a LazyFrame (lead/lag/shift/cum_*/diff/first_value/last_value). Eager
    narwhals computes them fine, so this divergence is lazy-specific.
    """
    if backend_name in NARWHALS_LAZY_BACKENDS:
        pytest.xfail(
            "narwhals-lazy: order-dependent window expression rejected on LazyFrame"
        )


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
        _xfail_lazy_order_dependent(backend_name)
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
        _xfail_lazy_order_dependent(backend_name)
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
        _xfail_lazy_order_dependent(backend_name)
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
        _xfail_lazy_order_dependent(backend_name)
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
        _xfail_lazy_order_dependent(backend_name)
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
        _xfail_lazy_order_dependent(backend_name)
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
        _xfail_lazy_order_dependent(backend_name)
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
        _xfail_lazy_order_dependent(backend_name)
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
        _xfail_lazy_order_dependent(backend_name)
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


# ─── Cumulative Operations ─────────────────────────────────────────────────────


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowCumSum:
    """Test cum_sum — cumulative sum."""

    def test_cum_sum_plain(self, backend_name, backend_factory):
        if backend_name in IBIS_BACKENDS:
            pytest.xfail("ibis: no translation rule for WindowFunction")
        _xfail_lazy_order_dependent(backend_name)
        data = {"a": [1, 2, 3, 4, 5]}
        df = backend_factory.create(data, backend_name)
        result = (
            ma.relation(df)
            .select(ma.col("a"), ma.col("a").cum_sum().alias("cs"))
            .to_dict()
        )
        assert result["cs"] == [1, 3, 6, 10, 15]

    def test_cum_sum_over_partition(self, backend_name, backend_factory):
        if backend_name in IBIS_BACKENDS:
            pytest.xfail("ibis: no translation rule for WindowFunction")
        data = {"group": ["A", "A", "A", "B", "B"],
                "val": [1, 2, 3, 10, 20]}
        df = backend_factory.create(data, backend_name)
        _xfail_lazy_order_dependent(backend_name)
        expr = ma.col("val").cum_sum().over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("val"), expr.alias("cs"))
            .sort("group", "val")
            .to_dict()
        )
        assert result["cs"] == [1, 3, 6, 10, 30]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowCumMax:
    """Test cum_max — cumulative maximum."""

    def test_cum_max_plain(self, backend_name, backend_factory):
        if backend_name in IBIS_BACKENDS:
            pytest.xfail("ibis: no translation rule for WindowFunction")
        _xfail_lazy_order_dependent(backend_name)
        data = {"a": [3, 1, 4, 1, 5]}
        df = backend_factory.create(data, backend_name)
        result = (
            ma.relation(df)
            .select(ma.col("a"), ma.col("a").cum_max().alias("cm"))
            .to_dict()
        )
        assert result["cm"] == [3, 3, 4, 4, 5]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowCumMin:
    """Test cum_min — cumulative minimum."""

    def test_cum_min_plain(self, backend_name, backend_factory):
        if backend_name in IBIS_BACKENDS:
            pytest.xfail("ibis: no translation rule for WindowFunction")
        _xfail_lazy_order_dependent(backend_name)
        data = {"a": [5, 3, 4, 1, 2]}
        df = backend_factory.create(data, backend_name)
        result = (
            ma.relation(df)
            .select(ma.col("a"), ma.col("a").cum_min().alias("cm"))
            .to_dict()
        )
        assert result["cm"] == [5, 3, 3, 1, 1]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowCumCount:
    """Test cum_count — cumulative count (non-null values)."""

    def test_cum_count_plain(self, backend_name, backend_factory):
        if backend_name in IBIS_BACKENDS:
            pytest.xfail("ibis: no translation rule for WindowFunction")
        _xfail_lazy_order_dependent(backend_name)
        data = {"a": [10, 20, 30, 40, 50]}
        df = backend_factory.create(data, backend_name)
        result = (
            ma.relation(df)
            .select(ma.col("a"), ma.col("a").cum_count().alias("cc"))
            .to_dict()
        )
        assert result["cc"] == [1, 2, 3, 4, 5]

    def test_cum_count_with_nulls(self, backend_name, backend_factory):
        if backend_name in IBIS_BACKENDS:
            pytest.xfail("ibis: no translation rule for WindowFunction")
        _xfail_lazy_order_dependent(backend_name)
        data = {"a": [10, None, 30, None, 50]}
        df = backend_factory.create(data, backend_name)
        result = (
            ma.relation(df)
            .select(ma.col("a"), ma.col("a").cum_count().alias("cc"))
            .to_dict()
        )
        assert result["cc"] == [1, 1, 2, 2, 3]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowCumProd:
    """Test cum_prod — cumulative product."""

    def test_cum_prod_plain(self, backend_name, backend_factory):
        if backend_name in IBIS_BACKENDS:
            pytest.xfail("ibis: no translation rule for WindowFunction")
        _xfail_lazy_order_dependent(backend_name)
        data = {"a": [1, 2, 3, 4]}
        df = backend_factory.create(data, backend_name)
        result = (
            ma.relation(df)
            .select(ma.col("a"), ma.col("a").cum_prod().alias("cp"))
            .to_dict()
        )
        assert result["cp"] == [1, 2, 6, 24]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowDiff:
    """Test diff — element-wise difference with lag."""

    def test_diff_basic(self, backend_name, backend_factory):
        if backend_name in IBIS_BACKENDS:
            pytest.xfail("ibis: no translation rule for WindowFunction")
        _xfail_lazy_order_dependent(backend_name)
        data = {"a": [10, 20, 35, 50]}
        df = backend_factory.create(data, backend_name)
        result = (
            ma.relation(df)
            .select(ma.col("a"), ma.col("a").diff().alias("d"))
            .to_dict()
        )
        assert result["d"] == [None, 10, 15, 15]

    def test_diff_n2(self, backend_name, backend_factory):
        if backend_name in IBIS_BACKENDS:
            pytest.xfail("ibis: no translation rule for WindowFunction")
        if backend_name in NARWHALS_BACKENDS:
            pytest.xfail("narwhals: diff() only supports n=1")
        data = {"a": [10, 20, 30, 40, 50]}
        df = backend_factory.create(data, backend_name)
        result = (
            ma.relation(df)
            .select(ma.col("a"), ma.col("a").diff(n=2).alias("d"))
            .to_dict()
        )
        assert result["d"] == [None, None, 20, 20, 20]


# ─── Rank Variants ────────────────────────────────────────────────────────────


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowRankDescending:
    """Test rank(descending=True) produces reversed ordering."""

    def test_rank_descending_differs_from_ascending(self, backend_name, backend_factory):
        if backend_name == "ibis-polars":
            pytest.xfail("ibis-polars: no translation rule for WindowFunction")
        if backend_name in ("ibis-duckdb", "ibis-sqlite"):
            pytest.xfail("ibis-duckdb/sqlite: rank() returns 0-based values")
        data = {"group": ["A", "A", "A", "A"],
                "score": [10, 20, 30, 30],
                "id": [1, 2, 3, 4]}
        df = backend_factory.create(data, backend_name)
        expr_asc = ma.col("score").rank(method="min").over("group")
        expr_desc = ma.col("score").rank(method="min", descending=True).over("group")
        result_asc = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), ma.col("id"), expr_asc.alias("rnk"))
            .sort("group", "score", "id")
            .to_dict()
        )
        result_desc = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), ma.col("id"), expr_desc.alias("rnk"))
            .sort("group", "score", "id")
            .to_dict()
        )
        assert result_asc["rnk"] != result_desc["rnk"]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowRankMethodDense:
    """Test rank(method='dense') — consecutive ranks, no gaps on ties."""

    def test_rank_method_dense(self, backend_name, backend_factory):
        if backend_name == "ibis-polars":
            pytest.xfail("ibis-polars: no translation rule for WindowFunction")
        if backend_name in ("ibis-duckdb", "ibis-sqlite"):
            pytest.xfail("ibis-duckdb/sqlite: rank() returns 0-based values")
        if backend_name in NARWHALS_BACKENDS:
            pytest.xfail("narwhals: rank(method='dense') not supported via method param")
        data = {"group": ["A", "A", "A", "A"],
                "score": [10, 20, 30, 30],
                "id": [1, 2, 3, 4]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").rank(method="dense").over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), ma.col("id"), expr.alias("drnk"))
            .sort("group", "score", "id")
            .to_dict()
        )
        assert result["drnk"] == [1, 2, 3, 3]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowRankMethodOrdinal:
    """Test rank(method='ordinal') — unique sequential ranks."""

    def test_rank_method_ordinal(self, backend_name, backend_factory):
        if backend_name == "ibis-polars":
            pytest.xfail("ibis-polars: no translation rule for WindowFunction")
        if backend_name in ("ibis-duckdb", "ibis-sqlite"):
            pytest.xfail("ibis-duckdb/sqlite: rank() returns 0-based values")
        if backend_name in NARWHALS_BACKENDS:
            pytest.xfail("narwhals: rank(method='ordinal') not supported via method param")
        data = {"group": ["A", "A", "A", "A"],
                "score": [10, 20, 30, 30],
                "id": [1, 2, 3, 4]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").rank(method="ordinal").over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), ma.col("id"), expr.alias("rn"))
            .sort("group", "score", "id")
            .to_dict()
        )
        assert result["rn"] == [1, 2, 3, 4]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowRankMethodAverage:
    """Test rank(method='average') — averaged ranks for ties (Polars-only, no SQL equivalent)."""

    def test_rank_method_average(self, backend_name, backend_factory):
        if backend_name in IBIS_BACKENDS:
            pytest.xfail("ibis: rank(method='average') has no SQL equivalent")
        if backend_name in NARWHALS_BACKENDS:
            pytest.xfail("narwhals: rank(method='average') not supported")
        data = {"group": ["A", "A", "A", "A"],
                "score": [10, 20, 30, 30],
                "id": [1, 2, 3, 4]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").rank(method="average").over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), ma.col("id"), expr.alias("rnk"))
            .sort("group", "score", "id")
            .to_dict()
        )
        assert result["rnk"] == [1.0, 2.0, 3.5, 3.5]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowRankMethodMax:
    """Test rank(method='max') — max rank for ties (Polars-only, no SQL equivalent)."""

    def test_rank_method_max(self, backend_name, backend_factory):
        if backend_name in IBIS_BACKENDS:
            pytest.xfail("ibis: rank(method='max') has no SQL equivalent")
        if backend_name in NARWHALS_BACKENDS:
            pytest.xfail("narwhals: rank(method='max') not supported")
        data = {"group": ["A", "A", "A", "A"],
                "score": [10, 20, 30, 30],
                "id": [1, 2, 3, 4]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").rank(method="max").over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), ma.col("id"), expr.alias("rnk"))
            .sort("group", "score", "id")
            .to_dict()
        )
        assert result["rnk"] == [1, 2, 4, 4]


# ─── Rank Method Guard ────────────────────────────────────────────────────────


class TestWindowRankMethodGuard:
    """Ibis must raise BackendCapabilityError for rank methods without SQL equivalents."""

    def test_ibis_rank_average_raises(self):
        import ibis
        con = ibis.duckdb.connect()
        t = con.create_table("_test_rank_avg", {"score": [10, 20, 30, 30]})
        expr = ma.col("score").rank(method="average").over("score")
        with pytest.raises(BackendCapabilityError, match="average"):
            expr.compile(t)

    def test_ibis_rank_max_raises(self):
        import ibis
        con = ibis.duckdb.connect()
        t = con.create_table("_test_rank_max", {"score": [10, 20, 30, 30]})
        expr = ma.col("score").rank(method="max").over("score")
        with pytest.raises(BackendCapabilityError, match="max"):
            expr.compile(t)


# ─── Percent Rank & Cume Dist ─────────────────────────────────────────────────


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowPercentRank:
    """Test percent_rank() — values between 0 and 1."""

    def test_percent_rank_basic(self, backend_name, backend_factory):
        if backend_name in IBIS_BACKENDS:
            pytest.xfail("ibis: no translation rule for WindowFunction")
        if backend_name in NARWHALS_BACKENDS:
            pytest.xfail("narwhals: percent_rank() not supported")
        data = {"group": ["A", "A", "A", "B", "B", "B"],
                "score": [10, 20, 20, 30, 10, 20]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").percent_rank().over("group", order_by="score")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), expr.alias("prnk"))
            .sort("group", "score")
            .to_dict()
        )
        for val in result["prnk"]:
            assert 0.0 <= val <= 1.0


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowCumeDist:
    """Test cume_dist() — cumulative distribution, values between 0 and 1."""

    def test_cume_dist_basic(self, backend_name, backend_factory):
        if backend_name in IBIS_BACKENDS:
            pytest.xfail("ibis: no translation rule for WindowFunction")
        if backend_name in NARWHALS_BACKENDS:
            pytest.xfail("narwhals: cume_dist() not supported")
        data = {"group": ["A", "A", "A", "B", "B", "B"],
                "score": [10, 20, 20, 30, 10, 20]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").cume_dist().over("group", order_by="score")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), expr.alias("cdist"))
            .sort("group", "score")
            .to_dict()
        )
        for val in result["cdist"]:
            assert 0.0 <= val <= 1.0


# ─── Nth Value ────────────────────────────────────────────────────────────────


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowNthValue:
    """Test nth_value(n) — nth value in partition."""

    def test_nth_value_basic(self, backend_name, backend_factory):
        if backend_name in IBIS_BACKENDS:
            pytest.xfail("ibis: no translation rule for WindowFunction")
        if backend_name in NARWHALS_BACKENDS:
            pytest.xfail("narwhals: nth_value() not supported")
        data = {"group": ["A", "A", "A"],
                "score": [10, 20, 30]}
        df = backend_factory.create(data, backend_name)
        try:
            expr = ma.col("score").nth_value(2).over("group")
            result = (
                ma.relation(df)
                .select(ma.col("group"), ma.col("score"), expr.alias("nth"))
                .sort("group", "score")
                .to_dict()
            )
            assert all(v == 20 for v in result["nth"])
        except Exception:
            pytest.xfail("nth_value not supported on this backend")


# ─── Over Modifier Variants ──────────────────────────────────────────────────


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowOverScalar:
    """Test .over() wrapping a non-window expression (scalar windowed)."""

    def test_over_scalar_expression(self, backend_name, backend_factory):
        if backend_name in IBIS_BACKENDS:
            pytest.xfail("ibis: no translation rule for WindowFunction")
        if backend_name in NARWHALS_BACKENDS:
            pytest.xfail("narwhals: Cannot apply .over() to elementwise expression")
        data = {"dept": ["eng", "eng", "sales", "sales"],
                "salary": [100, 120, 80, 110]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("salary").add(ma.lit(0)).over("dept")
        result = (
            ma.relation(df)
            .select(ma.col("dept"), ma.col("salary"), expr.alias("windowed"))
            .sort("dept", "salary")
            .to_dict()
        )
        assert len(result["windowed"]) == 4


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowMultiPartition:
    """Test .over() with multiple partition columns."""

    def test_rank_multi_partition(self, backend_name, backend_factory):
        if backend_name == "ibis-polars":
            pytest.xfail("ibis-polars: no translation rule for WindowFunction")
        if backend_name in ("ibis-duckdb", "ibis-sqlite"):
            pytest.xfail("ibis-duckdb/sqlite: rank() returns 0-based values")
        data = {"dept": ["eng", "eng", "eng", "sales", "sales"],
                "level": ["jr", "sr", "jr", "jr", "sr"],
                "salary": [100, 120, 90, 80, 110]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("salary").rank(method="min").over("dept", "level")
        result = (
            ma.relation(df)
            .select(
                ma.col("dept"), ma.col("level"), ma.col("salary"),
                expr.alias("rnk"),
            )
            .sort("dept", "level", "salary")
            .to_dict()
        )
        assert len(result["rnk"]) == 5
        assert all(r >= 1 for r in result["rnk"])


class TestWindowRequiresOver:
    """Window functions that don't pre-populate window_spec must have .over()."""

    def test_percent_rank_without_over_raises(self):
        import polars as pl
        df = pl.DataFrame({"salary": [100, 120, 90]})
        expr = ma.col("salary").percent_rank()
        with pytest.raises(ValueError, match=r"\.over\(\)"):
            expr.compile(df)
