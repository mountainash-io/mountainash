"""
Tests for cross-backend filter expression compatibility.

This module ensures filter expressions produce consistent results across all supported
DataFrame backends, validating the universal compatibility of the filter expression system.
"""

from __future__ import annotations

import pytest
import pandas as pd
import polars as pl
import ibis
import narwhals as nw

from mountainash.dataframes.filter_expressions import FilterExpressionStrategyFactory
from mountainash.dataframes import DataFrameUtils


@pytest.mark.integration
class TestCrossBackendSingleCondition:
    """Test that single-condition filters work consistently across backends."""

    def test_age_filter_polars_vs_narwhals(self, polars_df, narwhals_df):
        """Test age > 30 filter produces same results in Polars and Narwhals."""
        # Polars filter
        polars_expr = pl.col("age") > 30
        polars_factory = FilterExpressionStrategyFactory()
        polars_strategy = polars_factory.get_strategy(polars_expr)
        polars_result = polars_strategy.filter(polars_df, polars_expr)

        # Narwhals filter
        nw_expr = nw.col("age") > 30
        nw_factory = FilterExpressionStrategyFactory()
        nw_strategy = nw_factory.get_strategy(nw_expr)
        nw_result = nw_strategy.filter(narwhals_df, nw_expr)

        # Both should have same row count
        assert len(polars_result) == len(nw.to_native(nw_result))
        assert len(polars_result) == 5

    def test_age_filter_pandas_vs_polars(self, pandas_df, polars_df):
        """Test age > 30 filter produces same results in Pandas and Polars."""
        # Pandas filter
        pandas_expr = pandas_df["age"] > 30
        pandas_factory = FilterExpressionStrategyFactory()
        pandas_strategy = pandas_factory.get_strategy(pandas_expr)
        pandas_result = pandas_strategy.filter(pandas_df, pandas_expr)

        # Polars filter
        polars_expr = pl.col("age") > 30
        polars_factory = FilterExpressionStrategyFactory()
        polars_strategy = polars_factory.get_strategy(polars_expr)
        polars_result = polars_strategy.filter(polars_df, polars_expr)

        # Both should have same row count
        assert len(pandas_result) == len(polars_result)
        assert len(pandas_result) == 5

    def test_age_filter_ibis_consistency(self, ibis_table):
        """Test Ibis age > 30 filter produces expected results."""
        ibis_expr = ibis_table.age > 30
        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(ibis_expr)
        result = strategy.filter(ibis_table, ibis_expr)

        result_df = result.execute()
        assert len(result_df) == 5


@pytest.mark.integration
class TestCrossBackendMultipleConditions:
    """Test that multi-condition filters work consistently across backends."""

    def test_complex_filter_polars_vs_narwhals(self, polars_df, narwhals_df):
        """Test age > 30 AND salary >= 75000 produces same results."""
        # Polars filter
        polars_expr = (pl.col("age") > 30) & (pl.col("salary") >= 75000.0)
        polars_factory = FilterExpressionStrategyFactory()
        polars_strategy = polars_factory.get_strategy(polars_expr)
        polars_result = polars_strategy.filter(polars_df, polars_expr)

        # Narwhals filter
        nw_expr = (nw.col("age") > 30) & (nw.col("salary") >= 75000.0)
        nw_factory = FilterExpressionStrategyFactory()
        nw_strategy = nw_factory.get_strategy(nw_expr)
        nw_result = nw_strategy.filter(narwhals_df, nw_expr)

        # Both should have same row count
        assert len(polars_result) == len(nw.to_native(nw_result))
        assert len(polars_result) == 3

    def test_complex_filter_pandas_vs_polars(self, pandas_df, polars_df):
        """Test complex filter produces same results in Pandas and Polars."""
        # Pandas filter
        pandas_expr = (pandas_df["age"] > 30) & (pandas_df["salary"] >= 75000.0)
        pandas_factory = FilterExpressionStrategyFactory()
        pandas_strategy = pandas_factory.get_strategy(pandas_expr)
        pandas_result = pandas_strategy.filter(pandas_df, pandas_expr)

        # Polars filter
        polars_expr = (pl.col("age") > 30) & (pl.col("salary") >= 75000.0)
        polars_factory = FilterExpressionStrategyFactory()
        polars_strategy = polars_factory.get_strategy(polars_expr)
        polars_result = polars_strategy.filter(polars_df, polars_expr)

        # Both should have same row count
        assert len(pandas_result) == len(polars_result)
        assert len(pandas_result) == 3

    def test_complex_filter_ibis_consistency(self, ibis_table):
        """Test Ibis complex filter produces expected results."""
        ibis_expr = (ibis_table.age > 30) & (ibis_table.salary >= 75000.0)
        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(ibis_expr)
        result = strategy.filter(ibis_table, ibis_expr)

        result_df = result.execute()
        assert len(result_df) == 3


