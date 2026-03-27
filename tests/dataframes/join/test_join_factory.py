"""
Tests for DataFrameJoinFactory.

This module tests the factory's strategy selection and public API.
Join logic is tested in backend-specific and cross-backend test files.
"""

from __future__ import annotations

import pytest
import pandas as pd
import polars as pl
import ibis
import narwhals as nw

from mountainash.dataframes.join import DataFrameJoinFactory
from mountainash.dataframes.join.join_ibis import IbisJoinStrategy
from mountainash.dataframes.join.join_narwhals import NarwhalsJoinStrategy


@pytest.mark.unit
class TestFactoryStrategySelection:
    """Test that factory selects the correct strategy for each DataFrame type."""

    def test_factory_selects_ibis_strategy(self, left_ibis_table, right_ibis_table):
        """Test factory selects IbisStrategy for Ibis Table."""
        factory = DataFrameJoinFactory()

        strategy = factory.get_strategy(left_ibis_table)
        assert strategy == IbisJoinStrategy

    def test_factory_selects_narwhals_strategy_for_pandas(self, left_pandas_df, right_pandas_df):
        """Test factory selects NarwhalsStrategy for pandas DataFrame."""
        factory = DataFrameJoinFactory()

        strategy = factory.get_strategy(left_pandas_df)
        assert strategy == NarwhalsJoinStrategy

    def test_factory_selects_narwhals_strategy_for_polars(self, left_polars_df, right_polars_df):
        """Test factory selects NarwhalsStrategy for Polars DataFrame."""
        factory = DataFrameJoinFactory()

        strategy = factory.get_strategy(left_polars_df)
        assert strategy == NarwhalsJoinStrategy

    def test_factory_selects_narwhals_strategy_for_polars_lazy(self, left_polars_lazy, right_polars_lazy):
        """Test factory selects NarwhalsStrategy for Polars LazyFrame."""
        factory = DataFrameJoinFactory()

        strategy = factory.get_strategy(left_polars_lazy)
        assert strategy == NarwhalsJoinStrategy

    def test_factory_selects_narwhals_strategy_for_pyarrow(self, left_pyarrow_table, right_pyarrow_table):
        """Test factory selects NarwhalsStrategy for PyArrow Table."""
        factory = DataFrameJoinFactory()

        strategy = factory.get_strategy(left_pyarrow_table)
        assert strategy == NarwhalsJoinStrategy

    def test_factory_selects_narwhals_strategy_for_narwhals(self, left_narwhals_df, right_narwhals_df):
        """Test factory selects NarwhalsStrategy for narwhals DataFrame."""
        factory = DataFrameJoinFactory()

        strategy = factory.get_strategy(left_narwhals_df)
        assert strategy == NarwhalsJoinStrategy


@pytest.mark.unit
class TestFactoryPublicAPI:
    """Test factory's public API methods for different join types."""

    def test_inner_join_api(self, left_pandas_df, right_pandas_df):
        """Test public inner_join() API."""
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_pandas_df)

        result = strategy.inner_join(left_pandas_df, right_pandas_df, predicates="id")

        # Verify result is a DataFrame
        assert result is not None
        # Inner join should only include matching keys (2, 3, 4)
        assert len(result) == 3

    def test_left_join_api(self, left_pandas_df, right_pandas_df):
        """Test public left_join() API."""
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_pandas_df)

        result = strategy.left_join(left_pandas_df, right_pandas_df, predicates="id")

        # Verify result is a DataFrame
        assert result is not None
        # Left join should include all left rows (5)
        assert len(result) == 5

    def test_outer_join_api(self, left_pandas_df, right_pandas_df):
        """Test public outer_join() API."""
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_pandas_df)

        result = strategy.outer_join(left_pandas_df, right_pandas_df, predicates="id")

        # Verify result is a DataFrame
        assert result is not None
        # Outer join should include all rows from both tables
        # Left: 1, 2, 3, 4, 5; Right: 2, 3, 4, 6, 7 -> Union: 1, 2, 3, 4, 5, 6, 7 = 7 rows
        assert len(result) == 7

    def test_inner_join_with_polars(self, left_polars_df, right_polars_df):
        """Test inner join with Polars DataFrames."""
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_polars_df)

        result = strategy.inner_join(left_polars_df, right_polars_df, predicates="id")

        assert isinstance(result, (pl.DataFrame, nw.DataFrame))
        assert len(result) == 3

    def test_left_join_with_ibis(self, left_ibis_table, right_ibis_table):
        """Test left join with Ibis Tables."""
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_ibis_table)

        result = strategy.left_join(left_ibis_table, right_ibis_table, predicates="id")

        assert result is not None
        # Ibis returns lazy expressions, may need to execute
        # Just verify we got a result back
        assert hasattr(result, 'columns') or hasattr(result, 'schema')


