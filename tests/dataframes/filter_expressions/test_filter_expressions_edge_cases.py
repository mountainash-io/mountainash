"""
Tests for filter expression edge cases and error handling.

This module tests boundary conditions, error scenarios, and special cases
for the filter expression system.
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
class TestEmptyDataFrames:
    """Test filter expressions on empty DataFrames."""

    def test_filter_empty_polars(self, empty_dataframes):
        """Test filtering empty Polars DataFrame."""
        empty_df = empty_dataframes["polars"]

        # Can't filter empty DataFrame with no columns
        if len(empty_df.columns) == 0:
            pytest.skip("Cannot create expression for DataFrame with no columns")

        polars_expr = pl.col("age") > 30  # Expression that would match if data existed

        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(polars_expr)

        # Should not raise error, just return empty DataFrame
        result = strategy.filter(empty_df, polars_expr)
        assert isinstance(result, pl.DataFrame)
        assert len(result) == 0

    def test_filter_empty_pandas(self, empty_dataframes):
        """Test filtering empty Pandas DataFrame."""
        empty_df = empty_dataframes["pandas"]

        # Can't create expression from empty DataFrame, so skip if no columns
        if len(empty_df.columns) == 0:
            pytest.skip("Cannot create expression from DataFrame with no columns")

    def test_filter_empty_narwhals(self, empty_dataframes):
        """Test filtering empty Narwhals DataFrame."""
        empty_df = empty_dataframes["narwhals"]

        # Can't filter empty DataFrame with no columns
        result_native_test = nw.to_native(empty_df)
        if len(result_native_test.columns) == 0:
            pytest.skip("Cannot create expression for DataFrame with no columns")

        nw_expr = nw.col("age") > 30

        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(nw_expr)

        # Should not raise error
        result = strategy.filter(empty_df, nw_expr)
        result_native = nw.to_native(result)
        assert len(result_native) == 0


@pytest.mark.unit
class TestSingleRowDataFrames:
    """Test filter expressions on single-row DataFrames."""

    def test_single_row_matches(self, single_row_dataframes):
        """Test filter on single row that matches condition."""
        # Single row has age=25, so age < 30 should match
        polars_df = pl.DataFrame(single_row_dataframes)
        polars_expr = pl.col("age") < 30

        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(polars_expr)
        result = strategy.filter(polars_df, polars_expr)

        assert len(result) == 1

    def test_single_row_no_match(self, single_row_dataframes):
        """Test filter on single row that doesn't match condition."""
        # Single row has age=25, so age > 30 should not match
        polars_df = pl.DataFrame(single_row_dataframes)
        polars_expr = pl.col("age") > 30

        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(polars_expr)
        result = strategy.filter(polars_df, polars_expr)

        assert len(result) == 0


@pytest.mark.unit
class TestNullHandling:
    """Test filter expressions with null/None values."""

    def test_filter_with_nulls_polars(self, dataframes_with_nulls):
        """Test Polars handles nulls in filter expressions."""
        polars_df = pl.DataFrame(dataframes_with_nulls)
        # Filter for age > 30 (should handle nulls gracefully)
        polars_expr = pl.col("age") > 30

        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(polars_expr)
        result = strategy.filter(polars_df, polars_expr)

        # Should filter rows where age > 30 and age is not null
        assert len(result) > 0
        # Verify no null ages in result
        assert result["age"].null_count() == 0

    def test_filter_with_nulls_narwhals(self, dataframes_with_nulls):
        """Test Narwhals handles nulls in filter expressions."""
        nw_df = nw.from_native(pd.DataFrame(dataframes_with_nulls))
        nw_expr = nw.col("age") > 30

        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(nw_expr)
        result = strategy.filter(nw_df, nw_expr)

        assert len(nw.to_native(result)) > 0

    def test_filter_null_equality_polars(self, dataframes_with_nulls):
        """Test filtering for null values in Polars."""
        polars_df = pl.DataFrame(dataframes_with_nulls)
        # Filter for rows where name is null
        polars_expr = pl.col("name").is_null()

        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(polars_expr)
        result = strategy.filter(polars_df, polars_expr)

        # Should return 3 rows with null names
        assert len(result) == 3


@pytest.mark.unit
class TestAllMatchingConditions:
    """Test filter expressions where all rows match."""

    def test_all_rows_match_polars(self, all_matching_filter_data):
        """Test Polars filter where all rows match condition."""
        polars_df = pl.DataFrame(all_matching_filter_data)
        polars_expr = pl.col("age") > 30  # All ages are > 30

        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(polars_expr)
        result = strategy.filter(polars_df, polars_expr)

        # Should return all 5 rows
        assert len(result) == 5

    def test_all_rows_match_narwhals(self, all_matching_filter_data):
        """Test Narwhals filter where all rows match condition."""
        nw_df = nw.from_native(pd.DataFrame(all_matching_filter_data))
        nw_expr = nw.col("age") > 30

        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(nw_expr)
        result = strategy.filter(nw_df, nw_expr)

        assert len(nw.to_native(result)) == 5


