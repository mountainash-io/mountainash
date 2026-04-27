"""Tests for the .over() modifier compiled against real Polars DataFrames.

Tests verify that window expressions with .over() compile correctly
and produce expected results when applied to Polars DataFrames.
"""

from __future__ import annotations

import pytest
import polars as pl
import mountainash as ma


@pytest.fixture
def dept_df():
    return pl.DataFrame({
        "dept": ["eng", "eng", "eng", "sales", "sales"],
        "salary": [100, 120, 90, 80, 110],
        "name": ["alice", "bob", "charlie", "diana", "eve"],
    })


class TestOverModifier:
    """Tests for .over() modifier on various expressions."""

    def test_over_wraps_scalar_expression(self, dept_df):
        """ma.col('salary').add(ma.lit(0)).over('dept') compiles and produces 5 rows."""
        expr = ma.col("salary").add(ma.lit(0)).over("dept")
        result = dept_df.with_columns(expr.compile(dept_df).alias("windowed"))
        assert result.shape[0] == 5
        assert "windowed" in result.columns

    def test_window_function_without_over_raises(self, dept_df):
        """Compiling a window function without .over() should raise ValueError.

        Note: rank()/dense_rank()/row_number() pre-populate window_spec so they
        work without explicit .over(). Use percent_rank() which does NOT
        pre-populate its spec.
        """
        expr = ma.col("salary").percent_rank()
        with pytest.raises(ValueError, match=r"\.over\(\)"):
            expr.compile(dept_df)

    def test_rank_in_relation_with_columns(self, dept_df):
        """rank().over() inside a relation pipeline produces expected output."""
        rank_expr = ma.col("salary").rank().over("dept", order_by="salary")
        result = (
            ma.relation(dept_df)
            .with_columns(rank_expr.compile(dept_df).alias("salary_rank"))
            .to_polars()
        )
        assert "salary_rank" in result.columns
        assert result.shape[0] == 5

    def test_lag_in_relation_with_columns(self, dept_df):
        """lag(1).over() inside a relation pipeline produces expected output."""
        lag_expr = ma.col("salary").lag(1).over("dept", order_by="salary")
        result = (
            ma.relation(dept_df)
            .with_columns(lag_expr.compile(dept_df).alias("salary_lag"))
            .to_polars()
        )
        assert "salary_lag" in result.columns
        assert result.shape[0] == 5

    def test_over_with_multiple_partitions(self, dept_df):
        """rank().over() with multiple partition columns compiles without error."""
        expr = ma.col("salary").rank().over("dept", "name", order_by="salary")
        result = dept_df.with_columns(expr.compile(dept_df).alias("ranked"))
        assert result.shape[0] == 5
        assert "ranked" in result.columns

    def test_over_with_no_partition(self, dept_df):
        """add(lit(0)).over() with no partition (global window) compiles."""
        expr = ma.col("salary").add(ma.lit(0)).over()
        result = dept_df.with_columns(expr.compile(dept_df).alias("global_window"))
        assert result.shape[0] == 5
        assert "global_window" in result.columns
