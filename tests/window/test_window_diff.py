"""Tests for .diff() — consecutive row difference."""

from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma


@pytest.fixture
def diff_df():
    return pl.DataFrame({
        "group": ["A", "A", "A", "B", "B"],
        "value": [10, 30, 25, 100, 80],
        "ts": [1, 2, 3, 1, 2],
    })


class TestDiff:
    def test_diff_basic(self, diff_df):
        """diff() computes consecutive differences."""
        expr = ma.col("value").diff()
        result = diff_df.with_columns(expr.compile(diff_df).alias("d"))
        diffs = result["d"].to_list()
        assert diffs == [None, 20, -5, 75, -20]

    def test_diff_over_partition(self, diff_df):
        """diff().over() computes differences within each partition."""
        expr = ma.col("value").diff().over("group", order_by="ts")
        result = diff_df.with_columns(expr.compile(diff_df).alias("d"))
        group_a = result.filter(pl.col("group") == "A").sort("ts")
        diffs_a = group_a["d"].to_list()
        assert diffs_a == [None, 20, -5]

        group_b = result.filter(pl.col("group") == "B").sort("ts")
        diffs_b = group_b["d"].to_list()
        assert diffs_b == [None, -20]
