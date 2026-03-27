"""Tests for previously uncovered DataFrameUtils methods.

This module targets specific methods that had low or zero coverage:
- distinct()
- table_schema_ibis()
- get_column_as_series_pandas()
- get_column_as_series_polars()
- get_column_as_set()
- split_dataframe_in_batches()
- get_dataframe_info()
"""

import pytest
import pandas as pd
import polars as pl
import pyarrow as pa
import ibis
import narwhals as nw

from mountainash.dataframes import DataFrameUtils


# NOTE: distinct() method is defined in dataframe_utils.py but not implemented
# in reshape strategies. Skipping tests for unimplemented method.


# NOTE: table_schema_ibis() method exists in dataframe_utils.py but _table_schema
# implementation in reshape strategies returns None. Skipping tests for unimplemented method.


@pytest.mark.unit
class TestGetColumnAsSeriesPandas:
    """Test get_column_as_series_pandas() method."""

    def test_get_column_as_series_pandas_basic(self):
        """Test basic column extraction as pandas Series."""
        df = DataFrameUtils.create_pandas({
            "id": [1, 2, 3, 4, 5],
            "value": [10, 20, 30, 40, 50]
        })

        result = DataFrameUtils.get_column_as_series_pandas(df, column="value")

        assert result is not None
        assert isinstance(result, pd.Series)
        assert len(result) == 5
        assert list(result) == [10, 20, 30, 40, 50]

    def test_get_column_as_series_pandas_from_polars(self):
        """Test column extraction from polars DataFrame."""
        df = DataFrameUtils.create_polars({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"]
        })

        result = DataFrameUtils.get_column_as_series_pandas(df, column="name")

        assert result is not None
        assert isinstance(result, pd.Series)
        assert list(result) == ["Alice", "Bob", "Charlie"]

    def test_get_column_as_series_pandas_from_pyarrow(self):
        """Test column extraction from pyarrow Table."""
        df = DataFrameUtils.create_pyarrow({
            "id": [1, 2, 3],
            "value": [100, 200, 300]
        })

        result = DataFrameUtils.get_column_as_series_pandas(df, column="value")

        assert result is not None
        assert isinstance(result, pd.Series)


@pytest.mark.unit
class TestGetColumnAsSeriesPolars:
    """Test get_column_as_series_polars() method."""

    def test_get_column_as_series_polars_basic(self):
        """Test basic column extraction as polars Series."""
        df = DataFrameUtils.create_polars({
            "id": [1, 2, 3, 4, 5],
            "value": [10, 20, 30, 40, 50]
        })

        result = DataFrameUtils.get_column_as_series_polars(df, column="value")

        assert result is not None
        assert isinstance(result, pl.Series)
        assert len(result) == 5
        assert result.to_list() == [10, 20, 30, 40, 50]

    def test_get_column_as_series_polars_from_pandas(self):
        """Test column extraction from pandas DataFrame."""
        df = DataFrameUtils.create_pandas({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"]
        })

        result = DataFrameUtils.get_column_as_series_polars(df, column="name")

        assert result is not None
        assert isinstance(result, pl.Series)
        assert result.to_list() == ["Alice", "Bob", "Charlie"]

    def test_get_column_as_series_polars_from_pyarrow(self):
        """Test column extraction from pyarrow Table."""
        df = DataFrameUtils.create_pyarrow({
            "id": [1, 2, 3],
            "value": [100, 200, 300]
        })

        result = DataFrameUtils.get_column_as_series_polars(df, column="value")

        assert result is not None
        assert isinstance(result, pl.Series)


@pytest.mark.unit
class TestGetColumnAsSet:
    """Test get_column_as_set() method."""

    def test_get_column_as_set_basic(self):
        """Test basic column extraction as set."""
        df = DataFrameUtils.create_polars({
            "id": [1, 2, 2, 3, 3, 3],
            "category": ["A", "B", "B", "C", "C", "C"]
        })

        result = DataFrameUtils.get_column_as_set(df, column="id")

        assert result == {1, 2, 3}

    def test_get_column_as_set_with_duplicates(self):
        """Test that get_column_as_set removes duplicates."""
        df = DataFrameUtils.create_pandas({
            "value": ["X", "Y", "X", "Z", "Y", "X"]
        })

        result = DataFrameUtils.get_column_as_set(df, column="value")

        assert result == {"X", "Y", "Z"}
        assert len(result) == 3

    def test_get_column_as_set_from_pyarrow(self):
        """Test get_column_as_set from pyarrow."""
        df = DataFrameUtils.create_pyarrow({
            "category": ["A", "B", "A", "C", "B", "A"]
        })

        result = DataFrameUtils.get_column_as_set(df, column="category")

        assert result == {"A", "B", "C"}

    def test_get_column_as_set_empty_column(self):
        """Test get_column_as_set with column that yields empty result."""
        df = DataFrameUtils.create_polars({"id": [1, 2, 3]})

        # Non-existent column should return empty set
        result = DataFrameUtils.get_column_as_set(df, column="nonexistent")

        assert result == set()


