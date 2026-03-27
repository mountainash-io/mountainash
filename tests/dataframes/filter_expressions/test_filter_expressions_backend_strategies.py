"""
Tests for backend-specific filter expression strategies.

This module tests the backend-specific filter implementations through the factory pattern.
Since strategies use class methods and cannot be directly instantiated, all tests use
the factory's get_strategy() method.
"""

from __future__ import annotations

import pytest
import pandas as pd
import polars as pl
import ibis
import narwhals as nw

from mountainash.dataframes.filter_expressions import FilterExpressionStrategyFactory
from mountainash.dataframes import DataFrameUtils


@pytest.mark.unit
class TestIbisStrategyViaFactory:
    """Test Ibis filter expression strategy through factory pattern."""

    def test_filter_single_condition(self, ibis_table, ibis_expression_single_column):
        """Test basic filter with single condition using Ibis."""
        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(ibis_expression_single_column)
        result = strategy.filter(ibis_table, ibis_expression_single_column)

        # Verify result is an Ibis table
        assert isinstance(result, ibis.expr.types.Table)

        # Execute and verify data
        result_df = result.execute()
        assert len(result_df) == 5  # Ages > 30: 35, 42, 31, 38, 33

    def test_filter_multiple_conditions(self, ibis_table, ibis_expression_multiple_conditions):
        """Test filter with multiple conditions using Ibis."""
        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(ibis_expression_multiple_conditions)
        result = strategy.filter(ibis_table, ibis_expression_multiple_conditions)

        assert isinstance(result, ibis.expr.types.Table)

        # Execute and verify
        result_df = result.execute()
        # Age > 30 AND salary >= 75000: rows 3, 5, 6 (Charlie, Eve, Frank)
        assert len(result_df) == 3

    def test_filter_returns_correct_columns(self, ibis_table, ibis_expression_single_column):
        """Test that filtered result preserves all columns."""
        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(ibis_expression_single_column)
        result = strategy.filter(ibis_table, ibis_expression_single_column)

        result_df = result.execute()
        expected_columns = ["id", "name", "age", "department", "salary", "is_active"]
        assert all(col in result_df.columns for col in expected_columns)

    def test_can_handle_ibis_expression(self, ibis_expression_single_column):
        """Test can_handle() method for Ibis expressions."""
        from mountainash.dataframes.filter_expressions.filter_expressions_ibis import IbisFilterExpressionStrategy

        assert IbisFilterExpressionStrategy.can_handle(ibis_expression_single_column) is True
        assert IbisFilterExpressionStrategy.can_handle("not an expression") is False


@pytest.mark.unit
class TestPolarsStrategyViaFactory:
    """Test Polars filter expression strategy through factory pattern."""

    def test_filter_single_condition(self, polars_df, polars_expression_single_column):
        """Test basic filter with single condition using Polars."""
        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(polars_expression_single_column)
        result = strategy.filter(polars_df, polars_expression_single_column)

        # Result should be a Polars DataFrame
        assert isinstance(result, (pl.DataFrame, pl.LazyFrame))
        assert len(result) == 5

    def test_filter_multiple_conditions(self, polars_df, polars_expression_multiple_conditions):
        """Test filter with multiple conditions using Polars."""
        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(polars_expression_multiple_conditions)
        result = strategy.filter(polars_df, polars_expression_multiple_conditions)

        assert isinstance(result, (pl.DataFrame, pl.LazyFrame))
        assert len(result) == 3

    def test_filter_with_lazy_frame(self, polars_lazy, polars_expression_single_column):
        """Test filter with Polars LazyFrame."""
        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(polars_expression_single_column)
        result = strategy.filter(polars_lazy, polars_expression_single_column)

        # Should return LazyFrame
        assert isinstance(result, pl.LazyFrame)

        # Collect and verify
        collected = result.collect()
        assert len(collected) == 5

    def test_can_handle_polars_expression(self, polars_expression_single_column):
        """Test can_handle() method for Polars expressions."""
        from mountainash.dataframes.filter_expressions.filter_expressions_polars import PolarsFilterExpressionStrategy

        assert PolarsFilterExpressionStrategy.can_handle(polars_expression_single_column) is True
        assert PolarsFilterExpressionStrategy.can_handle("not an expression") is False


