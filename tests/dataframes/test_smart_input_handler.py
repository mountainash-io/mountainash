"""
Tests for SmartInputHandlerMixin functionality.

Tests automatic conversion of Python data structures to DataFrames
and framework preservation logic.
"""

from __future__ import annotations

import pytest
import polars as pl
import pandas as pd

from mountainash.dataframes import DataFrameUtils
from mountainash.dataframes.constants import CONST_DATAFRAME_FRAMEWORK, CONST_DATAFRAME_TYPE
from mountainash.dataframes.mixins import DynamicInputHandlerMixin


# ============================================================================
# Normalize Input Tests - DataFrame Inputs
# ============================================================================

class TestNormalizeDataFrameInput:
    """Test normalization of DataFrame inputs."""

    def test_normalize_pandas_dataframe(self):
        """Test normalization of Pandas DataFrame preserves framework."""
        df = pd.DataFrame({"id": [1, 2, 3]})

        normalized, original_fw = DataFrameUtils._normalize_input(df)

        assert isinstance(normalized, pd.DataFrame)
        assert original_fw.value == CONST_DATAFRAME_TYPE.PANDAS_DATAFRAME.value
        assert normalized.equals(df)

    def test_normalize_polars_dataframe(self):
        """Test normalization of Polars DataFrame preserves framework."""
        df = pl.DataFrame({"id": [1, 2, 3]})

        normalized, original_fw = DataFrameUtils._normalize_input(df)

        assert isinstance(normalized, pl.DataFrame)
        assert original_fw.value == CONST_DATAFRAME_TYPE.POLARS_DATAFRAME.value
        assert normalized.equals(df)

    def test_normalize_polars_lazyframe(self):
        """Test normalization of Polars LazyFrame preserves framework."""
        df = pl.DataFrame({"id": [1, 2, 3]}).lazy()

        normalized, original_fw = DataFrameUtils._normalize_input(df)

        assert isinstance(normalized, pl.LazyFrame)
        assert original_fw.value == CONST_DATAFRAME_TYPE.POLARS_LAZYFRAME.value

    def test_normalize_dataframe_returns_unchanged(self):
        """Test normalization returns DataFrame unchanged."""
        df = pd.DataFrame({"id": [1, 2, 3]})

        normalized, original_fw = DataFrameUtils._normalize_input(df)

        # Should return as-is
        assert isinstance(normalized, pd.DataFrame)
        assert normalized.equals(df)
        # Original framework tracked
        assert original_fw.value == CONST_DATAFRAME_TYPE.PANDAS_DATAFRAME.value


# ============================================================================
# Normalize Input Tests - Python Data Inputs
# ============================================================================

class TestNormalizePythonDataInput:
    """Test normalization of Python data inputs."""

    def test_normalize_list_of_dicts(self):
        """Test normalization of list of dicts to Polars DataFrame."""
        data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]

        normalized, original_fw = DataFrameUtils._normalize_input(data)

        # Should convert to Polars by default
        assert isinstance(normalized, pl.DataFrame)
        # No original framework for Python data
        assert original_fw is None
        # Data preserved
        assert normalized.shape == (2, 2)
        assert "id" in normalized.columns
        assert "name" in normalized.columns

    def test_normalize_dict_of_lists(self):
        """Test normalization of dict of lists to Polars DataFrame."""
        data = {"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"]}

        normalized, original_fw = DataFrameUtils._normalize_input(data)

        assert isinstance(normalized, pl.DataFrame)
        assert original_fw is None
        assert normalized.shape == (3, 2)

    def test_normalize_collection_scalar_list(self):
        """Test normalization of scalar list to Polars DataFrame."""
        data = [1, 2, 3, 4, 5]

        normalized, original_fw = DataFrameUtils._normalize_input(data)

        assert isinstance(normalized, pl.DataFrame)
        assert original_fw is None
        assert normalized.shape == (5, 1)
        assert "value" in normalized.columns  # Default column name

    def test_normalize_python_data_default_polars(self):
        """Test normalization of Python data always converts to Polars."""
        data = [{"id": 1, "name": "Alice"}]

        normalized, original_fw = DataFrameUtils._normalize_input(data)

        # Should convert to Polars (default)
        assert isinstance(normalized, pl.DataFrame)
        # No original framework for Python data
        assert original_fw is None