@pytest.mark.unit
class TestSplitDataFrameInBatches:
    """Test split_dataframe_in_batches() method."""

    def test_split_in_batches_pandas(self):
        """Test splitting pandas DataFrame into batches."""
        df = DataFrameUtils.create_pandas({
            "id": list(range(1, 101)),  # 100 rows
            "value": list(range(100, 200))
        })

        batches, total = DataFrameUtils.split_dataframe_in_batches(df, batch_size=25)

        # Should create 4 batches of 25 rows each
        assert batches is not None
        assert isinstance(batches, list)
        assert len(batches) == 4
        assert total == 100

        # Verify each batch size
        for batch in batches:
            assert DataFrameUtils.count(batch) == 25

    def test_split_in_batches_polars(self):
        """Test splitting polars DataFrame into batches."""
        df = DataFrameUtils.create_polars({
            "id": list(range(1, 51)),  # 50 rows
            "value": list(range(50, 100))
        })

        batches, total = DataFrameUtils.split_dataframe_in_batches(df, batch_size=10)

        assert batches is not None
        assert isinstance(batches, list)
        assert len(batches) == 5
        assert total == 50

        for batch in batches:
            assert DataFrameUtils.count(batch) == 10

    def test_split_in_batches_uneven_split(self):
        """Test splitting with uneven batch sizes."""
        df = DataFrameUtils.create_polars({
            "id": list(range(1, 23))  # 22 rows
        })

        batches, total = DataFrameUtils.split_dataframe_in_batches(df, batch_size=10)

        assert len(batches) == 3
        assert total == 22
        # First two batches should be 10, last batch should be 2
        assert DataFrameUtils.count(batches[0]) == 10
        assert DataFrameUtils.count(batches[1]) == 10
        assert DataFrameUtils.count(batches[2]) == 2


@pytest.mark.unit
class TestGetDataFrameInfo:
    """Test get_dataframe_info() method."""

    def test_get_dataframe_info_pandas(self):
        """Test get_dataframe_info with pandas DataFrame."""
        df = DataFrameUtils.create_pandas({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "value": [10.5, 20.0, 30.5]
        })

        info = DataFrameUtils.get_dataframe_info(df)

        assert info is not None
        assert "type" in info
        assert "shape" in info or "rows" in info
        assert "columns" in info

    def test_get_dataframe_info_polars(self):
        """Test get_dataframe_info with polars DataFrame."""
        df = DataFrameUtils.create_polars({
            "id": [1, 2, 3, 4, 5],
            "value": [10, 20, 30, 40, 50]
        })

        info = DataFrameUtils.get_dataframe_info(df)

        assert info is not None
        assert "type" in info
        assert "DataFrame" in info["type"] or "Polars" in str(info["type"])

    def test_get_dataframe_info_pyarrow(self):
        """Test get_dataframe_info with pyarrow Table."""
        df = DataFrameUtils.create_pyarrow({
            "id": [1, 2, 3],
            "name": ["A", "B", "C"]
        })

        info = DataFrameUtils.get_dataframe_info(df)

        assert info is not None
        assert "type" in info

    def test_get_dataframe_info_ibis(self):
        """Test get_dataframe_info with ibis Table."""
        df = DataFrameUtils.create_ibis({
            "id": [1, 2, 3],
            "value": [100, 200, 300]
        })

        info = DataFrameUtils.get_dataframe_info(df)

        assert info is not None
        assert "type" in info
        assert "columns" in info or "schema" in info

    def test_get_dataframe_info_narwhals(self):
        """Test get_dataframe_info with narwhals DataFrame."""
        pandas_df = DataFrameUtils.create_pandas({"id": [1, 2, 3]})
        nw_df = nw.from_native(pandas_df)

        info = DataFrameUtils.get_dataframe_info(nw_df)

        assert info is not None
        assert "type" in info


@pytest.mark.unit
class TestCrossBackendConsistency:
    """Test that methods produce consistent results across backends."""

    def test_get_column_as_set_consistency(self):
        """Test get_column_as_set produces same result across backends."""
        data = {"category": ["A", "B", "A", "C", "B", "A"]}

        pandas_df = DataFrameUtils.create_pandas(data)
        polars_df = DataFrameUtils.create_polars(data)
        pyarrow_df = DataFrameUtils.create_pyarrow(data)

        pandas_set = DataFrameUtils.get_column_as_set(pandas_df, column="category")
        polars_set = DataFrameUtils.get_column_as_set(polars_df, column="category")
        pyarrow_set = DataFrameUtils.get_column_as_set(pyarrow_df, column="category")

        expected_set = {"A", "B", "C"}
        assert pandas_set == expected_set
        assert polars_set == expected_set
        assert pyarrow_set == expected_set
