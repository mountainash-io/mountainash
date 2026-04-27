"""Tests for cumulative operations: cum_sum, cum_max, cum_min, cum_count."""

from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma


@pytest.fixture
def cum_df():
    return pl.DataFrame({
        "store": ["A", "A", "A", "B", "B"],
        "date": [1, 2, 3, 1, 2],
        "sales": [10, 20, 30, 100, 50],
    })


class TestCumSum:
    def test_cum_sum_basic(self, cum_df):
        """cum_sum() computes running total."""
        expr = ma.col("sales").cum_sum()
        result = cum_df.with_columns(expr.compile(cum_df).alias("cs"))
        assert result["cs"].to_list() == [10, 30, 60, 160, 210]

    def test_cum_sum_over_partition_with_order(self, cum_df):
        """cum_sum().over('store', order_by='date') resets per partition."""
        expr = ma.col("sales").cum_sum().over("store", order_by="date")
        result = cum_df.with_columns(expr.compile(cum_df).alias("cs"))

        store_a = result.filter(pl.col("store") == "A").sort("date")
        assert store_a["cs"].to_list() == [10, 30, 60]

        store_b = result.filter(pl.col("store") == "B").sort("date")
        assert store_b["cs"].to_list() == [100, 150]

    def test_cum_sum_reverse(self, cum_df):
        """cum_sum(reverse=True) computes from bottom to top."""
        expr = ma.col("sales").cum_sum(reverse=True)
        result = cum_df.with_columns(expr.compile(cum_df).alias("cs"))
        assert result["cs"].to_list() == [210, 200, 180, 150, 50]


class TestCumMax:
    def test_cum_max_basic(self, cum_df):
        """cum_max() computes running maximum."""
        expr = ma.col("sales").cum_max()
        result = cum_df.with_columns(expr.compile(cum_df).alias("cm"))
        assert result["cm"].to_list() == [10, 20, 30, 100, 100]


class TestCumMin:
    def test_cum_min_basic(self, cum_df):
        """cum_min() computes running minimum."""
        expr = ma.col("sales").cum_min()
        result = cum_df.with_columns(expr.compile(cum_df).alias("cm"))
        assert result["cm"].to_list() == [10, 10, 10, 10, 10]
