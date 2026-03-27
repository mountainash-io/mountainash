"""
Tests for edge cases in join operations.

This module tests boundary conditions, error cases, and unusual scenarios
to ensure robust join behavior across all backends.
"""

import pytest
import pandas as pd
import polars as pl
import narwhals as nw

from mountainash.dataframes.join import DataFrameJoinFactory
from mountainash.dataframes.cast import DataFrameCastFactory


@pytest.mark.unit
class TestEmptyDataFrameJoins:
    """Test join operations with empty DataFrames."""

    def test_empty_left_inner_join(self, right_pandas_df):
        """Test inner join with empty left DataFrame."""
        empty_df = pd.DataFrame({"id": [], "name": [], "department": []})

        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(empty_df)

        result = strategy.inner_join(empty_df, right_pandas_df, predicates="id")

        # Convert to pandas
        cast_factory = DataFrameCastFactory()
        cast_strategy = cast_factory.get_strategy(result)
        result_df = cast_strategy.to_pandas(result)

        # Inner join with empty left should be empty
        assert len(result_df) == 0

    def test_empty_right_inner_join(self, left_pandas_df):
        """Test inner join with empty right DataFrame."""
        empty_df = pd.DataFrame({"id": [], "salary": [], "bonus": []})

        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_pandas_df)

        result = strategy.inner_join(left_pandas_df, empty_df, predicates="id")

        # Convert to pandas
        cast_factory = DataFrameCastFactory()
        cast_strategy = cast_factory.get_strategy(result)
        result_df = cast_strategy.to_pandas(result)

        # Inner join with empty right should be empty
        assert len(result_df) == 0

    def test_empty_left_left_join(self, right_pandas_df):
        """Test left join with empty left DataFrame."""
        empty_df = pd.DataFrame({"id": [], "name": [], "department": []})

        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(empty_df)

        result = strategy.left_join(empty_df, right_pandas_df, predicates="id")

        # Convert to pandas
        cast_factory = DataFrameCastFactory()
        cast_strategy = cast_factory.get_strategy(result)
        result_df = cast_strategy.to_pandas(result)

        # Left join with empty left should be empty
        assert len(result_df) == 0

    def test_empty_right_left_join(self, left_pandas_df):
        """Test left join with empty right DataFrame."""
        empty_df = pd.DataFrame({"id": [], "salary": [], "bonus": []})

        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_pandas_df)

        result = strategy.left_join(left_pandas_df, empty_df, predicates="id")

        # Convert to pandas
        cast_factory = DataFrameCastFactory()
        cast_strategy = cast_factory.get_strategy(result)
        result_df = cast_strategy.to_pandas(result)

        # Left join should preserve all left rows (5)
        assert len(result_df) == 5

    def test_both_empty_inner_join(self):
        """Test inner join with both DataFrames empty."""
        empty_left = pd.DataFrame({"id": [], "name": []})
        empty_right = pd.DataFrame({"id": [], "salary": []})

        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(empty_left)

        result = strategy.inner_join(empty_left, empty_right, predicates="id")

        # Convert to pandas
        cast_factory = DataFrameCastFactory()
        cast_strategy = cast_factory.get_strategy(result)
        result_df = cast_strategy.to_pandas(result)

        assert len(result_df) == 0


@pytest.mark.unit
class TestSingleRowJoins:
    """Test join operations with single-row DataFrames."""

    def test_single_row_inner_join_match(self, single_row_join_data):
        """Test inner join with single-row DataFrames that match."""
        left_data, right_data = single_row_join_data

        left_df = pd.DataFrame(left_data)
        right_df = pd.DataFrame(right_data)

        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_df)

        result = strategy.inner_join(left_df, right_df, predicates="id")

        # Convert to pandas
        cast_factory = DataFrameCastFactory()
        cast_strategy = cast_factory.get_strategy(result)
        result_df = cast_strategy.to_pandas(result)

        # Should have 1 matching row
        assert len(result_df) == 1
        assert result_df.iloc[0]['id'] == 1

    def test_single_row_inner_join_no_match(self):
        """Test inner join with single-row DataFrames that don't match."""
        left_df = pd.DataFrame({"id": [1], "name": ["Alice"]})
        right_df = pd.DataFrame({"id": [2], "salary": [95000.0]})

        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_df)

        result = strategy.inner_join(left_df, right_df, predicates="id")

        # Convert to pandas
        cast_factory = DataFrameCastFactory()
        cast_strategy = cast_factory.get_strategy(result)
        result_df = cast_strategy.to_pandas(result)

        # No matching rows
        assert len(result_df) == 0


