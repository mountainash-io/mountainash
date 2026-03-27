"""
Tests for DataframeFromCollection converter with round-trip validation.

This module tests the conversion of basic Python collections (list, set, frozenset)
to DataFrames and validates round-trip conversions.
"""

from __future__ import annotations

import pytest
import polars as pl

from mountainash.dataframes.ingress import (
    PydataConverterFactory,
    DataframeFromCollection
)
from mountainash.dataframes.cast import DataFrameCastFactory
from mountainash.dataframes.schema_config import SchemaConfig


# ============================================================================
# Detection Tests
# ============================================================================

class TestCollectionDetection:
    """Test detection of collection data formats."""

    def test_can_handle_list_of_integers(self):
        """Test detection of list of integers."""
        data = [1, 2, 3, 4, 5]
        assert DataframeFromCollection.can_handle(data) is True

    def test_can_handle_list_of_strings(self):
        """Test detection of list of strings."""
        data = ["apple", "banana", "cherry"]
        assert DataframeFromCollection.can_handle(data) is True

    def test_can_handle_list_of_floats(self):
        """Test detection of list of floats."""
        data = [1.5, 2.7, 3.9]
        assert DataframeFromCollection.can_handle(data) is True

    def test_can_handle_set_of_integers(self):
        """Test detection of set of integers."""
        data = {1, 2, 3, 4, 5}
        assert DataframeFromCollection.can_handle(data) is True

    def test_can_handle_set_of_strings(self):
        """Test detection of set of strings."""
        data = {"apple", "banana", "cherry"}
        assert DataframeFromCollection.can_handle(data) is True

    def test_can_handle_frozenset_of_integers(self):
        """Test detection of frozenset of integers."""
        data = frozenset([1, 2, 3, 4, 5])
        assert DataframeFromCollection.can_handle(data) is True

    def test_can_handle_frozenset_of_strings(self):
        """Test detection of frozenset of strings."""
        data = frozenset(["apple", "banana", "cherry"])
        assert DataframeFromCollection.can_handle(data) is True

    def test_can_handle_empty_list(self):
        """Test detection of empty list."""
        data = []
        assert DataframeFromCollection.can_handle(data) is True

    def test_can_handle_empty_set(self):
        """Test detection of empty set."""
        data = set()
        assert DataframeFromCollection.can_handle(data) is True

    def test_can_handle_empty_frozenset(self):
        """Test detection of empty frozenset."""
        data = frozenset()
        assert DataframeFromCollection.can_handle(data) is True

    def test_cannot_handle_list_of_dicts(self):
        """Test that list of dicts is not detected as collection."""
        data = [{"id": 1}, {"id": 2}]
        assert DataframeFromCollection.can_handle(data) is False

    def test_cannot_handle_list_of_tuples(self):
        """Test that list of tuples is not detected as collection."""
        data = [(1, 2), (3, 4)]
        assert DataframeFromCollection.can_handle(data) is False

    def test_cannot_handle_dict(self):
        """Test that dict is not detected as collection."""
        data = {"col1": [1, 2, 3]}
        assert DataframeFromCollection.can_handle(data) is False

    def test_cannot_handle_single_tuple(self):
        """Test that single tuple is not detected as collection."""
        data = (1, 2, 3)
        assert DataframeFromCollection.can_handle(data) is False


# ============================================================================
# Factory Detection Tests
# ============================================================================

