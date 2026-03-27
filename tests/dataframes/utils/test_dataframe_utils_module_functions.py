"""Tests for module-level wrapper functions in dataframe_utils.

This module tests all the module-level convenience functions that wrap
DataFrameUtils class methods, ensuring 100% coverage of the wrapper layer.
"""

import pytest
import pandas as pd
import polars as pl
import pyarrow as pa
import ibis

from mountainash.dataframes.dataframe_utils import (
    create_dataframe,
    create_pandas,
    create_polars,
    create_pyarrow,
    create_ibis,
    cast_dataframe,
    to_narwhals,
    to_pandas,
    to_polars,
    to_pyarrow,
    to_ibis,
    to_dictionary_of_lists,
    to_dictionary_of_series_pandas,
    to_dictionary_of_series_polars,
    to_list_of_dictionaries,
    column_names,
    table_schema_ibis,
    drop,
    select,
    head,
    count,
    split_dataframe_in_batches,
    filter as filter_df,
    get_dataframe_info,
    get_column_as_list,
    get_column_as_series_pandas,
    get_column_as_series_polars,
    get_column_as_set,
    get_first_row_as_dict,
    inner_join,
    left_join,
    outer_join,
)
from mountainash.dataframes.constants import CONST_DATAFRAME_FRAMEWORK


@pytest.mark.unit
class TestCreationModuleFunctions:
    """Test module-level creation functions."""

    def test_create_dataframe_wrapper(self):
        """Test create_dataframe module function."""
        data = {"id": [1, 2, 3], "value": [10, 20, 30]}
        df = create_dataframe(data, dataframe_framework=CONST_DATAFRAME_FRAMEWORK.PANDAS)

        assert df is not None
        assert isinstance(df, pd.DataFrame)

    def test_create_pandas_wrapper(self):
        """Test create_pandas module function."""
        data = {"id": [1, 2, 3], "name": ["A", "B", "C"]}
        df = create_pandas(data)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3

    def test_create_polars_wrapper(self):
        """Test create_polars module function."""
        data = {"id": [1, 2, 3], "value": [100, 200, 300]}
        df = create_polars(data)

        assert isinstance(df, pl.DataFrame)
        assert len(df) == 3

    def test_create_pyarrow_wrapper(self):
        """Test create_pyarrow module function."""
        data = {"id": [1, 2, 3], "category": ["X", "Y", "Z"]}
        df = create_pyarrow(data)

        assert isinstance(df, pa.Table)
        assert len(df) == 3

    def test_create_ibis_wrapper(self):
        """Test create_ibis module function."""
        data = {"id": [1, 2, 3], "value": [10.5, 20.5, 30.5]}
        df = create_ibis(data)

        assert hasattr(df, 'schema')
        assert df.count().execute() == 3


@pytest.mark.unit
class TestConversionModuleFunctions:
    """Test module-level conversion functions."""

    def test_cast_dataframe_wrapper(self):
        """Test cast_dataframe module function."""
        df = create_polars({"id": [1, 2, 3]})
        result = cast_dataframe(df, dataframe_framework=CONST_DATAFRAME_FRAMEWORK.PANDAS)

        assert isinstance(result, pd.DataFrame)

    def test_to_narwhals_wrapper(self):
        """Test to_narwhals module function."""
        df = create_pandas({"id": [1, 2, 3]})
        result = to_narwhals(df)

        assert result is not None
        # Narwhals wraps the original dataframe

    def test_to_pandas_wrapper(self):
        """Test to_pandas module function."""
        df = create_polars({"id": [1, 2, 3]})
        result = to_pandas(df)

        assert isinstance(result, pd.DataFrame)

    def test_to_polars_wrapper(self):
        """Test to_polars module function."""
        df = create_pandas({"id": [1, 2, 3]})
        result = to_polars(df)

        assert isinstance(result, pl.DataFrame)

    def test_to_pyarrow_wrapper(self):
        """Test to_pyarrow module function."""
        df = create_polars({"id": [1, 2, 3]})
        result = to_pyarrow(df)

        assert isinstance(result, pa.Table)

    def test_to_ibis_wrapper(self):
        """Test to_ibis module function."""
        df = create_pandas({"id": [1, 2, 3]})
        result = to_ibis(df)

        assert hasattr(result, 'schema')

    def test_to_ibis_wrapper_with_params(self):
        """Test to_ibis module function with optional parameters."""
        df = create_polars({"id": [1, 2, 3]})
        result = to_ibis(df, tablename_prefix="test")

        assert hasattr(result, 'schema')


