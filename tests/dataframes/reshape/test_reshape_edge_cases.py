"""Tests for reshape module edge cases and error handling.

This module comprehensively tests edge cases, boundary conditions, and error scenarios
to ensure robust behavior across all reshape operations.
"""

import pytest
from pytest_check import check
import pandas as pd
import polars as pl

from mountainash.dataframes.select import DataFrameSelectFactory
from mountainash.dataframes.introspect import DataFrameIntrospectFactory


BACKEND_FIXTURES = [
    "sample_pandas_df",
    "sample_polars_df",
    "sample_pyarrow_table",
    "real_ibis_table",
    "sample_narwhals_df"
]


@pytest.mark.unit
class TestEmptyDataFrameOperations:
    """Test reshape operations on empty DataFrames."""

    def test_empty_df_column_names(self, empty_dataframes):
        """Test column_names() works on empty DataFrames."""
        for backend_name, df in empty_dataframes.items():
            strategy = DataFrameSelectFactory.get_strategy(df)
            columns = strategy.column_names(df)

            check.is_instance(columns, list, msg=f"{backend_name} didn't return list")
            check.greater_equal(len(columns), 0, msg=f"{backend_name} returned negative column count")

    def test_empty_df_count(self, empty_dataframes):
        """Test count() returns 0 for empty DataFrames."""
        for backend_name, df in empty_dataframes.items():
            strategy = DataFrameSelectFactory.get_strategy(df)
            count = strategy.count(df)

            check.equal(count, 0, msg=f"{backend_name} empty df count should be 0")

    def test_empty_df_head(self, empty_dataframes):
        """Test head() works on empty DataFrames."""
        for backend_name, df in empty_dataframes.items():
            strategy = DataFrameSelectFactory.get_strategy(df)
            result = strategy.head(df, 5)

            result_count = strategy.count(result)
            check.equal(result_count, 0, msg=f"{backend_name} empty df head should return empty")

    def test_empty_df_select(self, empty_dataframes):
        """Test select() works on empty DataFrames."""
        for backend_name, df in empty_dataframes.items():
            strategy = DataFrameSelectFactory.get_strategy(df)
            result = strategy.select(df, [])

            check.is_not_none(result, msg=f"{backend_name} select on empty df returned None")

    def test_empty_df_drop(self, empty_dataframes):
        """Test drop() works on empty DataFrames."""
        for backend_name, df in empty_dataframes.items():
            strategy = DataFrameSelectFactory.get_strategy(df)
            result = strategy.drop(df, ["nonexistent"])

            check.is_not_none(result, msg=f"{backend_name} drop on empty df returned None")

    # def test_empty_df_get_first_row(self, empty_dataframes):
    #     """Test get_first_row_as_dict() handles empty DataFrames gracefully."""
    #     for backend_name, df in empty_dataframes.items():
    #         strategy = DataFrameSelectFactory.get_strategy(df)
    #         result = strategy.get_first_row_as_dict(df)

    #         check.is_instance(result, dict, msg=f"{backend_name} should return dict for empty df")


@pytest.mark.unit
class TestSingleRowOperations:
    """Test operations on single-row DataFrames."""

    def test_single_row_count(self, single_row_dataframes):
        """Test count() returns 1 for single-row DataFrames."""
        for backend_name, df in single_row_dataframes.items():
            strategy = DataFrameSelectFactory.get_strategy(df)
            count = strategy.count(df)

            check.equal(count, 1, msg=f"{backend_name} single row count should be 1")

    def test_single_row_head(self, single_row_dataframes):
        """Test head() on single-row DataFrames."""
        for backend_name, df in single_row_dataframes.items():
            strategy = DataFrameSelectFactory.get_strategy(df)

            # head(0) should return empty
            result_zero = strategy.head(df, 0)
            check.equal(strategy.count(result_zero), 0)

            # head(1) should return the single row
            result_one = strategy.head(df, 1)
            check.equal(strategy.count(result_one), 1)

            # head(10) should return the single row (not error)
            result_many = strategy.head(df, 10)
            check.equal(strategy.count(result_many), 1)

    def test_single_row_split_batches(self, single_row_dataframes):
        """Test split_in_batches() on single-row DataFrames."""
        for backend_name, df in single_row_dataframes.items():
            strategy = DataFrameSelectFactory.get_strategy(df)

            batches, total = strategy.split_in_batches(df, batch_size=1)

            check.equal(len(batches), 1, msg=f"{backend_name} should return 1 batch")
            check.equal(total, 1, msg=f"{backend_name} should report 1 total row")
            check.equal(strategy.count(batches[0]), 1)

    # def test_single_row_get_first_row(self, single_row_dataframes):
    #     """Test get_first_row_as_dict() on single-row DataFrames."""
    #     for backend_name, df in single_row_dataframes.items():
    #         strategy = DataFrameSelectFactory.get_strategy(df)
    #         result = strategy.get_first_row_as_dict(df)

    #         check.is_instance(result, dict)
    #         check.greater(len(result), 0)