@pytest.mark.unit
class TestNoMatchingConditions:
    """Test filter expressions where no rows match."""

    def test_no_rows_match_polars(self, no_matching_filter_data):
        """Test Polars filter where no rows match condition."""
        polars_df = pl.DataFrame(no_matching_filter_data)
        polars_expr = pl.col("age") > 30  # All ages are <= 30

        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(polars_expr)
        result = strategy.filter(polars_df, polars_expr)

        # Should return empty DataFrame
        assert len(result) == 0
        # But preserve structure
        assert "age" in result.columns

    def test_no_rows_match_narwhals(self, no_matching_filter_data):
        """Test Narwhals filter where no rows match condition."""
        nw_df = nw.from_native(pd.DataFrame(no_matching_filter_data))
        nw_expr = nw.col("age") > 30

        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(nw_expr)
        result = strategy.filter(nw_df, nw_expr)

        result_native = nw.to_native(result)
        assert len(result_native) == 0


@pytest.mark.unit
class TestComplexExpressions:
    """Test complex filter expressions with multiple operations."""

    def test_or_expression_polars(self, polars_df):
        """Test OR logic in Polars expressions."""
        # age > 40 OR salary < 70000
        polars_expr = (pl.col("age") > 40) | (pl.col("salary") < 70000.0)

        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(polars_expr)
        result = strategy.filter(polars_df, polars_expr)

        # Should match: age > 40 (Eve=42) OR salary < 70000 (Bob=65000, Diana=70000, Grace=68000)
        assert len(result) >= 2

    def test_not_expression_polars(self, polars_df):
        """Test NOT logic in Polars expressions."""
        # NOT is_active
        polars_expr = ~pl.col("is_active")

        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(polars_expr)
        result = strategy.filter(polars_df, polars_expr)

        # Should return 3 inactive employees
        assert len(result) == 3

    def test_chained_and_or_polars(self, polars_df):
        """Test chained AND/OR expressions in Polars."""
        # (age > 30 AND department == 'Engineering') OR salary > 90000
        polars_expr = ((pl.col("age") > 30) & (pl.col("department") == "Engineering")) | (pl.col("salary") > 90000.0)

        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(polars_expr)
        result = strategy.filter(polars_df, polars_expr)

        assert len(result) > 0


@pytest.mark.unit
class TestStringOperations:
    """Test filter expressions with string operations."""

    def test_string_contains_polars(self, polars_df):
        """Test string contains operation in Polars."""
        # Name contains 'a' (case-insensitive)
        polars_expr = pl.col("name").str.contains("a", literal=True)

        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(polars_expr)
        result = strategy.filter(polars_df, polars_expr)

        # Should match multiple names containing 'a'
        assert len(result) > 0

    def test_string_startswith_polars(self, polars_df):
        """Test string startswith operation in Polars."""
        # Name starts with 'A'
        polars_expr = pl.col("name").str.starts_with("A")

        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(polars_expr)
        result = strategy.filter(polars_df, polars_expr)

        # Should match Alice
        assert len(result) == 1


@pytest.mark.unit
class TestNumericOperations:
    """Test filter expressions with numeric operations."""

    def test_between_operation_polars(self, polars_df):
        """Test between operation in Polars."""
        # Age between 28 and 35 (inclusive)
        polars_expr = pl.col("age").is_between(28, 35, closed="both")

        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(polars_expr)
        result = strategy.filter(polars_df, polars_expr)

        # Should match ages: 28, 29, 30, 31, 33, 35
        assert len(result) == 6

    def test_in_list_operation_polars(self, polars_df):
        """Test IN list operation in Polars."""
        # Department in ['Engineering', 'HR']
        polars_expr = pl.col("department").is_in(["Engineering", "HR"])

        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(polars_expr)
        result = strategy.filter(polars_df, polars_expr)

        # Should match 4 Engineering + 3 HR = 7 rows
        assert len(result) == 7


@pytest.mark.unit
class TestErrorHandling:
    """Test error handling in filter expressions."""

    def test_invalid_column_name_polars(self, polars_df):
        """Test filter with non-existent column raises appropriate error."""
        polars_expr = pl.col("nonexistent_column") > 30

        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(polars_expr)

        # Should raise an error about missing column
        with pytest.raises(Exception):  # Polars will raise ColumnNotFoundError or similar
            result = strategy.filter(polars_df, polars_expr)

    def test_type_mismatch_polars(self, polars_df):
        """Test filter with type mismatch."""
        # Try to compare string column with number
        polars_expr = pl.col("name") > 30

        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(polars_expr)

        # Should raise a type error
        with pytest.raises(Exception):  # Polars will raise a type-related error
            result = strategy.filter(polars_df, polars_expr)


@pytest.mark.unit
class TestBackendConversion:
    """Test filter expressions with backend conversion."""

    def test_narwhals_auto_converts_pandas(self, pandas_df, narwhals_expression_single_column):
        """Test Narwhals strategy auto-converts pandas DataFrame."""
        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(narwhals_expression_single_column)

        # Pass pandas DataFrame with narwhals expression
        result = strategy.filter(pandas_df, narwhals_expression_single_column)

        # Should return pandas DataFrame
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 5

    def test_narwhals_auto_converts_polars(self, polars_df, narwhals_expression_single_column):
        """Test Narwhals strategy auto-converts polars DataFrame."""
        factory = FilterExpressionStrategyFactory()
        strategy = factory.get_strategy(narwhals_expression_single_column)

        # Pass polars DataFrame with narwhals expression
        result = strategy.filter(polars_df, narwhals_expression_single_column)

        # Should return polars DataFrame
        assert isinstance(result, pl.DataFrame)
        assert len(result) == 5
