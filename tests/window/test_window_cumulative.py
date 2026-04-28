"""Tests for cumulative operations: cum_sum, cum_max, cum_min, cum_count."""

from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma

BACKENDS = ["polars", "narwhals-polars", "ibis-duckdb"]

# Ibis cumulative ops (cumsum, cummax, cummin) compile to .cumsum().over(...)
# which Ibis rejects at execution time because cumsum() is already a window
# function and cannot be wrapped in a second .over() frame expression.
# This is a pre-existing backend limitation — not introduced by PR #84.
_IBIS_CUM_XFAIL = pytest.mark.xfail(
    reason=(
        "Ibis cumulative ops compile to .cumsum().over(...) which Ibis rejects: "
        "'No reduction or analytic function found to construct a window expression'. "
        "Pre-existing backend limitation."
    )
)


# =============================================================================
# Cross-backend: cum_sum basic
# =============================================================================


@pytest.mark.parametrize("backend_name", [
    "polars",
    "narwhals-polars",
    pytest.param("ibis-duckdb", marks=_IBIS_CUM_XFAIL),
])
class TestCumSum:
    def test_cum_sum_basic(self, backend_name, backend_factory, collect_expr):
        """cum_sum() computes running total."""
        data = {"sales": [10, 20, 30, 100, 50]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("sales").cum_sum()
        result = collect_expr(df, expr)
        assert result == [10, 30, 60, 160, 210], f"[{backend_name}] got {result}"

    def test_cum_sum_reverse(self, backend_name, backend_factory, collect_expr):
        """cum_sum(reverse=True) computes from bottom to top."""
        data = {"sales": [10, 20, 30, 100, 50]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("sales").cum_sum(reverse=True)
        result = collect_expr(df, expr)
        assert result == [210, 200, 180, 150, 50], f"[{backend_name}] got {result}"


# =============================================================================
# Cross-backend: cum_max basic
# =============================================================================


@pytest.mark.parametrize("backend_name", [
    "polars",
    "narwhals-polars",
    pytest.param("ibis-duckdb", marks=_IBIS_CUM_XFAIL),
])
class TestCumMax:
    def test_cum_max_basic(self, backend_name, backend_factory, collect_expr):
        """cum_max() computes running maximum."""
        data = {"sales": [10, 20, 30, 100, 50]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("sales").cum_max()
        result = collect_expr(df, expr)
        assert result == [10, 20, 30, 100, 100], f"[{backend_name}] got {result}"


# =============================================================================
# Cross-backend: cum_min basic
# =============================================================================


@pytest.mark.parametrize("backend_name", [
    "polars",
    "narwhals-polars",
    pytest.param("ibis-duckdb", marks=_IBIS_CUM_XFAIL),
])
class TestCumMin:
    def test_cum_min_basic(self, backend_name, backend_factory, collect_expr):
        """cum_min() computes running minimum."""
        data = {"sales": [10, 20, 30, 100, 50]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("sales").cum_min()
        result = collect_expr(df, expr)
        assert result == [10, 10, 10, 10, 10], f"[{backend_name}] got {result}"


# =============================================================================
# Polars-only: .over() path
# =============================================================================


class TestCumSumOverPartition:
    """Tests Polars-specific .over() execution path — no cross-backend equivalent via relation API."""

    @pytest.fixture
    def cum_df(self):
        return pl.DataFrame({
            "store": ["A", "A", "A", "B", "B"],
            "date": [1, 2, 3, 1, 2],
            "sales": [10, 20, 30, 100, 50],
        })

    def test_cum_sum_over_partition_with_order(self, cum_df):
        """cum_sum().over('store', order_by='date') resets per partition."""
        expr = ma.col("sales").cum_sum().over("store", order_by="date")
        result = cum_df.with_columns(expr.compile(cum_df).alias("cs"))

        store_a = result.filter(pl.col("store") == "A").sort("date")
        assert store_a["cs"].to_list() == [10, 30, 60]

        store_b = result.filter(pl.col("store") == "B").sort("date")
        assert store_b["cs"].to_list() == [100, 150]
