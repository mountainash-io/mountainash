"""
Tests for FilterExpressionStrategyFactory.

This module tests the factory's strategy selection and public API.
Filter logic is tested in backend-specific and cross-backend test files.
"""

from __future__ import annotations

import pytest
import pandas as pd
import polars as pl
import ibis
import narwhals as nw

from mountainash.dataframes.filter_expressions import FilterExpressionStrategyFactory
from mountainash.dataframes.filter_expressions.filter_expressions_ibis import IbisFilterExpressionStrategy
from mountainash.dataframes.filter_expressions.filter_expressions_narwhals import NarwhalsFilterExpressionStrategy
from mountainash.dataframes.filter_expressions.filter_expressions_polars import PolarsFilterExpressionStrategy
from mountainash.dataframes.filter_expressions.filter_expressions_pandas import PandasFilterExpressionStrategy


@pytest.mark.unit
class TestFactoryStrategySelection:
    """Test that factory selects the correct strategy for each expression type."""

    def test_factory_selects_ibis_strategy(self, ibis_expression_single_column):
        """Test factory selects IbisStrategy for Ibis expression."""
        factory = FilterExpressionStrategyFactory()

        strategy = factory.get_strategy(ibis_expression_single_column)
        assert strategy == IbisFilterExpressionStrategy

    def test_factory_selects_polars_strategy(self, polars_expression_single_column):
        """Test factory selects PolarsStrategy for Polars expression."""
        factory = FilterExpressionStrategyFactory()

        strategy = factory.get_strategy(polars_expression_single_column)
        assert strategy == PolarsFilterExpressionStrategy

    def test_factory_selects_narwhals_strategy(self, narwhals_expression_single_column):
        """Test factory selects NarwhalsStrategy for narwhals expression."""
        factory = FilterExpressionStrategyFactory()

        strategy = factory.get_strategy(narwhals_expression_single_column)
        assert strategy == NarwhalsFilterExpressionStrategy

    def test_factory_selects_pandas_strategy(self, pandas_expression_single_column):
        """Test factory selects PandasStrategy for pandas Series."""
        factory = FilterExpressionStrategyFactory()

        strategy = factory.get_strategy(pandas_expression_single_column)
        assert strategy == PandasFilterExpressionStrategy


@pytest.mark.unit
class TestFactoryPublicAPI:
    """Test factory's public API methods for different filter operations."""

    def test_filter_api_polars(self, polars_df, polars_expression_single_column):
        """Test public filter() API with Polars."""
        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(polars_expression_single_column)

        result = strategy.filter(polars_df, polars_expression_single_column)

        # Verify result is a DataFrame
        assert result is not None
        assert isinstance(result, (pl.DataFrame, pl.LazyFrame))
        # Should filter to rows where age > 30 (5 rows: ages 35, 42, 31, 38, 33)
        assert len(result) == 5

    def test_filter_api_narwhals(self, narwhals_df, narwhals_expression_single_column):
        """Test public filter() API with Narwhals."""
        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(narwhals_expression_single_column)

        result = strategy.filter(narwhals_df, narwhals_expression_single_column)

        # Verify result
        assert result is not None
        # Convert to native to check length
        result_native = nw.to_native(result) if isinstance(result, nw.DataFrame) else result
        assert len(result_native) == 5

    def test_filter_api_ibis(self, ibis_table, ibis_expression_single_column):
        """Test public filter() API with Ibis."""
        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(ibis_expression_single_column)

        result = strategy.filter(ibis_table, ibis_expression_single_column)

        # Verify result is an Ibis table
        assert result is not None
        assert isinstance(result, ibis.expr.types.Table)

    def test_filter_api_pandas(self, pandas_df, pandas_expression_single_column):
        """Test public filter() API with Pandas."""
        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(pandas_expression_single_column)

        result = strategy.filter(pandas_df, pandas_expression_single_column)

        # Verify result
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 5


@pytest.mark.unit
class TestFactoryErrorHandling:
    """Test factory error handling for unsupported types and edge cases."""

    def test_factory_handles_unknown_type(self):
        """Test factory behavior with unsupported expression type."""
        # A simple string is not a supported expression type
        unsupported = "age > 30"

        factory = FilterExpressionStrategyFactory()

        # Factory should either return None or raise an error
        with pytest.raises((ValueError, TypeError, KeyError, AttributeError)):
            strategy = factory.get_strategy(unsupported)

    def test_factory_handles_none_input(self):
        """Test factory behavior with None input."""
        factory = FilterExpressionStrategyFactory()

        # Should raise an error or return None
        with pytest.raises((ValueError, TypeError, AttributeError)):
            strategy = factory.get_strategy(None)


@pytest.mark.unit
class TestFactoryConsistency:
    """Test factory behaves consistently across instances and calls."""

    def test_factory_instances_independent(self, polars_expression_single_column):
        """Test that separate factory instances work independently."""
        factory1 = FilterExpressionStrategyFactory()
        factory2 = FilterExpressionStrategyFactory()

        strategy1 = factory1.get_strategy(polars_expression_single_column)
        strategy2 = factory2.get_strategy(polars_expression_single_column)

        # Both should select the same strategy
        assert strategy1 == strategy2

    def test_factory_multiple_calls_consistent(self, polars_expression_single_column):
        """Test that multiple calls to same factory are consistent."""
        factory = FilterExpressionStrategyFactory()

        result1 = factory.get_strategy(polars_expression_single_column)
        result2 = factory.get_strategy(polars_expression_single_column)

        assert result1 == result2

    def test_factory_same_strategy_different_expressions(self, polars_expression_single_column, polars_expression_multiple_conditions):
        """Test factory selects same strategy for same expression type."""
        factory = FilterExpressionStrategyFactory()

        strategy1 = factory.get_strategy(polars_expression_single_column)
        strategy2 = factory.get_strategy(polars_expression_multiple_conditions)

        # Both polars expressions should get same strategy
        assert strategy1 == strategy2


@pytest.mark.unit
class TestFactoryCaching:
    """Test factory's lazy loading and caching behavior."""

    def test_factory_lazy_loading(self, polars_expression_single_column):
        """Test that factory uses lazy loading for strategies."""
        # Create fresh factory
        factory = FilterExpressionStrategyFactory()

        # First call should trigger lazy loading
        strategy1 = factory.get_strategy(polars_expression_single_column)
        assert strategy1 is not None

        # Second call should use cached strategy
        strategy2 = factory.get_strategy(polars_expression_single_column)
        assert strategy2 == strategy1

    def test_factory_handles_multiple_backends(self, polars_expression_single_column, narwhals_expression_single_column, ibis_expression_single_column):
        """Test factory correctly handles multiple expression types."""
        factory = FilterExpressionStrategyFactory()

        polars_strategy = factory.get_strategy(polars_expression_single_column)
        narwhals_strategy = factory.get_strategy(narwhals_expression_single_column)
        ibis_strategy = factory.get_strategy(ibis_expression_single_column)

        # Different expression types should use different strategies
        assert polars_strategy == PolarsFilterExpressionStrategy
        assert narwhals_strategy == NarwhalsFilterExpressionStrategy
        assert ibis_strategy == IbisFilterExpressionStrategy
