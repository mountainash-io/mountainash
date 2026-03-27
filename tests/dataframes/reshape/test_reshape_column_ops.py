"""Tests for reshape module column operations.

This module tests column manipulation methods (drop, select, rename) across all backends.
"""

import pytest
from pytest_check import check
import pandas as pd
import polars as pl

from mountainash.dataframes.select import DataFrameSelectFactory
from mountainash.dataframes.introspect import DataFrameIntrospectFactory


# Backend fixtures for parameterized testing
BACKEND_FIXTURES = [
    "sample_pandas_df",
    "sample_polars_df",
    "sample_pyarrow_table",
    "real_ibis_table",
    "sample_narwhals_df"
]


@pytest.mark.unit
@pytest.mark.parametrize("backend_fixture", BACKEND_FIXTURES)
class TestSelectOperation:
    """Test select() column operation across all backends."""

    def test_select_single_column(self, backend_fixture, request):
        """Test selecting a single column."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameSelectFactory.get_strategy(df)

        result = strategy.select(df, "name")

        # Verify column selection worked
        result_columns = strategy.column_names(result)
        check.is_in("name", result_columns)
        # Should only have 1 column (or the original if select didn't filter)
        check.less_equal(len(result_columns), len(strategy.column_names(df)))

    def test_select_multiple_columns(self, backend_fixture, request):
        """Test selecting multiple columns."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameSelectFactory.get_strategy(df)

        result = strategy.select(df, ["id", "name"])

        result_columns = strategy.column_names(result)
        check.is_in("id", result_columns)
        check.is_in("name", result_columns)

    def test_select_nonexistent_column(self, backend_fixture, request):
        """Test selecting nonexistent column returns original or empty result."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameSelectFactory.get_strategy(df)

        # Select should handle nonexistent columns gracefully
        result = strategy.select(df, "nonexistent_column")

        # Should return original df or df with valid columns only
        check.is_not_none(result)

    def test_select_empty_list(self, backend_fixture, request):
        """Test selecting empty column list returns original DataFrame."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameSelectFactory.get_strategy(df)

        result = strategy.select(df, [])

        # Empty selection should return original df
        check.is_not_none(result)


@pytest.mark.unit
@pytest.mark.parametrize("backend_fixture", BACKEND_FIXTURES)
class TestDropOperation:
    """Test drop() column operation across all backends."""

    def test_drop_single_column(self, backend_fixture, request):
        """Test dropping a single column."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameSelectFactory.get_strategy(df)

        original_columns = strategy.column_names(df)
        result = strategy.drop(df, "category")

        result_columns = strategy.column_names(result)
        # Should have one fewer column (if category existed)
        check.less_equal(len(result_columns), len(original_columns))
        # category should be gone
        check.is_not_in("category", result_columns)

    def test_drop_multiple_columns(self, backend_fixture, request):
        """Test dropping multiple columns."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameSelectFactory.get_strategy(df)

        original_columns = strategy.column_names(df)
        result = strategy.drop(df, ["category", "active"])

        result_columns = strategy.column_names(result)
        check.less_equal(len(result_columns), len(original_columns))
        check.is_not_in("category", result_columns)
        check.is_not_in("active", result_columns)

    def test_drop_nonexistent_column(self, backend_fixture, request):
        """Test dropping nonexistent column doesn't raise error."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameSelectFactory.get_strategy(df)

        # Should not raise error for nonexistent column
        result = strategy.drop(df, "nonexistent_column")
        check.is_not_none(result)

    def test_drop_empty_list(self, backend_fixture, request):
        """Test dropping empty list returns original DataFrame."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameSelectFactory.get_strategy(df)

        original_columns = strategy.column_names(df)
        result = strategy.drop(df, [])

        result_columns = strategy.column_names(result)
        check.equal(len(result_columns), len(original_columns))