@pytest.mark.unit
class TestFactoryErrorHandling:
    """Test factory error handling for unsupported types and edge cases."""

    def test_factory_handles_unknown_type(self):
        """Test factory behavior with unsupported DataFrame type."""
        # A list is not a supported DataFrame type
        unsupported = [{"id": 1, "name": "Alice"}]

        factory = DataFrameJoinFactory()

        # Factory should either return None or raise an error
        with pytest.raises((ValueError, TypeError, KeyError, AttributeError)):
            strategy = factory.get_strategy(unsupported)

    def test_factory_handles_none_input(self):
        """Test factory behavior with None input."""
        factory = DataFrameJoinFactory()

        # Should raise an error or return None
        with pytest.raises((ValueError, TypeError, AttributeError)):
            strategy = factory.get_strategy(None)


@pytest.mark.unit
class TestFactoryConsistency:
    """Test factory behaves consistently across instances and calls."""

    def test_factory_instances_independent(self, left_pandas_df, right_pandas_df):
        """Test that separate factory instances work independently."""
        factory1 = DataFrameJoinFactory()
        factory2 = DataFrameJoinFactory()

        strategy1 = factory1.get_strategy(left_pandas_df)
        strategy2 = factory2.get_strategy(left_pandas_df)

        # Both should select the same strategy
        assert strategy1 == strategy2

    def test_factory_multiple_calls_consistent(self, left_pandas_df, right_pandas_df):
        """Test that multiple calls to same factory are consistent."""
        factory = DataFrameJoinFactory()

        result1 = factory.get_strategy(left_pandas_df)
        result2 = factory.get_strategy(left_pandas_df)

        assert result1 == result2

    def test_factory_same_strategy_different_dataframes(self, left_pandas_df, right_pandas_df):
        """Test factory selects same strategy for same DataFrame type."""
        factory = DataFrameJoinFactory()

        strategy_left = factory.get_strategy(left_pandas_df)
        strategy_right = factory.get_strategy(right_pandas_df)

        # Both pandas DataFrames should get same strategy
        assert strategy_left == strategy_right


@pytest.mark.unit
class TestFactoryCaching:
    """Test factory's lazy loading and caching behavior."""

    def test_factory_lazy_loading(self, left_pandas_df):
        """Test that factory uses lazy loading for strategies."""
        # Create fresh factory
        factory = DataFrameJoinFactory()

        # First call should trigger lazy loading
        strategy1 = factory.get_strategy(left_pandas_df)
        assert strategy1 is not None

        # Second call should use cached strategy
        strategy2 = factory.get_strategy(left_pandas_df)
        assert strategy2 == strategy1

    def test_factory_handles_multiple_backends(self, left_pandas_df, left_polars_df, left_ibis_table):
        """Test factory correctly handles multiple backend types."""
        factory = DataFrameJoinFactory()

        pandas_strategy = factory.get_strategy(left_pandas_df)
        polars_strategy = factory.get_strategy(left_polars_df)
        ibis_strategy = factory.get_strategy(left_ibis_table)

        # Pandas and Polars should use NarwhalsStrategy
        assert pandas_strategy == NarwhalsJoinStrategy
        assert polars_strategy == NarwhalsJoinStrategy

        # Ibis should use IbisStrategy
        assert ibis_strategy == IbisJoinStrategy