@pytest.mark.unit
class TestSingleColumnOperations:
    """Test operations on single-column DataFrames."""

    def test_single_column_drop_only_column(self, single_column_dataframes):
        """Test dropping the only column from DataFrame."""
        for backend_name, df in single_column_dataframes.items():
            strategy = DataFrameSelectFactory.get_strategy(df)

            result = strategy.drop(df, "id")

            check.is_not_none(result)
            result_columns = strategy.column_names(result)
            check.equal(len(result_columns), 0, msg=f"{backend_name} should have 0 columns after dropping only column")

    def test_single_column_select(self, single_column_dataframes):
        """Test select() on single-column DataFrames."""
        for backend_name, df in single_column_dataframes.items():
            strategy = DataFrameSelectFactory.get_strategy(df)

            result = strategy.select(df, "id")

            result_columns = strategy.column_names(result)
            check.equal(len(result_columns), 1)
            check.is_in("id", result_columns)

    def test_single_column_rename(self, single_column_dataframes):
        """Test rename() on single-column DataFrames."""
        for backend_name, df in single_column_dataframes.items():
            strategy = DataFrameSelectFactory.get_strategy(df)

            result = strategy.rename(df, {"id": "identifier"})

            result_columns = strategy.column_names(result)
            print(f"{backend_name} columns after rename: {result_columns}")

            check.is_in("identifier", result_columns)
            check.is_not_in("id", result_columns)


@pytest.mark.unit
class TestSpecialColumnNames:
    """Test operations with special column names."""

    def test_special_column_names_select(self, dataframe_with_special_columns):
        """Test select() works with special column names."""
        strategy = DataFrameSelectFactory.get_strategy(dataframe_with_special_columns)

        # Select column with spaces
        result = strategy.select(dataframe_with_special_columns, "column with spaces")
        result_columns = strategy.column_names(result)
        check.is_in("column with spaces", result_columns)

    def test_special_column_names_drop(self, dataframe_with_special_columns):
        """Test drop() works with special column names."""
        strategy = DataFrameSelectFactory.get_strategy(dataframe_with_special_columns)

        # Drop column with dashes
        result = strategy.drop(dataframe_with_special_columns, "column-with-dashes")
        result_columns = strategy.column_names(result)
        check.is_not_in("column-with-dashes", result_columns)

    def test_special_column_names_rename(self, dataframe_with_special_columns):
        """Test rename() works with special column names."""
        strategy = DataFrameSelectFactory.get_strategy(dataframe_with_special_columns)

        # Rename emoji column
        result = strategy.rename(dataframe_with_special_columns, {"🚀_emoji_col": "rocket_col"})
        result_columns = strategy.column_names(result)
        check.is_in("rocket_col", result_columns)
        check.is_not_in("🚀_emoji_col", result_columns)


@pytest.mark.unit
class TestNullHandling:
    """Test operations with null/missing values."""

    def test_null_values_count(self, dataframe_with_nulls):
        """Test count() includes rows with nulls."""
        for backend_name, df in dataframe_with_nulls.items():
            strategy = DataFrameSelectFactory.get_strategy(df)
            count = strategy.count(df)

            # Should count all rows, including those with nulls
            check.greater(count, 0, msg=f"{backend_name} should count rows with nulls")

    # def test_null_values_get_first_row(self, dataframe_with_nulls):
    #     """Test get_first_row_as_dict() handles nulls correctly."""
    #     for backend_name, df in dataframe_with_nulls.items():
    #         strategy = DataFrameSelectFactory.get_strategy(df)
    #         result = strategy.get_first_row_as_dict(df)

    #         check.is_instance(result, dict)
    #         # Result may contain None values
    #         check.greater_equal(len(result), 0)

    def test_null_values_select(self, dataframe_with_nulls):
        """Test select() preserves nulls."""
        for backend_name, df in dataframe_with_nulls.items():
            strategy = DataFrameSelectFactory.get_strategy(df)

            columns = strategy.column_names(df)
            if columns:
                result = strategy.select(df, columns[0])
                check.is_not_none(result, msg=f"{backend_name} select should work with nulls")


