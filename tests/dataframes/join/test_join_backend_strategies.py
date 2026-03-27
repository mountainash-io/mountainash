"""
Tests for backend-specific join strategies.

This module tests the backend-specific join implementations through the factory pattern.
Since strategies use class methods and cannot be directly instantiated, all tests use
the factory's get_strategy() method.
"""

from __future__ import annotations

import pytest
import pandas as pd
import polars as pl
import ibis
import narwhals as nw

from mountainash.dataframes.join import DataFrameJoinFactory
from mountainash.dataframes import DataFrameUtils


@pytest.mark.unit
class TestIbisStrategyViaFactory:
    """Test Ibis join strategy through factory pattern."""

    def test_inner_join_basic(self, left_ibis_table, right_ibis_table):
        """Test basic inner join with Ibis tables."""
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_ibis_table)
        result = strategy.inner_join(left_ibis_table, right_ibis_table, predicates="id")

        # Verify result is an Ibis table
        assert isinstance(result, ibis.expr.types.Table)

        # Execute and verify data
        result_df = result.execute()
        assert len(result_df) == 3  # Only matching keys: 2, 3, 4
        assert "name" in result_df.columns
        assert "salary" in result_df.columns

    def test_left_join_basic(self, left_ibis_table, right_ibis_table):
        """Test basic left join with Ibis tables."""
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_ibis_table)
        result = strategy.left_join(left_ibis_table, right_ibis_table, predicates="id")

        assert isinstance(result, ibis.expr.types.Table)

        # Execute and verify
        result_df = result.execute()
        assert len(result_df) == 5  # All left rows

    def test_outer_join_basic(self, left_ibis_table, right_ibis_table):
        """Test basic outer join with Ibis tables."""
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_ibis_table)
        result = strategy.outer_join(left_ibis_table, right_ibis_table, predicates="id")

        assert isinstance(result, ibis.expr.types.Table)

        # Execute and verify
        result_df = result.execute()
        assert len(result_df) == 7  # All rows from both tables

    def test_ibis_join_with_kwargs(self, left_ibis_table, right_ibis_table):
        """Test Ibis join with additional kwargs."""
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_ibis_table)

        # Ibis supports suffixes for overlapping columns
        result = strategy.inner_join(
            left_ibis_table,
            right_ibis_table,
            predicates="id",
            lname="left_{name}",
            rname="right_{name}",
        )

        assert isinstance(result, ibis.expr.types.Table)


@pytest.mark.unit
class TestNarwhalsStrategyViaFactory:
    """Test Narwhals join strategy through factory pattern."""

    def test_inner_join_pandas(self, left_pandas_df, right_pandas_df):
        """Test inner join with pandas DataFrames via Narwhals."""
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_pandas_df)
        result = strategy.inner_join(left_pandas_df, right_pandas_df, predicates="id")

        # Result should be a narwhals DataFrame
        assert isinstance(result, nw.DataFrame)

        # Convert to native and verify
        result_native = nw.to_native(result)
        assert len(result_native) == 3

    def test_inner_join_polars(self, left_polars_df, right_polars_df):
        """Test inner join with Polars DataFrames via Narwhals."""
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_polars_df)
        result = strategy.inner_join(left_polars_df, right_polars_df, predicates="id")

        assert isinstance(result, nw.DataFrame)
        result_native = nw.to_native(result)
        assert len(result_native) == 3

    def test_left_join_pandas(self, left_pandas_df, right_pandas_df):
        """Test left join with pandas DataFrames."""
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_pandas_df)
        result = strategy.left_join(left_pandas_df, right_pandas_df, predicates="id")

        assert isinstance(result, nw.DataFrame)
        result_native = nw.to_native(result)
        assert len(result_native) == 5

    def test_left_join_polars(self, left_polars_df, right_polars_df):
        """Test left join with Polars DataFrames."""
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_polars_df)
        result = strategy.left_join(left_polars_df, right_polars_df, predicates="id")

        assert isinstance(result, nw.DataFrame)
        result_native = nw.to_native(result)
        assert len(result_native) == 5

    def test_outer_join_pandas(self, left_pandas_df, right_pandas_df):
        """Test outer join with pandas DataFrames."""
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_pandas_df)
        result = strategy.outer_join(left_pandas_df, right_pandas_df, predicates="id")

        assert isinstance(result, nw.DataFrame)
        result_native = nw.to_native(result)
        assert len(result_native) == 7

    def test_outer_join_polars(self, left_polars_df, right_polars_df):
        """Test outer join with Polars DataFrames."""
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_polars_df)
        result = strategy.outer_join(left_polars_df, right_polars_df, predicates="id")

        assert isinstance(result, nw.DataFrame)
        result_native = nw.to_native(result)
        assert len(result_native) == 7

    def test_narwhals_lazy_frame_collection(self, left_polars_lazy, right_polars_lazy):
        """Test that same-backend LazyFrames preserve lazy evaluation."""
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_polars_lazy)
        result = strategy.inner_join(left_polars_lazy, right_polars_lazy, predicates="id")

        # Result should be LazyFrame for same-backend joins
        assert isinstance(result, nw.LazyFrame)

        # Verify correctness when collected
        native_result = nw.to_native(result)
        collected = native_result.collect()
        assert len(collected) == 3

    def test_narwhals_already_wrapped(self, left_narwhals_df, right_narwhals_df):
        """Test that already-wrapped narwhals DataFrames work correctly."""
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_narwhals_df)
        result = strategy.inner_join(left_narwhals_df, right_narwhals_df, predicates="id")

        assert isinstance(result, nw.DataFrame)


