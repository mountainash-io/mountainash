"""Comprehensive error handling and edge case tests for DataFrameUtils.

This module tests all error paths, None handling, and edge cases to achieve
maximum coverage of defensive programming patterns in DataFrameUtils.
"""

import pytest
import pandas as pd
import polars as pl
import pyarrow as pa
import ibis

from mountainash.dataframes import DataFrameUtils
from mountainash.dataframes.constants import CONST_DATAFRAME_FRAMEWORK


@pytest.mark.unit
class TestCreationErrorHandling:
    """Test error handling in DataFrame creation methods."""

    def test_create_dataframe_missing_framework(self):
        """Test create_dataframe raises error when framework not specified."""
        data = {"id": [1, 2, 3]}

        with pytest.raises(ValueError, match="dataframe_framework must be specified"):
            DataFrameUtils.create_dataframe(data, dataframe_framework=None)

        with pytest.raises(ValueError, match="dataframe_framework must be specified"):
            DataFrameUtils.create_dataframe(data, dataframe_framework="")

    def test_create_dataframe_invalid_framework(self):
        """Test create_dataframe raises error for unsupported framework."""
        data = {"id": [1, 2, 3]}

        with pytest.raises(ValueError, match="Unsupported dataframe framework"):
            DataFrameUtils.create_dataframe(data, dataframe_framework="invalid_backend")

    def test_create_pandas_with_none_data(self):
        """Test create_pandas handles None data gracefully."""
        # Should convert None to empty dict
        result = DataFrameUtils.create_pandas(None)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    def test_create_polars_with_none_data(self):
        """Test create_polars handles None data gracefully."""
        result = DataFrameUtils.create_polars(None)
        assert isinstance(result, pl.DataFrame)
        assert len(result) == 0

    def test_create_pyarrow_with_none_data(self):
        """Test create_pyarrow handles None data gracefully."""
        result = DataFrameUtils.create_pyarrow(None)
        assert isinstance(result, pa.Table)
        assert len(result) == 0

    def test_create_ibis_with_none_data(self):
        """Test create_ibis handles None data gracefully."""
        result = DataFrameUtils.create_ibis(None)
        assert hasattr(result, 'schema')
        # Ibis tables from empty data have 0 rows
        assert result.count().execute() == 0


@pytest.mark.unit
class TestConversionErrorHandling:
    """Test error handling in DataFrame conversion methods."""

    def test_cast_dataframe_with_none(self):
        """Test cast_dataframe returns None when input is None."""
        result = DataFrameUtils.cast_dataframe(None, CONST_DATAFRAME_FRAMEWORK.PANDAS)
        assert result is None

    def test_to_pandas_with_none(self):
        """Test to_pandas returns None when input is None."""
        result = DataFrameUtils.to_pandas(None)
        assert result is None

    def test_to_polars_with_none(self):
        """Test to_polars returns None when input is None."""
        result = DataFrameUtils.to_polars(None)
        assert result is None

    def test_to_pyarrow_with_none(self):
        """Test to_pyarrow returns None when input is None."""
        result = DataFrameUtils.to_pyarrow(None)
        assert result is None

    def test_to_ibis_with_none(self):
        """Test to_ibis returns None when input is None."""
        result = DataFrameUtils.to_ibis(None)
        assert result is None

    def test_to_narwhals_with_none(self):
        """Test to_narwhals returns None when input is None."""
        result = DataFrameUtils.to_narwhals(None)
        assert result is None

    def test_to_dictionary_of_lists_with_none(self):
        """Test to_dictionary_of_lists returns empty dict when input is None."""
        result = DataFrameUtils.to_dictionary_of_lists(None)
        assert result == {}

    def test_to_dictionary_of_series_pandas_with_none(self):
        """Test to_dictionary_of_series_pandas returns empty dict when input is None."""
        result = DataFrameUtils.to_dictionary_of_series_pandas(None)
        assert result == {}

    def test_to_dictionary_of_series_polars_with_none(self):
        """Test to_dictionary_of_series_polars returns empty dict when input is None."""
        result = DataFrameUtils.to_dictionary_of_series_polars(None)
        assert result == {}

    def test_to_list_of_dictionaries_with_none(self):
        """Test to_list_of_dictionaries returns empty list when input is None."""
        result = DataFrameUtils.to_list_of_dictionaries(None)
        assert result == []


@pytest.mark.unit
class TestUtilityErrorHandling:
    """Test error handling in utility methods."""

    def test_column_names_with_none(self):
        """Test column_names returns empty list when input is None."""
        result = DataFrameUtils.column_names(None)
        assert result == []

    def test_table_schema_ibis_with_none(self):
        """Test table_schema_ibis returns None when input is None."""
        result = DataFrameUtils.table_schema_ibis(None)
        assert result is None

    def test_drop_with_none(self):
        """Test drop returns None when input is None."""
        result = DataFrameUtils.drop(None, columns="id")
        assert result is None

    def test_select_with_none(self):
        """Test select returns None when input is None."""
        result = DataFrameUtils.select(None, columns="id")
        assert result is None

    def test_distinct_with_none(self):
        """Test distinct returns None when input is None."""
        result = DataFrameUtils.distinct(None, columns="id")
        assert result is None

    def test_head_with_none(self):
        """Test head returns None when input is None."""
        result = DataFrameUtils.head(None, n=5)
        assert result is None

    def test_count_with_none(self):
        """Test count returns 0 when input is None."""
        result = DataFrameUtils.count(None)
        assert result == 0

    def test_count_with_empty_list(self):
        """Test count returns 0 for empty list."""
        result = DataFrameUtils.count([])
        assert result == 0

    def test_filter_with_none(self):
        """Test filter returns None when input is None."""
        import polars as pl
        expr = pl.col("id") > 5

        result = DataFrameUtils.filter(None, expression=expr)
        assert result is None

    def test_get_dataframe_info_with_none(self):
        """Test get_dataframe_info handles None input gracefully."""
        result = DataFrameUtils.get_dataframe_info(None)

        assert "type" in result
        assert result["type"] is None
        assert "error" in result
        assert "None" in result["error"]

    def test_split_dataframe_in_batches_with_none(self):
        """Test split_dataframe_in_batches returns empty tuple when input is None."""
        batches, total = DataFrameUtils.split_dataframe_in_batches(None, batch_size=10)
        assert batches == []
        assert total == 0