# ============================================================================
# Normalize Input Tests - Error Cases
# ============================================================================

class TestNormalizeInputErrors:
    """Test error handling in input normalization."""

    # def test_normalize_none_input(self):
    #     """Test that None input raises ValueError."""
    #     with pytest.raises(ValueError, match="Input data cannot be None"):
    #         DataFrameUtils._normalize_input(None)

    def test_normalize_unsupported_type(self):
        """Test that unsupported type raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported input type"):
            DataFrameUtils._normalize_input("not a dataframe or data structure")

    def test_normalize_unsupported_object(self):
        """Test that random object raises ValueError."""
        class CustomObject:
            pass

        with pytest.raises(ValueError, match="Unsupported input type"):
            DataFrameUtils._normalize_input(CustomObject())


# ============================================================================
# Framework Preservation Tests
# ============================================================================

class TestFrameworkPreservation:
    """Test framework preservation logic."""

    def test_preserve_pandas_framework(self):
        """Test preserving Pandas framework through operation."""
        df = pd.DataFrame({"id": [1, 2, 3]})
        original_fw = CONST_DATAFRAME_TYPE.PANDAS_DATAFRAME

        # Simulate operation that might convert to Polars
        polars_result = pl.DataFrame({"id": [1, 2]})

        preserved = DataFrameUtils._preserve_output_framework(polars_result, original_fw)

        assert isinstance(preserved, pd.DataFrame)

    def test_preserve_polars_framework(self):
        """Test preserving Polars framework through operation."""
        df = pl.DataFrame({"id": [1, 2, 3]})
        original_fw = CONST_DATAFRAME_TYPE.POLARS_DATAFRAME

        # Simulate operation that might convert to Pandas
        pandas_result = pd.DataFrame({"id": [1, 2]})

        preserved = DataFrameUtils._preserve_output_framework(pandas_result, original_fw)

        assert isinstance(preserved, pl.DataFrame)

    def test_no_preservation_for_python_data(self):
        """Test that Python data has no framework to preserve."""
        result = pl.DataFrame({"id": [1, 2]})

        # original_fw is None for Python data
        preserved = DataFrameUtils._preserve_output_framework(result, None)

        # Should return unchanged
        assert isinstance(preserved, pl.DataFrame)
        assert preserved.equals(result)

    def test_preserve_already_correct_framework(self):
        """Test that preservation is skipped if already correct framework."""
        df = pl.DataFrame({"id": [1, 2, 3]})
        original_fw = CONST_DATAFRAME_TYPE.POLARS_DATAFRAME

        # Already in Polars - should return unchanged
        preserved = DataFrameUtils._preserve_output_framework(df, original_fw)

        assert isinstance(preserved, pl.DataFrame)
        assert preserved.equals(df)


# ============================================================================
# Filter Integration Tests - DataFrame Inputs
# ============================================================================

class TestFilterDataFrameInput:
    """Test filter() method with DataFrame inputs."""

    def test_filter_pandas_preserves_framework(self):
        """Test filtering Pandas DataFrame preserves framework."""
        df = pd.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})

        result = DataFrameUtils.filter(df, df["id"] > 1)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert list(result["id"]) == [2, 3]

    def test_filter_polars_preserves_framework(self):
        """Test filtering Polars DataFrame preserves framework."""
        df = pl.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})

        result = DataFrameUtils.filter(df, pl.col("id") > 1)

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 2
        assert result["id"].to_list() == [2, 3]



# ============================================================================
# Filter Integration Tests - Python Data Inputs
# ============================================================================

class TestFilterPythonDataInput:
    """Test filter() method with Python data inputs."""

    def test_filter_list_of_dicts(self):
        """Test filtering list of dicts converts to Polars."""
        data = [
            {"id": 1, "value": 10},
            {"id": 2, "value": 20},
            {"id": 3, "value": 30}
        ]

        result = DataFrameUtils.filter(data, pl.col("id") > 1)

        # Should convert to Polars by default
        assert isinstance(result, pl.DataFrame)
        assert len(result) == 2
        assert result["id"].to_list() == [2, 3]

    def test_filter_dict_of_lists(self):
        """Test filtering dict of lists converts to Polars."""
        data = {
            "id": [1, 2, 3],
            "value": [10, 20, 30]
        }

        result = DataFrameUtils.filter(data, pl.col("id") > 1)

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 2

    def test_filter_python_data_then_cast(self):
        """Test filtering Python data then casting to different framework."""
        data = [{"id": 1}, {"id": 2}, {"id": 3}]

        # Filter returns Polars (default for Python data)
        result_polars = DataFrameUtils.filter(data, pl.col("id") > 1)
        assert isinstance(result_polars, pl.DataFrame)
        assert len(result_polars) == 2

        # Want Pandas? Cast afterward
        result_pandas = DataFrameUtils.to_pandas(result_polars)
        assert isinstance(result_pandas, pd.DataFrame)
        assert len(result_pandas) == 2

    def test_filter_empty_list(self):
        """Test filtering empty list."""
        data = []

        # Empty data should be handled gracefully
        with pytest.raises((ValueError, Exception)):
            # Might raise error for empty data or unsupported type
            DataFrameUtils.filter(data, pl.col("id") > 1)


# ============================================================================
# Filter Integration Tests - Error Cases
# ============================================================================

class TestFilterErrorCases:
    """Test error handling in filter() method."""

    def test_filter_none_data(self):
        """Test that None data returns None (backward compatibility)."""
        result = DataFrameUtils.filter(None, pl.col("id") > 1)
        assert result is None

    def test_filter_unsupported_data_type(self):
        """Test that unsupported data type raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported input type"):
            DataFrameUtils.filter("not a dataframe", pl.col("id") > 1)

    def test_filter_with_invalid_expression(self):
        """Test that invalid expression raises error."""
        df = pl.DataFrame({"id": [1, 2, 3]})

        # Invalid expression should raise error
        with pytest.raises((ValueError, Exception)):
            DataFrameUtils.filter(df, "not an expression")