@pytest.mark.integration
class TestCrossBackendBooleanColumn:
    """Test filtering on boolean columns across backends."""

    def test_boolean_filter_polars_vs_narwhals(self, polars_df, narwhals_df):
        """Test is_active == True filter across backends."""
        # Polars filter
        polars_expr = pl.col("is_active") == True
        polars_factory = FilterExpressionStrategyFactory()
        polars_strategy = polars_factory.get_strategy(polars_expr)
        polars_result = polars_strategy.filter(polars_df, polars_expr)

        # Narwhals filter
        nw_expr = nw.col("is_active") == True
        nw_factory = FilterExpressionStrategyFactory()
        nw_strategy = nw_factory.get_strategy(nw_expr)
        nw_result = nw_strategy.filter(narwhals_df, nw_expr)

        # Both should have same row count (7 active employees)
        assert len(polars_result) == len(nw.to_native(nw_result))
        assert len(polars_result) == 7

    def test_boolean_filter_pandas_vs_polars(self, pandas_df, polars_df):
        """Test is_active filter in Pandas vs Polars."""
        # Pandas filter
        pandas_expr = pandas_df["is_active"] == True
        pandas_factory = FilterExpressionStrategyFactory()
        pandas_strategy = pandas_factory.get_strategy(pandas_expr)
        pandas_result = pandas_strategy.filter(pandas_df, pandas_expr)

        # Polars filter
        polars_expr = pl.col("is_active") == True
        polars_factory = FilterExpressionStrategyFactory()
        polars_strategy = polars_factory.get_strategy(polars_expr)
        polars_result = polars_strategy.filter(polars_df, polars_expr)

        # Both should have same row count
        assert len(pandas_result) == len(polars_result)
        assert len(pandas_result) == 7


@pytest.mark.integration
class TestCrossBackendStringFilter:
    """Test filtering on string columns across backends."""

    def test_string_equality_polars_vs_narwhals(self, polars_df, narwhals_df):
        """Test department == 'Engineering' filter across backends."""
        # Polars filter
        polars_expr = pl.col("department") == "Engineering"
        polars_factory = FilterExpressionStrategyFactory()
        polars_strategy = polars_factory.get_strategy(polars_expr)
        polars_result = polars_strategy.filter(polars_df, polars_expr)

        # Narwhals filter
        nw_expr = nw.col("department") == "Engineering"
        nw_factory = FilterExpressionStrategyFactory()
        nw_strategy = nw_factory.get_strategy(nw_expr)
        nw_result = nw_strategy.filter(narwhals_df, nw_expr)

        # Both should have same row count (4 Engineering employees)
        assert len(polars_result) == len(nw.to_native(nw_result))
        assert len(polars_result) == 4

    def test_string_equality_pandas_vs_polars(self, pandas_df, polars_df):
        """Test department filter in Pandas vs Polars."""
        # Pandas filter
        pandas_expr = pandas_df["department"] == "Engineering"
        pandas_factory = FilterExpressionStrategyFactory()
        pandas_strategy = pandas_factory.get_strategy(pandas_expr)
        pandas_result = pandas_strategy.filter(pandas_df, pandas_expr)

        # Polars filter
        polars_expr = pl.col("department") == "Engineering"
        polars_factory = FilterExpressionStrategyFactory()
        polars_strategy = polars_factory.get_strategy(polars_expr)
        polars_result = polars_strategy.filter(polars_df, polars_expr)

        # Both should have same row count
        assert len(pandas_result) == len(polars_result)
        assert len(pandas_result) == 4


@pytest.mark.integration
class TestCrossBackendDataIntegrity:
    """Test that filtered data maintains integrity across backends."""

    def test_filtered_data_values_match(self, polars_df, pandas_df):
        """Test that filtered data contains same values across backends."""
        # Filter both to age > 30
        polars_expr = pl.col("age") > 30
        polars_factory = FilterExpressionStrategyFactory()
        polars_strategy = polars_factory.get_strategy(polars_expr)
        polars_result = polars_strategy.filter(polars_df, polars_expr)

        pandas_expr = pandas_df["age"] > 30
        pandas_factory = FilterExpressionStrategyFactory()
        pandas_strategy = pandas_factory.get_strategy(pandas_expr)
        pandas_result = pandas_strategy.filter(pandas_df, pandas_expr)

        # Convert to pandas for comparison
        polars_as_pandas = polars_result.to_pandas()

        # Check that ages are identical
        polars_ages = sorted(polars_as_pandas["age"].tolist())
        pandas_ages = sorted(pandas_result["age"].tolist())

        assert polars_ages == pandas_ages
        assert polars_ages == [31, 33, 35, 38, 42]

    def test_column_preservation_across_backends(self, polars_df, narwhals_df):
        """Test that all columns are preserved after filtering."""
        # Polars filter
        polars_expr = pl.col("age") > 30
        polars_factory = FilterExpressionStrategyFactory()
        polars_strategy = polars_factory.get_strategy(polars_expr)
        polars_result = polars_strategy.filter(polars_df, polars_expr)

        # Narwhals filter
        nw_expr = nw.col("age") > 30
        nw_factory = FilterExpressionStrategyFactory()
        nw_strategy = nw_factory.get_strategy(nw_expr)
        nw_result = nw_strategy.filter(narwhals_df, nw_expr)

        # Both should preserve all columns
        expected_columns = ["id", "name", "age", "department", "salary", "is_active"]

        polars_columns = polars_result.columns
        nw_native = nw.to_native(nw_result)
        nw_columns = nw_native.columns.tolist()

        assert set(polars_columns) == set(expected_columns)
        assert set(nw_columns) == set(expected_columns)


@pytest.mark.integration
class TestLazyEvaluation:
    """Test filter expressions with lazy evaluation (Polars LazyFrame)."""

    def test_lazy_filter_vs_eager(self, polars_df, polars_lazy):
        """Test lazy filter produces same results as eager."""
        polars_expr = pl.col("age") > 30

        # Eager filter
        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(polars_expr)
        eager_result = strategy.filter(polars_df, polars_expr)

        # Lazy filter
        lazy_result = strategy.filter(polars_lazy, polars_expr)

        # Collect lazy and compare
        lazy_collected = lazy_result.collect()

        assert len(eager_result) == len(lazy_collected)
        assert len(eager_result) == 5
