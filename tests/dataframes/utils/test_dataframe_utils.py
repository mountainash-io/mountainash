import pytest
from pytest_check import check
import pandas as pd
import polars as pl
from polars.exceptions import ShapeError
import pyarrow as pa
import ibis
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Any, Union

from mountainash.dataframes import DataFrameUtils
# from mountainash_constants import CONST_DATAFRAME_FRAMEWORK
from mountainash.dataframes.constants import CONST_DATAFRAME_FRAMEWORK
import ibis
ibis.set_backend("polars")

# Test Data Fixtures
@pytest.fixture
def sample_data_clean() -> Dict[str, List[Any]]:
    """Clean test data with consistent types and lengths."""
    return {
        "integers": [1, 2, 3],
        "floats": [4.0, 5.0, 6.0],
        "strings": ["A", "B", "C"],
        "booleans": [True, False, True],
        "dates": [date(2023, 1, 1), date(2023, 1, 2), date(2023, 1, 3)],
        "decimals": [Decimal("1.1"), Decimal("2.2"), Decimal("3.3")]
    }

@pytest.fixture
def sample_data_mixed_types() -> Dict[str, List[Any]]:
    """Test data with mixed types in columns."""
    return {
        "mixed_ints_floats": [1, 2.5, 3],
        "mixed_strings_ints": ["1", 2, "3"],
        "mixed_nulls": [1, None, 3],
        "mixed_complex": [1, "string", True]
    }

@pytest.fixture
def sample_data_uneven() -> Dict[str, List[Any]]:
    """Test data with uneven column lengths."""
    return {
        "short": [1, 2],
        "medium": [1, 2, 3],
        "long": [1, 2, 3, 4, 5]
    }

@pytest.fixture
def sample_column_mappings() -> Dict[str, Dict[str, Any]]:
    """Various column mapping scenarios."""
    return {
        "simple": {
            "integers": "numbers",
            "strings": "text"
        },
        "with_types": {
            "integers": {"target_name": "numbers", "data_type": "integer"},
            "floats": {"target_name": "decimals", "data_type": "float"}
        },
        "invalid": {
            "integers": 123,  # Invalid mapping
            "missing": "column"  # Non-existent column
        }
    }

@pytest.fixture
def sample_dataframes(sample_data_clean):
    """Create sample dataframes in different formats."""
    return {
        "pandas": pd.DataFrame(sample_data_clean),
        "polars": pl.DataFrame(sample_data_clean),
        "pyarrow": pa.Table.from_pydict(sample_data_clean),
        "ibis": ibis.memtable(sample_data_clean)
    }