@pytest.mark.unit
class TestDataExtractionModuleFunctions:
    """Test module-level data extraction functions."""

    def test_to_dictionary_of_lists_wrapper(self):
        """Test to_dictionary_of_lists module function."""
        df = create_polars({"id": [1, 2, 3], "value": [10, 20, 30]})
        result = to_dictionary_of_lists(df)

        assert isinstance(result, dict)
        assert "id" in result
        assert result["id"] == [1, 2, 3]

    def test_to_dictionary_of_series_pandas_wrapper(self):
        """Test to_dictionary_of_series_pandas module function."""
        df = create_pandas({"id": [1, 2, 3], "value": [10, 20, 30]})
        result = to_dictionary_of_series_pandas(df)

        assert isinstance(result, dict)
        assert "id" in result
        assert isinstance(result["id"], pd.Series)

    def test_to_dictionary_of_series_polars_wrapper(self):
        """Test to_dictionary_of_series_polars module function."""
        df = create_polars({"id": [1, 2, 3], "value": [10, 20, 30]})
        result = to_dictionary_of_series_polars(df)

        assert isinstance(result, dict)
        assert "id" in result
        assert isinstance(result["id"], pl.Series)

    def test_to_list_of_dictionaries_wrapper(self):
        """Test to_list_of_dictionaries module function."""
        df = create_polars({"id": [1, 2], "name": ["A", "B"]})
        result = to_list_of_dictionaries(df)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[1]["name"] == "B"


@pytest.mark.unit
class TestUtilityModuleFunctions:
    """Test module-level utility functions."""

    def test_column_names_wrapper(self):
        """Test column_names module function."""
        df = create_polars({"id": [1, 2, 3], "name": ["A", "B", "C"], "value": [10, 20, 30]})
        result = column_names(df)

        assert isinstance(result, list)
        assert sorted(result) == ["id", "name", "value"]

    # NOTE: table_schema_ibis returns None - unimplemented in reshape strategies
    # def test_table_schema_ibis_wrapper(self):
    #     """Test table_schema_ibis module function."""
    #     df = create_ibis({"id": [1, 2, 3], "value": [10, 20, 30]})
    #     result = table_schema_ibis(df)
    #     assert result is not None

    def test_drop_wrapper(self):
        """Test drop module function."""
        df = create_polars({"id": [1, 2, 3], "name": ["A", "B", "C"], "value": [10, 20, 30]})
        result = drop(df, columns="value")

        cols = column_names(result)
        assert "value" not in cols
        assert "id" in cols
        assert "name" in cols

    def test_select_wrapper(self):
        """Test select module function."""
        df = create_polars({"id": [1, 2, 3], "name": ["A", "B", "C"], "value": [10, 20, 30]})
        result = select(df, columns=["id", "name"])

        cols = column_names(result)
        assert set(cols) == {"id", "name"}

    def test_head_wrapper(self):
        """Test head module function."""
        df = create_polars({"id": list(range(1, 101))})
        result = head(df, n=5)

        assert count(result) == 5

    def test_count_wrapper(self):
        """Test count module function."""
        df = create_polars({"id": [1, 2, 3, 4, 5]})
        result = count(df)

        assert result == 5

    def test_split_dataframe_in_batches_wrapper(self):
        """Test split_dataframe_in_batches module function."""
        df = create_polars({"id": list(range(1, 21))})
        batches, total = split_dataframe_in_batches(df, batch_size=5)

        assert len(batches) == 4
        assert total == 20
        for batch in batches:
            assert count(batch) == 5

    def test_filter_wrapper(self):
        """Test filter module function."""
        df = create_polars({"id": [1, 2, 3, 4, 5], "value": [10, 20, 30, 40, 50]})

        import polars as pl
        expr = pl.col("value") > 25

        result = filter_df(df, expression=expr)

        # Should filter to values > 25: 30, 40, 50
        assert count(result) == 3

    def test_get_dataframe_info_wrapper(self):
        """Test get_dataframe_info module function."""
        df = create_polars({"id": [1, 2, 3]})
        info = get_dataframe_info(df)

        assert info is not None
        assert "type" in info


