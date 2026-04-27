"""Tests that Polars apply_window passes order_by through to .over()."""

from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma


@pytest.fixture
def unordered_df():
    return pl.DataFrame({
        "group": ["A", "A", "A", "B", "B"],
        "value": [30, 10, 20, 50, 40],
        "ts": [3, 1, 2, 2, 1],
    })


class TestApplyWindowOrderBy:
    def test_lag_with_order_by_respects_ordering(self, unordered_df):
        """lag(1).over() with order_by should lag in the specified order."""
        expr = ma.col("value").lag(1).over("group", order_by="ts")
        result = unordered_df.with_columns(expr.compile(unordered_df).alias("lagged"))

        group_a = result.filter(pl.col("group") == "A").sort("ts")
        lagged = group_a["lagged"].to_list()
        # ts order: ts=1→value=10, ts=2→value=20, ts=3→value=30
        # lag(1) in ts order: [None, 10, 20]
        assert lagged == [None, 10, 20]