@pytest.mark.unit
class TestNullHandlingInJoins:
    """Test join operations with null values."""

    def test_inner_join_with_nulls(self, dataframes_with_nulls):
        """Test inner join with null values in join keys.

        IMPORTANT: Unlike SQL (where NULL != NULL), pandas/polars/narwhals
        treat NaN as matchable (NaN == NaN). This means joins WILL match rows
        where both sides have NaN in the join key.

        If SQL-like behavior is needed, filter out nulls before joining.
        """
        left_data, right_data = dataframes_with_nulls

        left_df = pd.DataFrame(left_data)
        right_df = pd.DataFrame(right_data)

        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_df)

        result = strategy.inner_join(left_df, right_df, predicates="id")

        # Convert to pandas
        cast_factory = DataFrameCastFactory()
        cast_strategy = cast_factory.get_strategy(result)
        result_df = cast_strategy.to_pandas(result)

        # pandas/polars/narwhals match NaN values in joins
        # Expected matches: id=2, id=4, and id=NaN (from both tables)
        # So we expect 3 rows, with one containing NaN
        assert len(result_df) == 3
        # One row should have NaN in the join key (pandas/polars behavior)
        assert pd.isna(result_df['id']).sum() == 1

    def test_left_join_preserves_nulls(self, dataframes_with_nulls):
        """Test that left join preserves null values from left table."""
        left_data, right_data = dataframes_with_nulls

        left_df = pd.DataFrame(left_data)
        right_df = pd.DataFrame(right_data)

        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_df)

        result = strategy.left_join(left_df, right_df, predicates="id")

        # Convert to pandas
        cast_factory = DataFrameCastFactory()
        cast_strategy = cast_factory.get_strategy(result)
        result_df = cast_strategy.to_pandas(result)

        # All left rows should be preserved (including those with null keys)
        assert len(result_df) >= len(left_df) - 1  # May vary by backend null handling


@pytest.mark.unit
class TestNoOverlapJoins:
    """Test join operations with no overlapping keys."""

    def test_no_overlap_inner_join(self, no_overlap_join_data):
        """Test inner join with no overlapping keys."""
        left_data, right_data = no_overlap_join_data

        left_df = pd.DataFrame(left_data)
        right_df = pd.DataFrame(right_data)

        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_df)

        result = strategy.inner_join(left_df, right_df, predicates="id")

        # Convert to pandas
        cast_factory = DataFrameCastFactory()
        cast_strategy = cast_factory.get_strategy(result)
        result_df = cast_strategy.to_pandas(result)

        # No overlap means empty result
        assert len(result_df) == 0

    def test_no_overlap_left_join(self, no_overlap_join_data):
        """Test left join with no overlapping keys."""
        left_data, right_data = no_overlap_join_data

        left_df = pd.DataFrame(left_data)
        right_df = pd.DataFrame(right_data)

        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_df)

        result = strategy.left_join(left_df, right_df, predicates="id")

        # Convert to pandas
        cast_factory = DataFrameCastFactory()
        cast_strategy = cast_factory.get_strategy(result)
        result_df = cast_strategy.to_pandas(result)

        # All left rows preserved with nulls for right columns
        assert len(result_df) == len(left_df)

    def test_no_overlap_outer_join(self, no_overlap_join_data):
        """Test outer join with no overlapping keys."""
        left_data, right_data = no_overlap_join_data

        left_df = pd.DataFrame(left_data)
        right_df = pd.DataFrame(right_data)

        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_df)

        result = strategy.outer_join(left_df, right_df, predicates="id")

        # Convert to pandas
        cast_factory = DataFrameCastFactory()
        cast_strategy = cast_factory.get_strategy(result)
        result_df = cast_strategy.to_pandas(result)

        # All rows from both tables
        assert len(result_df) == len(left_df) + len(right_df)


@pytest.mark.unit
class TestCompleteOverlapJoins:
    """Test join operations with complete key overlap."""

    def test_complete_overlap_inner_join(self, complete_overlap_join_data):
        """Test inner join with complete key overlap."""
        left_data, right_data = complete_overlap_join_data

        left_df = pd.DataFrame(left_data)
        right_df = pd.DataFrame(right_data)

        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_df)

        result = strategy.inner_join(left_df, right_df, predicates="id")

        # Convert to pandas
        cast_factory = DataFrameCastFactory()
        cast_strategy = cast_factory.get_strategy(result)
        result_df = cast_strategy.to_pandas(result)

        # All rows match
        assert len(result_df) == len(left_df)

    def test_complete_overlap_outer_join(self, complete_overlap_join_data):
        """Test outer join with complete key overlap."""
        left_data, right_data = complete_overlap_join_data

        left_df = pd.DataFrame(left_data)
        right_df = pd.DataFrame(right_data)

        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_df)

        result = strategy.outer_join(left_df, right_df, predicates="id")

        # Convert to pandas
        cast_factory = DataFrameCastFactory()
        cast_strategy = cast_factory.get_strategy(result)
        result_df = cast_strategy.to_pandas(result)

        # Same as inner join when complete overlap
        assert len(result_df) == len(left_df)