class TestFactoryCollectionDetection:
    """Test factory detection of collection data formats."""

    def test_factory_detects_list_of_integers(self):
        """Test factory detects list of integers as COLLECTION."""
        from mountainash.dataframes.constants import CONST_PYTHON_DATAFORMAT

        data = [1, 2, 3, 4, 5]
        strategy_key = PydataConverterFactory._get_strategy_key(data)
        assert strategy_key == CONST_PYTHON_DATAFORMAT.COLLECTION

    def test_factory_detects_set_of_strings(self):
        """Test factory detects set of strings as COLLECTION."""
        from mountainash.dataframes.constants import CONST_PYTHON_DATAFORMAT

        data = {"apple", "banana", "cherry"}
        strategy_key = PydataConverterFactory._get_strategy_key(data)
        assert strategy_key == CONST_PYTHON_DATAFORMAT.COLLECTION

    def test_factory_detects_frozenset(self):
        """Test factory detects frozenset as COLLECTION."""
        from mountainash.dataframes.constants import CONST_PYTHON_DATAFORMAT

        data = frozenset([1.0, 2.5, 3.7])
        strategy_key = PydataConverterFactory._get_strategy_key(data)
        assert strategy_key == CONST_PYTHON_DATAFORMAT.COLLECTION

    def test_factory_detects_empty_list(self):
        """Test factory detects empty list as COLLECTION."""
        from mountainash.dataframes.constants import CONST_PYTHON_DATAFORMAT

        data = []
        strategy_key = PydataConverterFactory._get_strategy_key(data)
        assert strategy_key == CONST_PYTHON_DATAFORMAT.COLLECTION

    def test_factory_does_not_detect_list_of_dicts(self):
        """Test factory does not detect list of dicts as COLLECTION."""
        from mountainash.dataframes.constants import CONST_PYTHON_DATAFORMAT

        data = [{"id": 1}, {"id": 2}]
        strategy_key = PydataConverterFactory._get_strategy_key(data)
        assert strategy_key == CONST_PYTHON_DATAFORMAT.PYLIST


# ============================================================================
# Conversion Tests
# ============================================================================

class TestCollectionConversion:
    """Test conversion of collection data to DataFrame."""

    def test_convert_list_of_integers(self):
        """Test conversion of list of integers."""
        data = [1, 2, 3, 4, 5]
        df = DataframeFromCollection.convert(data)

        assert isinstance(df, pl.DataFrame)
        assert df.shape == (5, 1)
        assert df.columns == ["value"]
        assert df["value"].to_list() == [1, 2, 3, 4, 5]

    def test_convert_list_of_strings(self):
        """Test conversion of list of strings."""
        data = ["apple", "banana", "cherry"]
        df = DataframeFromCollection.convert(data)

        assert isinstance(df, pl.DataFrame)
        assert df.shape == (3, 1)
        assert df.columns == ["value"]
        assert df["value"].to_list() == ["apple", "banana", "cherry"]

    def test_convert_list_of_floats(self):
        """Test conversion of list of floats."""
        data = [1.5, 2.7, 3.9]
        df = DataframeFromCollection.convert(data)

        assert isinstance(df, pl.DataFrame)
        assert df.shape == (3, 1)
        assert df.columns == ["value"]
        assert df["value"].to_list() == [1.5, 2.7, 3.9]

    def test_convert_set_of_integers(self):
        """Test conversion of set of integers."""
        data = {1, 2, 3}
        df = DataframeFromCollection.convert(data)

        assert isinstance(df, pl.DataFrame)
        assert df.shape == (3, 1)
        assert df.columns == ["value"]
        # Set order is not guaranteed, so check contents
        assert set(df["value"].to_list()) == {1, 2, 3}

    def test_convert_set_of_strings(self):
        """Test conversion of set of strings."""
        data = {"apple", "banana", "cherry"}
        df = DataframeFromCollection.convert(data)

        assert isinstance(df, pl.DataFrame)
        assert df.shape == (3, 1)
        assert df.columns == ["value"]
        # Set order is not guaranteed, so check contents
        assert set(df["value"].to_list()) == {"apple", "banana", "cherry"}

    def test_convert_frozenset_of_integers(self):
        """Test conversion of frozenset of integers."""
        data = frozenset([1, 2, 3])
        df = DataframeFromCollection.convert(data)

        assert isinstance(df, pl.DataFrame)
        assert df.shape == (3, 1)
        assert df.columns == ["value"]
        # Set order is not guaranteed, so check contents
        assert set(df["value"].to_list()) == {1, 2, 3}

    def test_convert_empty_list(self):
        """Test conversion of empty list."""
        data = []
        df = DataframeFromCollection.convert(data)

        assert isinstance(df, pl.DataFrame)
        assert df.shape == (0, 1)
        assert df.columns == ["value"]

    def test_convert_empty_set(self):
        """Test conversion of empty set."""
        data = set()
        df = DataframeFromCollection.convert(data)

        assert isinstance(df, pl.DataFrame)
        assert df.shape == (0, 1)
        assert df.columns == ["value"]

    def test_convert_with_custom_column_name(self):
        """Test conversion with custom column name."""
        data = [1, 2, 3]
        df = DataframeFromCollection.convert(data, column_name="numbers")

        assert isinstance(df, pl.DataFrame)
        assert df.shape == (3, 1)
        assert df.columns == ["numbers"]
        assert df["numbers"].to_list() == [1, 2, 3]

    def test_convert_list_with_none_values(self):
        """Test conversion of list with None values."""
        data = [1, None, 3, None, 5]
        df = DataframeFromCollection.convert(data)

        assert isinstance(df, pl.DataFrame)
        assert df.shape == (5, 1)
        assert df.columns == ["value"]
        assert df["value"].to_list() == [1, None, 3, None, 5]

    def test_convert_list_with_mixed_numeric_types(self):
        """Test conversion of list with mixed numeric types."""
        # Polars 1.16+ raises an error for mixed numeric types without strict=False
        # This is expected behavior, so we test that it raises an error
        data = [1, 2.5, 3, 4.7]

        with pytest.raises(TypeError, match="unexpected value while building Series"):
            DataframeFromCollection.convert(data)