# Create DataFrame Tests
class TestCreateDataFrame:
    """Tests for DataFrame creation functionality."""

    @pytest.mark.parametrize("framework", [
        CONST_DATAFRAME_FRAMEWORK.PANDAS,
        CONST_DATAFRAME_FRAMEWORK.POLARS,
        CONST_DATAFRAME_FRAMEWORK.IBIS,
        CONST_DATAFRAME_FRAMEWORK.PYARROW,
        # CONST_DATAFRAME_FRAMEWORK.NARWHALS
    ])
    def test_create_basic_dataframe(self, framework, sample_data_clean):
        """Test basic dataframe creation with clean data."""
        df = DataFrameUtils.create_dataframe(sample_data_clean,
            dataframe_framework=framework,
        )
        assert DataFrameUtils.count(df) == 3
        assert set(DataFrameUtils.column_names(df)) == set(sample_data_clean.keys())

    @pytest.mark.parametrize("framework", [
        CONST_DATAFRAME_FRAMEWORK.PANDAS,
        CONST_DATAFRAME_FRAMEWORK.POLARS,
        CONST_DATAFRAME_FRAMEWORK.IBIS
    ])
    def test_create_with_column_mapping(self, framework, sample_data_clean, sample_column_mappings):
        """Test dataframe creation with column mappings."""
        df = DataFrameUtils.create_dataframe(sample_data_clean,
            dataframe_framework=framework,
            column_config=sample_column_mappings["simple"]
        )
        assert "numbers" in DataFrameUtils.column_names(df)
        assert "text" in DataFrameUtils.column_names(df)

    @pytest.mark.parametrize("framework", [
        CONST_DATAFRAME_FRAMEWORK.PANDAS,
        CONST_DATAFRAME_FRAMEWORK.POLARS,
        CONST_DATAFRAME_FRAMEWORK.IBIS
    ])
    def test_create_with_mixed_types(self, framework, sample_data_mixed_types):
        """Test dataframe creation with mixed type data."""
        df = DataFrameUtils.create_dataframe(sample_data_mixed_types,
            dataframe_framework=framework,
        )
        assert DataFrameUtils.count(df) == 3

    def test_create_with_invalid_framework(self, sample_data_clean):
        """Test creation with invalid framework specification."""
        with pytest.raises(ValueError):
            DataFrameUtils.create_dataframe(sample_data_clean,
                dataframe_framework="invalid",
            )

    def test_create_with_uneven_data(self, sample_data_uneven):
        """Test creation with uneven column lengths."""
        with pytest.raises(ShapeError):
            DataFrameUtils.create_dataframe(sample_data_uneven,
                dataframe_framework=CONST_DATAFRAME_FRAMEWORK.POLARS,
            )

# Conversion Tests
class TestDataFrameConversion:
    """Tests for DataFrame conversion functionality."""

    @pytest.mark.parametrize("source_df", ["pandas", "polars", "pyarrow", "ibis"])
    def test_to_pandas(self, source_df, sample_dataframes):
        """Test conversion to pandas DataFrame."""
        df = DataFrameUtils.to_pandas(sample_dataframes[source_df])
        assert isinstance(df, pd.DataFrame)
        assert df.shape[0] == 3

    @pytest.mark.parametrize("source_df", ["pandas", "polars", "pyarrow", "ibis"])
    def test_to_polars(self, source_df, sample_dataframes):
        """Test conversion to polars DataFrame.

        Note: Ibis is inherently lazy, so with as_lazy=None (default),
        it will return a LazyFrame. Other backends return eager DataFrames.
        """
        df = DataFrameUtils.to_polars(sample_dataframes[source_df])

        if source_df == "ibis":
            # Ibis is lazy, so default behavior preserves laziness
            assert isinstance(df, pl.LazyFrame)
            # Collect to verify data
            collected = df.collect()
            assert collected.shape[0] == 3
        else:
            # Other backends are eager by default
            assert isinstance(df, pl.DataFrame)
            assert df.shape[0] == 3

    @pytest.mark.parametrize("source_df", ["pandas", "polars", "pyarrow", "ibis"])
    def test_to_arrow(self, source_df, sample_dataframes):
        """Test conversion to Arrow table."""
        df = DataFrameUtils.to_pyarrow(sample_dataframes[source_df])
        assert isinstance(df, pa.Table)
        assert df.num_rows == 3

# Column Operation Tests
class TestColumnOperations:
    """Tests for column operations."""

    @pytest.mark.parametrize("framework", [
        CONST_DATAFRAME_FRAMEWORK.PANDAS,
        CONST_DATAFRAME_FRAMEWORK.POLARS,
        CONST_DATAFRAME_FRAMEWORK.IBIS
    ])
    def test_drop_columns(self, framework, sample_data_clean):
        """Test dropping columns."""
        df = DataFrameUtils.create_dataframe(sample_data_clean, dataframe_framework=framework)
        columns_to_drop = ["integers", "floats"]
        result = DataFrameUtils.drop(df, columns_to_drop)

        assert all(col not in DataFrameUtils.column_names(result) for col in columns_to_drop)

    @pytest.mark.parametrize("framework", [
        CONST_DATAFRAME_FRAMEWORK.PANDAS,
        CONST_DATAFRAME_FRAMEWORK.POLARS,
        CONST_DATAFRAME_FRAMEWORK.IBIS
    ])
    def test_select_columns(self, framework, sample_data_clean):
        """Test selecting columns."""
        df = DataFrameUtils.create_dataframe(sample_data_clean, dataframe_framework=framework)
        columns_to_select = ["integers", "strings"]
        result = DataFrameUtils.select(df, columns_to_select)
        assert set(DataFrameUtils.column_names(result)) == set(columns_to_select)