@pytest.mark.unit
class TestNarwhalsStrategyViaFactory:
    """Test Narwhals filter expression strategy through factory pattern."""

    def test_filter_single_condition(self, narwhals_df, narwhals_expression_single_column):
        """Test basic filter with single condition using Narwhals."""
        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(narwhals_expression_single_column)
        result = strategy.filter(narwhals_df, narwhals_expression_single_column)

        # Result should be a narwhals DataFrame
        assert isinstance(result, nw.DataFrame)

        # Convert to native and verify
        result_native = nw.to_native(result)
        assert len(result_native) == 5

    def test_filter_multiple_conditions(self, narwhals_df, narwhals_expression_multiple_conditions):
        """Test filter with multiple conditions using Narwhals."""
        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(narwhals_expression_multiple_conditions)
        result = strategy.filter(narwhals_df, narwhals_expression_multiple_conditions)

        assert isinstance(result, nw.DataFrame)
        result_native = nw.to_native(result)
        assert len(result_native) == 3

    def test_filter_with_native_pandas(self, pandas_df, narwhals_expression_single_column):
        """Test Narwhals strategy can handle native pandas DataFrame."""
        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(narwhals_expression_single_column)

        # Should convert pandas to narwhals, filter, and return
        result = strategy.filter(pandas_df, narwhals_expression_single_column)

        # Should return pandas DataFrame (narwhals returns to native)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 5

    def test_filter_with_native_polars(self, polars_df, narwhals_expression_single_column):
        """Test Narwhals strategy can handle native polars DataFrame."""
        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(narwhals_expression_single_column)

        # Should convert polars to narwhals, filter, and return
        result = strategy.filter(polars_df, narwhals_expression_single_column)

        # Should return polars DataFrame (narwhals returns to native)
        assert isinstance(result, pl.DataFrame)
        assert len(result) == 5

    def test_can_handle_narwhals_expression(self, narwhals_expression_single_column):
        """Test can_handle() method for Narwhals expressions."""
        from mountainash.dataframes.filter_expressions.filter_expressions_narwhals import NarwhalsFilterExpressionStrategy

        assert NarwhalsFilterExpressionStrategy.can_handle(narwhals_expression_single_column) is True
        assert NarwhalsFilterExpressionStrategy.can_handle("not an expression") is False


@pytest.mark.unit
class TestPandasStrategyViaFactory:
    """Test Pandas filter expression strategy through factory pattern."""

    def test_filter_single_condition(self, pandas_df, pandas_expression_single_column):
        """Test basic filter with single condition using Pandas."""
        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(pandas_expression_single_column)
        result = strategy.filter(pandas_df, pandas_expression_single_column)

        # Result should be a pandas DataFrame
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 5

    def test_filter_multiple_conditions(self, pandas_df):
        """Test filter with multiple conditions using Pandas."""
        # Create pandas boolean expression
        expression = (pandas_df["age"] > 30) & (pandas_df["salary"] >= 75000.0)

        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(expression)
        result = strategy.filter(pandas_df, expression)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3

    def test_filter_returns_correct_columns(self, pandas_df, pandas_expression_single_column):
        """Test that filtered result preserves all columns."""
        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(pandas_expression_single_column)
        result = strategy.filter(pandas_df, pandas_expression_single_column)

        expected_columns = ["id", "name", "age", "department", "salary", "is_active"]
        assert all(col in result.columns for col in expected_columns)

    def test_can_handle_pandas_series(self, pandas_expression_single_column):
        """Test can_handle() method for Pandas Series."""
        from mountainash.dataframes.filter_expressions.filter_expressions_pandas import PandasFilterExpressionStrategy

        assert PandasFilterExpressionStrategy.can_handle(pandas_expression_single_column) is True
        assert PandasFilterExpressionStrategy.can_handle("not a series") is False


@pytest.mark.unit
class TestStrategyTypeDetection:
    """Test that strategies correctly identify their expression types."""

    def test_ibis_expression_type(self):
        """Test Ibis strategy reports correct expression type."""
        from mountainash.dataframes.filter_expressions.filter_expressions_ibis import IbisFilterExpressionStrategy
        from mountainash.dataframes.constants import CONST_EXPRESSION_TYPE

        assert IbisFilterExpressionStrategy.expression_type() == CONST_EXPRESSION_TYPE.IBIS

    def test_polars_expression_type(self):
        """Test Polars strategy reports correct expression type."""
        from mountainash.dataframes.filter_expressions.filter_expressions_polars import PolarsFilterExpressionStrategy
        from mountainash.dataframes.constants import CONST_EXPRESSION_TYPE

        assert PolarsFilterExpressionStrategy.expression_type() == CONST_EXPRESSION_TYPE.POLARS

    def test_narwhals_expression_type(self):
        """Test Narwhals strategy reports correct expression type."""
        from mountainash.dataframes.filter_expressions.filter_expressions_narwhals import NarwhalsFilterExpressionStrategy
        from mountainash.dataframes.constants import CONST_EXPRESSION_TYPE

        assert NarwhalsFilterExpressionStrategy.expression_type() == CONST_EXPRESSION_TYPE.NARWHALS

    def test_pandas_expression_type(self):
        """Test Pandas strategy reports correct expression type."""
        from mountainash.dataframes.filter_expressions.filter_expressions_pandas import PandasFilterExpressionStrategy
        from mountainash.dataframes.constants import CONST_EXPRESSION_TYPE

        assert PandasFilterExpressionStrategy.expression_type() == CONST_EXPRESSION_TYPE.PANDAS