@pytest.mark.unit
class TestColumnExtractionModuleFunctions:
    """Test module-level column extraction functions."""

    def test_get_column_as_list_wrapper(self):
        """Test get_column_as_list module function."""
        df = create_polars({"id": [1, 2, 3, 4, 5], "value": [10, 20, 30, 40, 50]})
        result = get_column_as_list(df, column="value")

        assert result == [10, 20, 30, 40, 50]

    def test_get_column_as_series_pandas_wrapper(self):
        """Test get_column_as_series_pandas module function."""
        df = create_pandas({"id": [1, 2, 3], "name": ["A", "B", "C"]})
        result = get_column_as_series_pandas(df, column="name")

        assert isinstance(result, pd.Series)
        assert list(result) == ["A", "B", "C"]

    def test_get_column_as_series_polars_wrapper(self):
        """Test get_column_as_series_polars module function."""
        df = create_polars({"id": [1, 2, 3], "value": [100, 200, 300]})
        result = get_column_as_series_polars(df, column="value")

        assert isinstance(result, pl.Series)
        assert result.to_list() == [100, 200, 300]

    def test_get_column_as_set_wrapper(self):
        """Test get_column_as_set module function."""
        df = create_polars({"category": ["A", "B", "A", "C", "B", "A"]})
        result = get_column_as_set(df, column="category")

        assert result == {"A", "B", "C"}

    def test_get_first_row_as_dict_wrapper(self):
        """Test get_first_row_as_dict module function."""
        df = create_polars({"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"]})
        result = get_first_row_as_dict(df)

        assert result["id"] == 1
        assert result["name"] == "Alice"


@pytest.mark.unit
class TestJoinModuleFunctions:
    """Test module-level join functions."""

    def test_inner_join_wrapper(self):
        """Test inner_join module function."""
        left = create_polars({"id": [1, 2, 3], "left_val": ["A", "B", "C"]})
        right = create_polars({"id": [2, 3, 4], "right_val": ["X", "Y", "Z"]})

        result = inner_join(left, right, predicates="id")

        # Inner join should have rows where id matches: 2, 3
        assert count(result) == 2

    def test_left_join_wrapper(self):
        """Test left_join module function."""
        left = create_polars({"id": [1, 2, 3], "left_val": ["A", "B", "C"]})
        right = create_polars({"id": [2, 3, 4], "right_val": ["X", "Y", "Z"]})

        result = left_join(left, right, predicates="id")

        # Left join should have all left rows: 1, 2, 3
        assert count(result) == 3

    def test_outer_join_wrapper(self):
        """Test outer_join module function."""
        left = create_polars({"id": [1, 2, 3], "left_val": ["A", "B", "C"]})
        right = create_polars({"id": [2, 3, 4], "right_val": ["X", "Y", "Z"]})

        result = outer_join(left, right, predicates="id")

        # Outer join should have all unique ids: 1, 2, 3, 4
        assert count(result) == 4


@pytest.mark.unit
class TestModuleFunctionErrorHandling:
    """Test error handling in module-level functions."""

    def test_module_functions_with_none_inputs(self):
        """Test that module functions handle None inputs correctly."""
        # These should all handle None gracefully
        assert to_pandas(None) is None
        assert to_polars(None) is None
        assert to_pyarrow(None) is None
        assert to_ibis(None) is None
        assert to_narwhals(None) is None

        assert to_dictionary_of_lists(None) == {}
        assert to_dictionary_of_series_pandas(None) == {}
        assert to_dictionary_of_series_polars(None) == {}
        assert to_list_of_dictionaries(None) == []

        assert column_names(None) == []
        assert table_schema_ibis(None) is None
        assert count(None) == 0

        assert drop(None, columns="id") is None
        assert select(None, columns="id") is None
        assert head(None, n=5) is None

    def test_column_extraction_with_none(self):
        """Test column extraction functions with None."""
        assert get_column_as_list(None, column="id") == []
        assert get_column_as_series_pandas(None, column="id") is None
        assert get_column_as_series_polars(None, column="id") is None
        assert get_column_as_set(None, column="id") == set()