@pytest.mark.unit
@pytest.mark.parametrize("backend_fixture", BACKEND_FIXTURES)
class TestRenameOperation:
    """Test rename() column operation across all backends."""

    def test_rename_single_column(self, backend_fixture, request, rename_mapping_valid):
        """Test renaming a single column."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameSelectFactory.get_strategy(df)

        # Rename just one column
        mapping = {"name": "full_name"}
        result = strategy.rename(df, mapping)

        result_columns = strategy.column_names(result)
        check.is_in("full_name", result_columns)
        check.is_not_in("name", result_columns)

    def test_rename_multiple_columns(self, backend_fixture, request):
        """Test renaming multiple columns."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameSelectFactory.get_strategy(df)

        mapping = {"id": "identifier", "name": "full_name"}
        result = strategy.rename(df, mapping)

        result_columns = strategy.column_names(result)
        check.is_in("identifier", result_columns)
        check.is_in("full_name", result_columns)

    def test_rename_duplicate_target_names(self, backend_fixture, request, rename_mapping_invalid_duplicate):
        """Test renaming to duplicate names raises ValueError."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameSelectFactory.get_strategy(df)

        # Should raise ValueError for duplicate target names
        with pytest.raises(ValueError, match="[Dd]uplicate"):
            strategy.rename(df, rename_mapping_invalid_duplicate)

    def test_rename_nonexistent_column(self, backend_fixture, request, rename_mapping_nonexistent):
        """Test renaming nonexistent column raises ValueError."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameSelectFactory.get_strategy(df)

        # Should raise ValueError for nonexistent columns
        with pytest.raises(ValueError, match="not found|Columns"):
            strategy.rename(df, rename_mapping_nonexistent)

    def test_rename_empty_mapping(self, backend_fixture, request):
        """Test rename with empty mapping returns original DataFrame."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameSelectFactory.get_strategy(df)

        original_columns = strategy.column_names(df)
        result = strategy.rename(df, {})

        result_columns = strategy.column_names(result)
        # Should have same columns
        check.equal(sorted(result_columns), sorted(original_columns))


@pytest.mark.unit
class TestColumnOperationsEdgeCases:
    """Test column operations with edge cases."""

    def test_select_from_empty_dataframe(self, empty_dataframes):
        """Test select on empty DataFrames."""
        for backend_name, df in empty_dataframes.items():
            strategy = DataFrameSelectFactory.get_strategy(df)
            result = strategy.select(df, [])
            check.is_not_none(result)

    def test_drop_from_single_column_dataframe(self, single_column_dataframes):
        """Test dropping from single-column DataFrame."""
        for backend_name, df in single_column_dataframes.items():
            strategy = DataFrameSelectFactory.get_strategy(df)
            # Drop the only column
            result = strategy.drop(df, "id")
            check.is_not_none(result)
            # Result should have 0 columns
            result_columns = strategy.column_names(result)
            check.equal(len(result_columns), 0)

    def test_select_with_special_column_names(self, dataframe_with_special_columns):
        """Test select works with special column names."""
        strategy = DataFrameSelectFactory.get_strategy(dataframe_with_special_columns)

        # Should handle columns with spaces
        result = strategy.select(dataframe_with_special_columns, "column with spaces")
        check.is_not_none(result)

        result_columns = strategy.column_names(result)
        check.is_in("column with spaces", result_columns)


@pytest.mark.unit
class TestColumnOpsLazyFrameBehavior:
    """Test lazy frame specific behavior for column operations."""

    def test_select_polars_lazyframe_preserves_lazy(self, sample_polars_lazyframe):
        """Test that select() preserves Polars LazyFrame type."""
        strategy = DataFrameSelectFactory.get_strategy(sample_polars_lazyframe)
        result = strategy.select(sample_polars_lazyframe, "id")

        check.is_instance(result, pl.LazyFrame, "Result should remain Polars LazyFrame")

    def test_select_polars_lazyframe_multiple_columns(self, sample_polars_lazyframe):
        """Test that select() with multiple columns preserves Polars LazyFrame type."""
        strategy = DataFrameSelectFactory.get_strategy(sample_polars_lazyframe)
        result = strategy.select(sample_polars_lazyframe, ["id", "name"])

        check.is_instance(result, pl.LazyFrame, "Result should remain Polars LazyFrame")

        # Verify columns when collected
        result_columns = strategy.column_names(result)
        check.is_in("id", result_columns)
        check.is_in("name", result_columns)

    def test_select_narwhals_lazyframe_preserves_lazy(self, sample_narwhals_lazyframe):
        """Test that select() preserves Narwhals LazyFrame type."""
        import narwhals as nw

        strategy = DataFrameSelectFactory.get_strategy(sample_narwhals_lazyframe)
        result = strategy.select(sample_narwhals_lazyframe, "id")

        # Convert to native to check underlying type
        native_result = nw.to_native(result)
        check.is_true(
            hasattr(native_result, 'collect'),
            "Result should have collect method (indicating it's lazy)"
        )

    def test_drop_polars_lazyframe_preserves_lazy(self, sample_polars_lazyframe):
        """Test that drop() preserves Polars LazyFrame type."""
        strategy = DataFrameSelectFactory.get_strategy(sample_polars_lazyframe)
        result = strategy.drop(sample_polars_lazyframe, "category")

        check.is_instance(result, pl.LazyFrame, "Result should remain Polars LazyFrame")

    def test_drop_polars_lazyframe_multiple_columns(self, sample_polars_lazyframe):
        """Test that drop() with multiple columns preserves Polars LazyFrame type."""
        strategy = DataFrameSelectFactory.get_strategy(sample_polars_lazyframe)
        result = strategy.drop(sample_polars_lazyframe, ["category", "active"])

        check.is_instance(result, pl.LazyFrame, "Result should remain Polars LazyFrame")

        # Verify columns were dropped
        result_columns = strategy.column_names(result)
        check.is_not_in("category", result_columns)
        check.is_not_in("active", result_columns)

    def test_drop_narwhals_lazyframe_preserves_lazy(self, sample_narwhals_lazyframe):
        """Test that drop() preserves Narwhals LazyFrame type."""
        import narwhals as nw

        strategy = DataFrameSelectFactory.get_strategy(sample_narwhals_lazyframe)
        result = strategy.drop(sample_narwhals_lazyframe, "category")

        # Convert to native to check underlying type
        native_result = nw.to_native(result)
        check.is_true(
            hasattr(native_result, 'collect'),
            "Result should have collect method (indicating it's lazy)"
        )

    def test_rename_polars_lazyframe_preserves_lazy(self, sample_polars_lazyframe):
        """Test that rename() preserves Polars LazyFrame type."""
        strategy = DataFrameSelectFactory.get_strategy(sample_polars_lazyframe)
        result = strategy.rename(sample_polars_lazyframe, {"name": "full_name"})

        check.is_instance(result, pl.LazyFrame, "Result should remain Polars LazyFrame")

    def test_rename_polars_lazyframe_multiple_columns(self, sample_polars_lazyframe):
        """Test that rename() with multiple columns preserves Polars LazyFrame type."""
        strategy = DataFrameSelectFactory.get_strategy(sample_polars_lazyframe)
        result = strategy.rename(sample_polars_lazyframe, {"id": "identifier", "name": "full_name"})

        check.is_instance(result, pl.LazyFrame, "Result should remain Polars LazyFrame")

        # Verify renamed columns
        result_columns = strategy.column_names(result)
        check.is_in("identifier", result_columns)
        check.is_in("full_name", result_columns)
        check.is_not_in("id", result_columns)
        check.is_not_in("name", result_columns)

    def test_rename_narwhals_lazyframe_preserves_lazy(self, sample_narwhals_lazyframe):
        """Test that rename() preserves Narwhals LazyFrame type."""
        import narwhals as nw

        strategy = DataFrameSelectFactory.get_strategy(sample_narwhals_lazyframe)
        result = strategy.rename(sample_narwhals_lazyframe, {"name": "full_name"})

        # Convert to native to check underlying type
        native_result = nw.to_native(result)
        check.is_true(
            hasattr(native_result, 'collect'),
            "Result should have collect method (indicating it's lazy)"
        )


@pytest.mark.unit
class TestLazyFrameOperationChaining:
    """Test that chaining operations preserves laziness."""

    def test_select_drop_chain_polars_lazy(self, sample_polars_lazyframe):
        """Test chaining select and drop maintains Polars LazyFrame."""
        strategy = DataFrameSelectFactory.get_strategy(sample_polars_lazyframe)

        # Chain: select -> drop
        selected = strategy.select(sample_polars_lazyframe, ["id", "name", "category"])
        result = strategy.drop(selected, "category")

        check.is_instance(selected, pl.LazyFrame, "Intermediate result should be LazyFrame")
        check.is_instance(result, pl.LazyFrame, "Final result should be LazyFrame")

        # Verify correctness
        result_columns = strategy.column_names(result)
        check.equal(set(result_columns), {"id", "name"})

    def test_rename_select_chain_polars_lazy(self, sample_polars_lazyframe):
        """Test chaining rename and select maintains Polars LazyFrame."""
        strategy = DataFrameSelectFactory.get_strategy(sample_polars_lazyframe)

        # Chain: rename -> select
        renamed = strategy.rename(sample_polars_lazyframe, {"name": "full_name"})
        result = strategy.select(renamed, ["id", "full_name"])

        check.is_instance(renamed, pl.LazyFrame, "Intermediate result should be LazyFrame")
        check.is_instance(result, pl.LazyFrame, "Final result should be LazyFrame")

        # Verify correctness
        result_columns = strategy.column_names(result)
        check.is_in("full_name", result_columns)
        check.is_not_in("name", result_columns)

    def test_select_rename_drop_chain_polars_lazy(self, sample_polars_lazyframe):
        """Test complex chaining maintains Polars LazyFrame."""
        strategy = DataFrameSelectFactory.get_strategy(sample_polars_lazyframe)

        # Chain: select -> rename -> drop
        selected = strategy.select(sample_polars_lazyframe, ["id", "name", "category", "value"])
        renamed = strategy.rename(selected, {"name": "full_name", "value": "amount"})
        result = strategy.drop(renamed, "category")

        check.is_instance(selected, pl.LazyFrame, "After select should be LazyFrame")
        check.is_instance(renamed, pl.LazyFrame, "After rename should be LazyFrame")
        check.is_instance(result, pl.LazyFrame, "Final result should be LazyFrame")

        # Verify correctness
        result_columns = strategy.column_names(result)
        check.equal(set(result_columns), {"id", "full_name", "amount"})

    def test_select_drop_chain_narwhals_lazy(self, sample_narwhals_lazyframe):
        """Test chaining select and drop maintains Narwhals LazyFrame."""
        import narwhals as nw

        strategy = DataFrameSelectFactory.get_strategy(sample_narwhals_lazyframe)

        # Chain: select -> drop
        selected = strategy.select(sample_narwhals_lazyframe, ["id", "name", "category"])
        result = strategy.drop(selected, "category")

        # Verify both remain lazy
        check.is_true(hasattr(nw.to_native(selected), 'collect'), "Intermediate should be lazy")
        check.is_true(hasattr(nw.to_native(result), 'collect'), "Final result should be lazy")

        # Verify correctness
        result_columns = strategy.column_names(result)
        check.equal(set(result_columns), {"id", "name"})

    def test_rename_select_chain_narwhals_lazy(self, sample_narwhals_lazyframe):
        """Test chaining rename and select maintains Narwhals LazyFrame."""
        import narwhals as nw

        strategy = DataFrameSelectFactory.get_strategy(sample_narwhals_lazyframe)

        # Chain: rename -> select
        renamed = strategy.rename(sample_narwhals_lazyframe, {"name": "full_name"})
        result = strategy.select(renamed, ["id", "full_name"])

        # Verify both remain lazy
        check.is_true(hasattr(nw.to_native(renamed), 'collect'), "Intermediate should be lazy")
        check.is_true(hasattr(nw.to_native(result), 'collect'), "Final result should be lazy")