# Data Export Tests
class TestDataExport:
    """Tests for data export functionality."""

    @pytest.mark.parametrize("framework", [
        CONST_DATAFRAME_FRAMEWORK.PANDAS,
        CONST_DATAFRAME_FRAMEWORK.POLARS,
        CONST_DATAFRAME_FRAMEWORK.IBIS
    ])
    def test_to_dict_of_lists(self, framework, sample_data_clean):
        """Test conversion to dictionary of lists."""
        df = DataFrameUtils.create_dataframe(sample_data_clean, dataframe_framework=framework)
        result = DataFrameUtils.to_dictionary_of_lists(df)
        assert isinstance(result, dict)
        assert all(isinstance(v, list) for v in result.values())

    @pytest.mark.parametrize("framework", [
        CONST_DATAFRAME_FRAMEWORK.PANDAS,
        CONST_DATAFRAME_FRAMEWORK.POLARS,
        CONST_DATAFRAME_FRAMEWORK.IBIS
    ])
    def test_to_list_of_dicts(self, framework, sample_data_clean):
        """Test conversion to list of dictionaries."""
        df = DataFrameUtils.create_dataframe(sample_data_clean, dataframe_framework=framework)
        result = DataFrameUtils.to_list_of_dictionaries(df)
        assert isinstance(result, list)
        assert all(isinstance(d, dict) for d in result)

# Error Cases Tests
class TestErrorCases:
    """Tests for error handling."""

    def test_invalid_column_names(self, sample_data_clean):
        """Test handling of invalid column names."""
        invalid_mapping = {123: "column", "valid": None}
        with pytest.raises(ValueError):
            DataFrameUtils.create_dataframe(sample_data_clean,
                CONST_DATAFRAME_FRAMEWORK.POLARS,
                invalid_mapping
            )

    def test_invalid_data_types(self, sample_data_clean):
        """Test handling of invalid data types."""
        invalid_data = sample_data_clean.copy()
        invalid_data["invalid"] = [object(), object()]

        with pytest.raises(ShapeError):
            DataFrameUtils.create_dataframe(invalid_data,
                CONST_DATAFRAME_FRAMEWORK.POLARS,

            )

# # Performance Tests
# @pytest.mark.performance
# class TestPerformance:
#     """Performance tests."""

#     def test_large_dataframe_creation(self):
#         """Test creation of large dataframe."""
#         large_data = {
#             "column_" + str(i): list(range(10000))
#             for i in range(10)
#         }
#         df = DataFrameUtils.create_dataframe(
#             CONST_DATAFRAME_FRAMEWORK.POLARS,
#             large_data
#         )
#         assert DataFrameUtils.count(df) == 10000

#     def test_large_dataframe_conversion(self):
#         """Test conversion of large dataframe."""
#         large_data = {
#             "column_" + str(i): list(range(10000))
#             for i in range(10)
#         }
#         df = pl.DataFrame(large_data)
#         result = DataFrameUtils.cast_dataframe_to_pandas(df)
#         assert len(result) == 10000

# Utility Functions
@pytest.fixture
def create_test_df():
    """Utility function to create test dataframes."""
    def _create_df(framework: str, data: Dict[str, List[Any]], columns: Dict[str, str] = None):
        return DataFrameUtils.create_dataframe(data, framework, columns)
    return _create_df