@pytest.mark.unit
class TestColumnExtractionErrorHandling:
    """Test error handling in column extraction methods."""

    def test_get_column_as_list_with_none_df(self):
        """Test get_column_as_list returns empty list when DataFrame is None."""
        result = DataFrameUtils.get_column_as_list(None, column="id")
        assert result == []

    def test_get_column_as_list_with_none_column(self):
        """Test get_column_as_list returns empty list when column is None."""
        df = DataFrameUtils.create_polars({"id": [1, 2, 3]})
        result = DataFrameUtils.get_column_as_list(df, column=None)
        assert result == []

    def test_get_column_as_list_with_missing_column(self):
        """Test get_column_as_list returns empty list when column doesn't exist."""
        df = DataFrameUtils.create_polars({"id": [1, 2, 3]})
        result = DataFrameUtils.get_column_as_list(df, column="nonexistent")
        assert result == []

    def test_get_column_as_series_pandas_with_none_df(self):
        """Test get_column_as_series_pandas returns None when DataFrame is None."""
        result = DataFrameUtils.get_column_as_series_pandas(None, column="id")
        assert result is None

    def test_get_column_as_series_pandas_with_none_column(self):
        """Test get_column_as_series_pandas returns None when column is None."""
        df = DataFrameUtils.create_pandas({"id": [1, 2, 3]})
        result = DataFrameUtils.get_column_as_series_pandas(df, column=None)
        assert result is None

    def test_get_column_as_series_pandas_with_missing_column(self):
        """Test get_column_as_series_pandas returns None when column doesn't exist."""
        df = DataFrameUtils.create_pandas({"id": [1, 2, 3]})
        result = DataFrameUtils.get_column_as_series_pandas(df, column="nonexistent")
        assert result is None

    def test_get_column_as_series_polars_with_none_df(self):
        """Test get_column_as_series_polars returns None when DataFrame is None."""
        result = DataFrameUtils.get_column_as_series_polars(None, column="id")
        assert result is None

    def test_get_column_as_series_polars_with_none_column(self):
        """Test get_column_as_series_polars returns None when column is None."""
        df = DataFrameUtils.create_polars({"id": [1, 2, 3]})
        result = DataFrameUtils.get_column_as_series_polars(df, column=None)
        assert result is None

    def test_get_column_as_series_polars_with_missing_column(self):
        """Test get_column_as_series_polars returns None when column doesn't exist."""
        df = DataFrameUtils.create_polars({"id": [1, 2, 3]})
        result = DataFrameUtils.get_column_as_series_polars(df, column="nonexistent")
        assert result is None

    def test_get_column_as_set_with_none_df(self):
        """Test get_column_as_set returns empty set when DataFrame is None."""
        result = DataFrameUtils.get_column_as_set(None, column="id")
        assert result == set()

    def test_get_column_as_set_with_none_column(self):
        """Test get_column_as_set returns empty set when column is None."""
        df = DataFrameUtils.create_polars({"id": [1, 2, 3]})
        result = DataFrameUtils.get_column_as_set(df, column=None)
        assert result == set()

    def test_get_column_as_set_with_empty_list_result(self):
        """Test get_column_as_set returns empty set when column extraction returns empty list."""
        df = DataFrameUtils.create_polars({"id": [1, 2, 3]})
        result = DataFrameUtils.get_column_as_set(df, column="nonexistent")
        assert result == set()


@pytest.mark.unit
class TestEmptyDataFrameHandling:
    """Test handling of empty DataFrames."""

    def test_empty_dataframe_column_names(self):
        """Test column_names with empty DataFrame."""
        df = DataFrameUtils.create_polars({})
        result = DataFrameUtils.column_names(df)
        assert result == []

    def test_empty_dataframe_count(self):
        """Test count with empty DataFrame."""
        df = DataFrameUtils.create_polars({})
        result = DataFrameUtils.count(df)
        assert result == 0

    def test_empty_dataframe_to_list_of_dictionaries(self):
        """Test to_list_of_dictionaries with empty DataFrame."""
        df = DataFrameUtils.create_polars({})
        result = DataFrameUtils.to_list_of_dictionaries(df)
        assert result == []

    def test_empty_dataframe_to_dictionary_of_lists(self):
        """Test to_dictionary_of_lists with empty DataFrame."""
        df = DataFrameUtils.create_polars({})
        result = DataFrameUtils.to_dictionary_of_lists(df)
        assert result == {}

    def test_get_first_row_as_dict_empty_dataframe(self):
        """Test get_first_row_as_dict with empty DataFrame."""
        df = DataFrameUtils.create_polars({})
        result = DataFrameUtils.get_first_row_as_dict(df)
        assert result == {}


@pytest.mark.unit
class TestInvalidInputHandling:
    """Test handling of invalid or unsupported input types."""

    def test_cast_dataframe_invalid_framework(self):
        """Test cast_dataframe with invalid framework."""
        df = DataFrameUtils.create_polars({"id": [1, 2, 3]})

        with pytest.raises(ValueError, match="Invalid Dataframe Framework"):
            DataFrameUtils.cast_dataframe(df, dataframe_framework="invalid")