@pytest.mark.unit
class TestBackendTypeIdentification:
    """Test backend type identification through factory."""

    def test_ibis_backend_identified(self, left_ibis_table):
        """Test that Ibis tables are correctly identified."""
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_ibis_table)

        # Strategy should be IbisJoinStrategy
        from mountainash.dataframes.join.join_ibis import IbisJoinStrategy
        assert strategy == IbisJoinStrategy

    def test_pandas_backend_identified(self, left_pandas_df):
        """Test that pandas DataFrames are correctly identified."""
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_pandas_df)

        # Strategy should be NarwhalsJoinStrategy
        from mountainash.dataframes.join.join_narwhals import NarwhalsJoinStrategy
        assert strategy == NarwhalsJoinStrategy

    def test_polars_backend_identified(self, left_polars_df):
        """Test that Polars DataFrames are correctly identified."""
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_polars_df)

        from mountainash.dataframes.join.join_narwhals import NarwhalsJoinStrategy
        assert strategy == NarwhalsJoinStrategy


@pytest.mark.unit
class TestJoinDataIntegrity:
    """Test that joins preserve data integrity."""

    def test_inner_join_preserves_matching_data(self, left_pandas_df, right_pandas_df):
        """Test that inner join preserves data for matching keys."""
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_pandas_df)
        result = strategy.inner_join(left_pandas_df, right_pandas_df, predicates="id")

        result_native = nw.to_native(result)

        # Check that id=2 row has correct data from both tables
        row_2 = result_native[result_native['id'] == 2].iloc[0]
        assert row_2['name'] == "Bob"
        assert row_2['salary'] == 75000.0

    def test_left_join_preserves_all_left_data(self, left_pandas_df, right_pandas_df):
        """Test that left join preserves all left table data."""
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_pandas_df)
        result = strategy.left_join(left_pandas_df, right_pandas_df, predicates="id")

        result_native = nw.to_native(result)

        # Check that all left IDs are present
        left_ids = set(left_pandas_df['id'])
        result_ids = set(result_native['id'])
        assert left_ids.issubset(result_ids)

    def test_outer_join_includes_all_data(self, left_pandas_df, right_pandas_df):
        """Test that outer join includes data from both tables.

        Note: Outer joins use coalesce_keys=True by default, which merges duplicate
        join key columns (id and id_right) into a single column. This ensures all
        IDs are in one column without data loss.
        """
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_pandas_df)
        result = strategy.outer_join(left_pandas_df, right_pandas_df, predicates="id")

        result_native = nw.to_native(result)

        # Check that all IDs from both tables are present
        # With coalescing, all IDs should be in the 'id' column (no 'id_right')
        left_ids = set(left_pandas_df['id'])
        right_ids = set(right_pandas_df['id'])

        # Get result IDs, filtering out any NaN values
        import pandas as pd
        result_ids = set(result_native['id'].dropna()) if isinstance(result_native, pd.DataFrame) else set(result_native['id'])

        all_ids = left_ids.union(right_ids)
        assert all_ids == result_ids


@pytest.mark.unit
class TestBackendSpecificFeatures:
    """Test backend-specific join features."""

    def test_polars_lazy_evaluation(self, left_polars_lazy, right_polars_lazy):
        """Test that Polars lazy frames preserve lazy evaluation."""
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_polars_lazy)

        # Join should work with lazy frames
        result = strategy.inner_join(left_polars_lazy, right_polars_lazy, predicates="id")

        # Result should be lazy for same-backend joins
        assert isinstance(result, nw.LazyFrame)

        # Verify correctness when collected
        native_result = nw.to_native(result)
        collected = native_result.collect()
        assert len(collected) == 3

    def test_ibis_cross_backend_join(self, left_data_standard, right_data_standard):
        """Test Ibis strategy with cross-backend data."""
        factory = DataFrameJoinFactory()

        # Create tables
        left_table = DataFrameUtils.create_ibis(left_data_standard)
        right_table = DataFrameUtils.create_ibis(right_data_standard)

        strategy = factory.get_strategy(left_table)

        # Join should work regardless of backend
        result = strategy.inner_join(left_table, right_table, predicates="id")
        assert isinstance(result, ibis.expr.types.Table)