# ============================================================================
# Validation Tests
# ============================================================================

class TestCollectionValidation:
    """Test validation of collection data."""

    def test_convert_invalid_type_raises_error(self):
        """Test that invalid type raises ValueError."""
        data = "not a collection"
        with pytest.raises(ValueError, match="Container data must be list, set, or frozenset"):
            DataframeFromCollection.convert(data)

    def test_convert_dict_raises_error(self):
        """Test that dict raises ValueError."""
        data = {"col1": [1, 2, 3]}
        with pytest.raises(ValueError, match="Container data must be list, set, or frozenset"):
            DataframeFromCollection.convert(data)

    def test_convert_tuple_raises_error(self):
        """Test that tuple raises ValueError."""
        data = (1, 2, 3)
        with pytest.raises(ValueError, match="Container data must be list, set, or frozenset"):
            DataframeFromCollection.convert(data)

    def test_convert_list_of_dicts_raises_error(self):
        """Test that list of dicts raises ValueError."""
        data = [{"id": 1}, {"id": 2}]
        with pytest.raises(ValueError, match="Container has dict items"):
            DataframeFromCollection.convert(data)

    def test_convert_list_of_tuples_raises_error(self):
        """Test that list of tuples raises ValueError."""
        data = [(1, 2), (3, 4)]
        with pytest.raises(ValueError, match="Container has tuple items"):
            DataframeFromCollection.convert(data)


# ============================================================================
# Factory Integration Tests
# ============================================================================

class TestFactoryCollectionConversion:
    """Test factory-based conversion of collection data."""

    def test_factory_convert_list_of_integers(self):
        """Test factory conversion of list of integers."""
        data = [1, 2, 3, 4, 5]
        df = PydataConverterFactory.convert(data)

        assert isinstance(df, pl.DataFrame)
        assert df.shape == (5, 1)
        assert df.columns == ["value"]
        assert df["value"].to_list() == [1, 2, 3, 4, 5]

    def test_factory_convert_set_of_strings(self):
        """Test factory conversion of set of strings."""
        data = {"apple", "banana", "cherry"}
        df = PydataConverterFactory.convert(data)

        assert isinstance(df, pl.DataFrame)
        assert df.shape == (3, 1)
        assert df.columns == ["value"]
        assert set(df["value"].to_list()) == {"apple", "banana", "cherry"}

    def test_factory_convert_frozenset(self):
        """Test factory conversion of frozenset."""
        data = frozenset([1.0, 2.5, 3.7])
        df = PydataConverterFactory.convert(data)

        assert isinstance(df, pl.DataFrame)
        assert df.shape == (3, 1)
        assert df.columns == ["value"]
        assert set(df["value"].to_list()) == {1.0, 2.5, 3.7}

    def test_factory_convert_empty_list(self):
        """Test factory conversion of empty list."""
        data = []
        df = PydataConverterFactory.convert(data)

        assert isinstance(df, pl.DataFrame)
        assert df.shape == (0, 1)
        assert df.columns == ["value"]