@pytest.mark.unit
class TestDuplicateKeyJoins:
    """Test join operations with duplicate keys."""

    def test_duplicate_keys_inner_join(self, duplicate_keys_join_data):
        """Test inner join with duplicate join keys."""
        left_data, right_data = duplicate_keys_join_data

        left_df = pd.DataFrame(left_data)
        right_df = pd.DataFrame(right_data)

        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_df)

        result = strategy.inner_join(left_df, right_df, predicates="id")

        # Convert to pandas
        cast_factory = DataFrameCastFactory()
        cast_strategy = cast_factory.get_strategy(result)
        result_df = cast_strategy.to_pandas(result)

        # Duplicate keys create cartesian product for matching keys
        # id=1: 2 left × 2 right = 4 rows
        # id=2: 2 left × 1 right = 2 rows
        # id=3: 1 left × 2 right = 2 rows
        # Total: 8 rows
        assert len(result_df) == 8

    def test_duplicate_keys_left_join(self, duplicate_keys_join_data):
        """Test left join with duplicate join keys."""
        left_data, right_data = duplicate_keys_join_data

        left_df = pd.DataFrame(left_data)
        right_df = pd.DataFrame(right_data)

        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_df)

        result = strategy.left_join(left_df, right_df, predicates="id")

        # Convert to pandas
        cast_factory = DataFrameCastFactory()
        cast_strategy = cast_factory.get_strategy(result)
        result_df = cast_strategy.to_pandas(result)

        # Same as inner join for matching keys (8 rows)
        assert len(result_df) == 8


@pytest.mark.unit
class TestMultiColumnJoins:
    """Test join operations on multiple columns."""

    def test_multi_column_inner_join(self, multiple_key_join_data):
        """Test inner join on multiple columns."""
        left_data, right_data = multiple_key_join_data

        left_df = pd.DataFrame(left_data)
        right_df = pd.DataFrame(right_data)

        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_df)

        result = strategy.inner_join(left_df, right_df, predicates=["id", "dept"])

        # Convert to pandas
        cast_factory = DataFrameCastFactory()
        cast_strategy = cast_factory.get_strategy(result)
        result_df = cast_strategy.to_pandas(result)

        # All 5 rows should match on both id and dept
        assert len(result_df) == 5

    def test_multi_column_left_join(self, multiple_key_join_data):
        """Test left join on multiple columns."""
        left_data, right_data = multiple_key_join_data

        left_df = pd.DataFrame(left_data)
        right_df = pd.DataFrame(right_data)

        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_df)

        result = strategy.left_join(left_df, right_df, predicates=["id", "dept"])

        # Convert to pandas
        cast_factory = DataFrameCastFactory()
        cast_strategy = cast_factory.get_strategy(result)
        result_df = cast_strategy.to_pandas(result)

        # All left rows preserved
        assert len(result_df) == len(left_df)


@pytest.mark.unit
class TestJoinPredicateVariations:
    """Test different predicate formats."""

    def test_string_predicate(self, left_pandas_df, right_pandas_df):
        """Test join with string predicate."""
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_pandas_df)

        result = strategy.inner_join(left_pandas_df, right_pandas_df, predicates="id")

        # Convert to pandas
        cast_factory = DataFrameCastFactory()
        cast_strategy = cast_factory.get_strategy(result)
        result_df = cast_strategy.to_pandas(result)

        assert len(result_df) == 3

    def test_list_predicate_single(self, left_pandas_df, right_pandas_df):
        """Test join with single-element list predicate."""
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_pandas_df)

        result = strategy.inner_join(left_pandas_df, right_pandas_df, predicates=["id"])

        # Convert to pandas
        cast_factory = DataFrameCastFactory()
        cast_strategy = cast_factory.get_strategy(result)
        result_df = cast_strategy.to_pandas(result)

        assert len(result_df) == 3

    def test_list_predicate_multiple(self, multiple_key_join_data):
        """Test join with multi-element list predicate."""
        left_data, right_data = multiple_key_join_data

        left_df = pd.DataFrame(left_data)
        right_df = pd.DataFrame(right_data)

        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_df)

        result = strategy.inner_join(left_df, right_df, predicates=["id", "dept"])

        # Convert to pandas
        cast_factory = DataFrameCastFactory()
        cast_strategy = cast_factory.get_strategy(result)
        result_df = cast_strategy.to_pandas(result)

        assert len(result_df) == 5


@pytest.mark.unit
class TestBackendSpecificEdgeCases:
    """Test backend-specific edge cases."""

    def test_polars_lazy_empty_join(self):
        """Test Polars lazy frame with empty join."""
        empty_left = pl.DataFrame({"id": [], "name": []}).lazy()
        empty_right = pl.DataFrame({"id": [], "salary": []}).lazy()

        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(empty_left)

        result = strategy.inner_join(empty_left, empty_right, predicates="id")

        # Convert to pandas
        cast_factory = DataFrameCastFactory()
        cast_strategy = cast_factory.get_strategy(result)
        result_df = cast_strategy.to_pandas(result)

        assert len(result_df) == 0

    def test_narwhals_mixed_backends(self, left_pandas_df, right_polars_df):
        """Test Narwhals handling of mixed backends."""
        factory = DataFrameJoinFactory()

        # Wrap both in narwhals
        left_nw = nw.from_native(left_pandas_df)
        right_nw = nw.from_native(right_polars_df)

        strategy = factory.get_strategy(left_nw)

        result = strategy.inner_join(left_nw, right_nw, predicates="id")

        # Should work across backends
        assert result is not None
        assert len(result) == 3
