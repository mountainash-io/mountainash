"""Tests for .diff() — consecutive row difference."""

from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma

BACKENDS = ["polars", "narwhals-polars", "ibis-duckdb"]


# =============================================================================
# Cross-backend: basic diff (no .over())
# =============================================================================


@pytest.mark.parametrize("backend_name", BACKENDS)
class TestDiff:
    def test_diff_basic(self, backend_name, backend_factory, collect_expr):
        """diff() computes consecutive differences."""
        data = {"value": [10, 30, 25, 100, 80]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").diff()
        result = collect_expr(df, expr)
        assert result == [None, 20, -5, 75, -20], f"[{backend_name}] got {result}"


# =============================================================================
# Polars-only: .over() path
# =============================================================================


class TestDiffOverPartition:
    """Tests Polars-specific .over() execution path — no cross-backend equivalent via relation API."""

    @pytest.fixture
    def diff_df(self):
        return pl.DataFrame({
            "group": ["A", "A", "A", "B", "B"],
            "value": [10, 30, 25, 100, 80],
            "ts": [1, 2, 3, 1, 2],
        })

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