@pytest.mark.unit
@pytest.mark.parametrize("backend_fixture", BACKEND_FIXTURES)
class TestRenameErrorConditions:
    """Test error handling in rename operations."""

    def test_rename_duplicate_target_names(self, backend_fixture, request, rename_mapping_invalid_duplicate):
        """Test that renaming to duplicate names raises ValueError."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameSelectFactory.get_strategy(df)

        with pytest.raises(ValueError, match="[Dd]uplicate"):
            strategy.rename(df, rename_mapping_invalid_duplicate)

    def test_rename_nonexistent_column(self, backend_fixture, request, rename_mapping_nonexistent):
        """Test that renaming nonexistent column raises ValueError."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameSelectFactory.get_strategy(df)

        with pytest.raises(ValueError, match="not found|Columns"):
            strategy.rename(df, rename_mapping_nonexistent)


@pytest.mark.unit
@pytest.mark.parametrize("backend_fixture", BACKEND_FIXTURES)
class TestHeadErrorConditions:
    """Test error handling in head operations."""

    def test_head_negative_n(self, backend_fixture, request):
        """Test that head() with negative n raises ValueError."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameSelectFactory.get_strategy(df)

        with pytest.raises(ValueError, match="greater than or equal to 0"):
            strategy.head(df, -1)

        with pytest.raises(ValueError, match="greater than or equal to 0"):
            strategy.head(df, -100)


@pytest.mark.unit
class TestSplitBatchesErrorConditions:
    """Test error handling in split_in_batches operations."""

    def test_split_batches_zero_size(self, large_dataframe_for_batching):
        """Test that batch_size=0 raises ValueError."""
        strategy = DataFrameSelectFactory.get_strategy(large_dataframe_for_batching)

        with pytest.raises(ValueError, match="greater than 0"):
            strategy.split_in_batches(large_dataframe_for_batching, batch_size=0)

    def test_split_batches_negative_size(self, large_dataframe_for_batching):
        """Test that negative batch_size raises ValueError."""
        strategy = DataFrameSelectFactory.get_strategy(large_dataframe_for_batching)

        with pytest.raises(ValueError, match="greater than 0"):
            strategy.split_in_batches(large_dataframe_for_batching, batch_size=-10)

    def test_split_batches_generator_zero_size(self, large_dataframe_for_batching):
        """Test that batch_size=0 raises ValueError for generator."""
        strategy = DataFrameSelectFactory.get_strategy(large_dataframe_for_batching)

        with pytest.raises(ValueError, match="greater than 0"):
            list(strategy.split_in_batches_generator(large_dataframe_for_batching, batch_size=0))

    def test_split_batches_generator_negative_size(self, large_dataframe_for_batching):
        """Test that negative batch_size raises ValueError for generator."""
        strategy = DataFrameSelectFactory.get_strategy(large_dataframe_for_batching)

        with pytest.raises(ValueError, match="greater than 0"):
            list(strategy.split_in_batches_generator(large_dataframe_for_batching, batch_size=-10))


@pytest.mark.unit
class TestSplitBatchesGenerator:
    """Test split_in_batches_generator() functionality."""

    def test_generator_single_row(self, single_row_dataframes):
        """Test generator on single-row DataFrames."""
        for backend_name, df in single_row_dataframes.items():
            strategy = DataFrameSelectFactory.get_strategy(df)

            batches = list(strategy.split_in_batches_generator(df, batch_size=1))

            check.equal(len(batches), 1, msg=f"{backend_name} generator should yield 1 batch")
            check.equal(strategy.count(batches[0]), 1)

    def test_generator_large_df(self, large_dataframe_for_batching):
        """Test generator on large DataFrame."""
        strategy = DataFrameSelectFactory.get_strategy(large_dataframe_for_batching)

        batches = list(strategy.split_in_batches_generator(large_dataframe_for_batching, batch_size=10))

        check.equal(len(batches), 10, msg="Generator should yield 10 batches")
        total_rows = sum(strategy.count(batch) for batch in batches)
        check.equal(total_rows, 100, msg="All rows should be preserved")

    def test_generator_exact_division(self, large_dataframe_for_batching):
        """Test generator with exact division."""
        strategy = DataFrameSelectFactory.get_strategy(large_dataframe_for_batching)

        batches = list(strategy.split_in_batches_generator(large_dataframe_for_batching, batch_size=20))

        check.equal(len(batches), 5)
        for batch in batches:
            check.equal(strategy.count(batch), 20)

    def test_generator_early_termination(self, large_dataframe_for_batching):
        """Test generator can be terminated early."""
        strategy = DataFrameSelectFactory.get_strategy(large_dataframe_for_batching)

        # Take only first 3 batches
        batches = []
        for i, batch in enumerate(strategy.split_in_batches_generator(large_dataframe_for_batching, batch_size=10)):
            batches.append(batch)
            if i >= 2:  # Get first 3 batches (0, 1, 2)
                break

        check.equal(len(batches), 3, msg="Should only have 3 batches due to early termination")
        total_rows = sum(strategy.count(batch) for batch in batches)
        check.equal(total_rows, 30, msg="Should have 30 rows from 3 batches")

    def test_generator_vs_list_equivalence(self, large_dataframe_for_batching):
        """Test that generator and list methods produce equivalent results."""
        strategy = DataFrameSelectFactory.get_strategy(large_dataframe_for_batching)

        # Get batches from both methods
        batches_list, total = strategy.split_in_batches(large_dataframe_for_batching, batch_size=10)
        batches_gen = list(strategy.split_in_batches_generator(large_dataframe_for_batching, batch_size=10))

        # Should have same number of batches
        check.equal(len(batches_gen), len(batches_list))
        check.equal(len(batches_gen), 10)

        # Should have same total rows
        total_gen = sum(strategy.count(batch) for batch in batches_gen)
        total_list = sum(strategy.count(batch) for batch in batches_list)
        check.equal(total_gen, total_list)
        check.equal(total_gen, total)


@pytest.mark.unit
class TestDataFrameInfoEdgeCases:
    """Test get_dataframe_info() with edge cases."""

    def test_info_on_empty_dataframe(self, empty_dataframes):
        """Test get_dataframe_info() on empty DataFrames."""
        for backend_name, df in empty_dataframes.items():
            strategy = DataFrameIntrospectFactory.get_strategy(df)
            info = strategy.get_dataframe_info(df)

            check.is_instance(info, dict)
            check.is_in("type", info)
            # Should not raise error on empty DataFrame

    def test_info_on_single_row(self, single_row_dataframes):
        """Test get_dataframe_info() on single-row DataFrames."""
        for backend_name, df in single_row_dataframes.items():
            strategy = DataFrameIntrospectFactory.get_strategy(df)
            info = strategy.get_dataframe_info(df)

            check.is_instance(info, dict)
            check.is_in("type", info)

    def test_info_on_single_column(self, single_column_dataframes):
        """Test get_dataframe_info() on single-column DataFrames."""
        for backend_name, df in single_column_dataframes.items():
            strategy = DataFrameIntrospectFactory.get_strategy(df)
            info = strategy.get_dataframe_info(df)

            check.is_instance(info, dict)
            check.is_in("type", info)

    def test_info_with_nulls(self, dataframe_with_nulls):
        """Test get_dataframe_info() handles null values correctly."""
        for backend_name, df in dataframe_with_nulls.items():
            strategy = DataFrameIntrospectFactory.get_strategy(df)
            info = strategy.get_dataframe_info(df)

            check.is_instance(info, dict)
            # Should handle nulls gracefully
            if "null_counts" in info:
                check.is_instance(info["null_counts"], dict)


@pytest.mark.unit
class TestLargeDataFrameOperations:
    """Test operations on large DataFrames."""

    def test_large_df_count(self, large_dataframe_for_batching):
        """Test count() on large DataFrame."""
        strategy = DataFrameSelectFactory.get_strategy(large_dataframe_for_batching)
        count = strategy.count(large_dataframe_for_batching)

        check.equal(count, 100, msg="Large DataFrame should have 100 rows")

    def test_large_df_split_performance(self, large_dataframe_for_batching):
        """Test split_in_batches() efficiency on large DataFrame."""
        strategy = DataFrameSelectFactory.get_strategy(large_dataframe_for_batching)

        # Split into reasonable batch sizes
        batches, total = strategy.split_in_batches(large_dataframe_for_batching, batch_size=10)

        check.equal(len(batches), 10)
        check.equal(total, 100, msg="Total should be 100 rows")
        total_rows = sum(strategy.count(batch) for batch in batches)
        check.equal(total_rows, 100, msg="All rows should be preserved in batches")

    def test_large_df_head_subset(self, large_dataframe_for_batching):
        """Test head() returns exact subset from large DataFrame."""
        strategy = DataFrameSelectFactory.get_strategy(large_dataframe_for_batching)

        result = strategy.head(large_dataframe_for_batching, 25)

        check.equal(strategy.count(result), 25)


@pytest.mark.unit
class TestOperationChainingSafety:
    """Test that operation chaining preserves data integrity."""

    def test_select_drop_chain(self, sample_pandas_df):
        """Test chaining select and drop operations."""
        strategy = DataFrameSelectFactory.get_strategy(sample_pandas_df)

        # Chain: select -> drop
        selected = strategy.select(sample_pandas_df, ["id", "name", "category"])
        result = strategy.drop(selected, "category")

        result_columns = strategy.column_names(result)
        check.equal(set(result_columns), {"id", "name"})

    def test_rename_select_chain(self, sample_polars_df):
        """Test chaining rename and select operations."""
        strategy = DataFrameSelectFactory.get_strategy(sample_polars_df)

        # Chain: rename -> select
        renamed = strategy.rename(sample_polars_df, {"name": "full_name"})
        result = strategy.select(renamed, "full_name")

        result_columns = strategy.column_names(result)
        check.is_in("full_name", result_columns)
        check.is_not_in("name", result_columns)

    def test_head_select_drop_chain(self, sample_pyarrow_table):
        """Test chaining head, select, and drop operations."""
        strategy = DataFrameSelectFactory.get_strategy(sample_pyarrow_table)

        # Chain: head -> select -> drop
        subset = strategy.head(sample_pyarrow_table, 3)
        selected = strategy.select(subset, ["id", "name", "value"])
        result = strategy.drop(selected, "value")

        result_columns = strategy.column_names(result)
        result_count = strategy.count(result)

        check.equal(set(result_columns), {"id", "name"})
        check.less_equal(result_count, 3)


@pytest.mark.unit
class TestBoundaryConditions:
    """Test boundary conditions for various operations."""

    def test_head_boundary_at_df_size(self, sample_pandas_df):
        """Test head() with n exactly equal to DataFrame size."""
        strategy = DataFrameSelectFactory.get_strategy(sample_pandas_df)

        original_count = strategy.count(sample_pandas_df)
        result = strategy.head(sample_pandas_df, original_count)

        result_count = strategy.count(result)
        check.equal(result_count, original_count)

    def test_split_batches_boundary_exact_division(self, large_dataframe_for_batching):
        """Test split_in_batches() with exact division."""
        strategy = DataFrameSelectFactory.get_strategy(large_dataframe_for_batching)

        # 100 rows / 20 per batch = exactly 5 batches
        batches, total = strategy.split_in_batches(large_dataframe_for_batching, batch_size=20)

        check.equal(len(batches), 5)
        check.equal(total, 100, msg="Total should be 100 rows")
        for batch in batches:
            check.equal(strategy.count(batch), 20)

    def test_rename_all_columns(self, sample_polars_df):
        """Test renaming all columns at once."""
        strategy = DataFrameSelectFactory.get_strategy(sample_polars_df)

        columns = strategy.column_names(sample_polars_df)
        mapping = {col: f"new_{col}" for col in columns}

        result = strategy.rename(sample_polars_df, mapping)

        result_columns = strategy.column_names(result)
        for col in columns:
            check.is_not_in(col, result_columns, msg=f"Old column {col} should be renamed")
            check.is_in(f"new_{col}", result_columns, msg=f"New column new_{col} should exist")