# ============================================================================
# Column Transform Tests
# ============================================================================

class TestCollectionColumnTransform:
    """Test column transformations with collection data."""

    def test_convert_with_column_rename(self):
        """Test conversion with column renaming via ColumnTransformConfig."""
        data = [1, 2, 3]
        df = DataframeFromCollection.convert(data, column_name="numbers")

        # Apply column transformation
        config = SchemaConfig(
            columns={"numbers": {"rename": "values"}}
        )
        df_transformed = config.apply(df)

        assert df_transformed.columns == ["values"]
        assert df_transformed["values"].to_list() == [1, 2, 3]

    def test_convert_with_column_cast(self):
        """Test conversion with column type casting."""
        data = [1, 2, 3]
        df = DataframeFromCollection.convert(data)

        # Apply column transformation with casting
        config = SchemaConfig(
            columns={"value": {"cast": "str"}}
        )
        df_transformed = config.apply(df)

        assert df_transformed["value"].dtype == pl.String
        assert df_transformed["value"].to_list() == ["1", "2", "3"]


# ============================================================================
# Round-Trip Tests
# ============================================================================

class TestCollectionRoundTrip:
    """Test round-trip conversions: collection → DataFrame → collection."""

    def test_roundtrip_list_via_to_list(self):
        """Test round-trip: list → DataFrame → list."""
        original_data = [1, 2, 3, 4, 5]

        # Convert to DataFrame
        df = DataframeFromCollection.convert(original_data)

        # Convert back to list
        strategy = DataFrameCastFactory.get_strategy(df)
        result_dict = strategy.to_dictionary_of_lists(df)

        # Validate round-trip
        assert result_dict == {"value": [1, 2, 3, 4, 5]}

    def test_roundtrip_set_via_to_list(self):
        """Test round-trip: set → DataFrame → list (order not preserved)."""
        original_data = {1, 2, 3}

        # Convert to DataFrame
        df = DataframeFromCollection.convert(original_data)

        # Convert back to list
        strategy = DataFrameCastFactory.get_strategy(df)
        result_dict = strategy.to_dictionary_of_lists(df)

        # Validate round-trip (check contents, not order)
        assert set(result_dict["value"]) == {1, 2, 3}

    def test_roundtrip_list_of_strings(self):
        """Test round-trip: list of strings → DataFrame → list."""
        original_data = ["apple", "banana", "cherry"]

        # Convert to DataFrame
        df = DataframeFromCollection.convert(original_data)

        # Convert back to list
        strategy = DataFrameCastFactory.get_strategy(df)
        result_dict = strategy.to_dictionary_of_lists(df)

        # Validate round-trip
        assert result_dict == {"value": ["apple", "banana", "cherry"]}

    def test_roundtrip_with_custom_column_name(self):
        """Test round-trip with custom column name."""
        original_data = [10, 20, 30]

        # Convert to DataFrame with custom column name
        df = DataframeFromCollection.convert(original_data, column_name="numbers")

        # Convert back to list
        strategy = DataFrameCastFactory.get_strategy(df)
        result_dict = strategy.to_dictionary_of_lists(df)

        # Validate round-trip
        assert result_dict == {"numbers": [10, 20, 30]}

    def test_roundtrip_empty_collection(self):
        """Test round-trip with empty collection."""
        original_data = []

        # Convert to DataFrame
        df = DataframeFromCollection.convert(original_data)

        # Convert back to list
        strategy = DataFrameCastFactory.get_strategy(df)
        result_dict = strategy.to_dictionary_of_lists(df)

        # Validate round-trip
        assert result_dict == {"value": []}