# ============================================================================
# Round-Trip Tests
# ============================================================================

class TestRoundTripConversions:
    """Test round-trip conversions: Python data → filter → validate."""

    def test_roundtrip_list_of_dicts_to_polars(self):
        """Test round-trip: list of dicts → filter → Polars."""
        original_data = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
            {"id": 3, "name": "Charlie"}
        ]

        result = DataFrameUtils.filter(original_data, pl.col("id") > 1)

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 2
        assert result["name"].to_list() == ["Bob", "Charlie"]

    def test_roundtrip_pandas_to_pandas(self):
        """Test round-trip: Pandas → filter → Pandas."""
        original_df = pd.DataFrame({"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"]})

        result = DataFrameUtils.filter(original_df, original_df["id"] > 1)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert list(result["name"]) == ["Bob", "Charlie"]

    def test_roundtrip_polars_to_polars(self):
        """Test round-trip: Polars → filter → Polars."""
        original_df = pl.DataFrame({"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"]})

        result = DataFrameUtils.filter(original_df, pl.col("id") > 1)

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 2
        assert result["name"].to_list() == ["Bob", "Charlie"]


# ============================================================================
# Backward Compatibility Tests
# ============================================================================

class TestBackwardCompatibility:
    """Test that existing DataFrame-only usage continues to work."""

    def test_existing_pandas_usage(self):
        """Test existing Pandas usage still works."""
        df = pd.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})

        # Old usage pattern - should still work
        result = DataFrameUtils.filter(df, df["id"] > 1)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2

    def test_existing_polars_usage(self):
        """Test existing Polars usage still works."""
        df = pl.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})

        # Old usage pattern - should still work
        result = DataFrameUtils.filter(df, pl.col("id") > 1)

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 2

    def test_no_breaking_changes_to_api(self):
        """Test that API is backward compatible."""
        df = pl.DataFrame({"id": [1, 2, 3]})

        # Old signature still works (new params are optional)
        result = DataFrameUtils.filter(df, pl.col("id") > 1)

        assert isinstance(result, pl.DataFrame)
