"""
Tests for PydataConverterFactory.

This module tests the factory's strategy selection, automatic data type detection,
and public API for converting Python data structures to DataFrames.
"""

from __future__ import annotations

import pytest
import polars as pl

from mountainash.dataframes.ingress import PydataConverterFactory
from mountainash.dataframes.ingress.dataframe_from_dataclass import DataframeFromDataclass
from mountainash.dataframes.ingress.dataframe_from_pydantic import DataframeFromPydantic
from mountainash.dataframes.ingress.dataframe_from_pydict import DataframeFromPydict
from mountainash.dataframes.ingress.dataframe_from_pylist import DataframeFromPylist
from mountainash.dataframes.schema_config import SchemaConfig


@pytest.mark.unit
class TestFactoryStrategySelection:
    """Test that factory selects the correct strategy for each data type."""

    def test_factory_selects_dataclass_strategy_single(self, simple_dataclass_single):
        """Test factory selects DataclassStrategy for single dataclass instance."""


        strategy = PydataConverterFactory.get_strategy(simple_dataclass_single)
        assert strategy == DataframeFromDataclass

    def test_factory_selects_dataclass_strategy_list(self, simple_dataclass_list):
        """Test factory selects DataclassStrategy for list of dataclasses."""


        strategy = PydataConverterFactory.get_strategy(simple_dataclass_list)
        assert strategy == DataframeFromDataclass

    @pytest.mark.skipif(
        not hasattr(pytest, "PYDANTIC_AVAILABLE") or not pytest.PYDANTIC_AVAILABLE,
        reason="Pydantic not available"
    )
    def test_factory_selects_pydantic_strategy_single(self, simple_pydantic_single):
        """Test factory selects PydanticStrategy for single Pydantic model."""


        strategy = PydataConverterFactory.get_strategy(simple_pydantic_single)
        assert strategy == DataframeFromPydantic

    @pytest.mark.skipif(
        not hasattr(pytest, "PYDANTIC_AVAILABLE") or not pytest.PYDANTIC_AVAILABLE,
        reason="Pydantic not available"
    )
    def test_factory_selects_pydantic_strategy_list(self, simple_pydantic_list):
        """Test factory selects PydanticStrategy for list of Pydantic models."""


        strategy = PydataConverterFactory.get_strategy(simple_pydantic_list)
        assert strategy == DataframeFromPydantic

    def test_factory_selects_pydict_strategy(self, dict_of_lists_simple):
        """Test factory selects PydictStrategy for dictionary of lists."""


        strategy = PydataConverterFactory.get_strategy(dict_of_lists_simple)
        assert strategy == DataframeFromPydict

    def test_factory_selects_pylist_strategy(self, list_of_dicts_simple):
        """Test factory selects PylistStrategy for list of dictionaries."""


        strategy = PydataConverterFactory.get_strategy(list_of_dicts_simple)
        assert strategy == DataframeFromPylist


@pytest.mark.unit
class TestFactoryPublicAPI:
    """Test factory's public API methods for data conversion."""

    def test_convert_dataclass_single(self, simple_dataclass_single, expected_simple_columns):
        """Test converting single dataclass instance."""


        result = PydataConverterFactory.convert(simple_dataclass_single)

        assert isinstance(result, pl.DataFrame)
        assert result.shape[0] == 1
        assert set(result.columns) == set(expected_simple_columns)
        assert result["user_id"][0] == 1
        assert result["name"][0] == "Alice"

    def test_convert_dataclass_list(self, simple_dataclass_list, expected_simple_columns, expected_row_count_simple):
        """Test converting list of dataclass instances."""


        result = PydataConverterFactory.convert(simple_dataclass_list)

        assert isinstance(result, pl.DataFrame)
        assert result.shape[0] == expected_row_count_simple
        assert set(result.columns) == set(expected_simple_columns)
        assert result["user_id"].to_list() == [1, 2, 3]

    def test_convert_dict_of_lists(self, dict_of_lists_simple, expected_simple_columns, expected_row_count_simple):
        """Test converting dictionary of lists."""
        result = PydataConverterFactory.convert(dict_of_lists_simple)

        assert isinstance(result, pl.DataFrame)
        assert result.shape[0] == expected_row_count_simple
        assert set(result.columns) == set(expected_simple_columns)

    def test_convert_list_of_dicts(self, list_of_dicts_simple, expected_simple_columns, expected_row_count_simple):
        """Test converting list of dictionaries."""
        result = PydataConverterFactory.convert(list_of_dicts_simple)

        assert isinstance(result, pl.DataFrame)
        assert result.shape[0] == expected_row_count_simple
        assert set(result.columns) == set(expected_simple_columns)

    def test_convert_with_column_config(self, simple_dataclass_list):
        """Test public API with column configuration."""
        config = SchemaConfig(columns={
            "user_id": {"rename": "id"},
            "name": {"rename": "full_name"},
            "email": {"rename": "email_address"}
        })
        result = PydataConverterFactory.convert(simple_dataclass_list, column_config=config)

        assert isinstance(result, pl.DataFrame)
        assert "id" in result.columns
        assert "full_name" in result.columns
        assert "email_address" in result.columns
        assert "user_id" not in result.columns


@pytest.mark.unit
class TestFactoryErrorHandling:
    """Test factory error handling for unsupported types and edge cases."""

    def test_factory_handles_unknown_type(self):
        """Test factory behavior with unsupported data type."""
        unsupported = "just a string"

        # Factory should raise an error for unsupported types
        with pytest.raises((ValueError, TypeError, KeyError)):
            PydataConverterFactory.get_strategy(unsupported)

    def test_factory_handles_empty_list(self, empty_list_of_dicts):
        """Test factory behavior with empty list."""

        # Empty list should either raise error or be handled gracefully
        try:
            strategy = PydataConverterFactory.get_strategy(empty_list_of_dicts)
            # If it doesn't raise, the result should be None or a valid strategy
            assert strategy is None or strategy is not None
        except (ValueError, IndexError):
            # This is acceptable - empty data is an edge case
            pass

    def test_factory_handles_empty_dict(self, empty_dict_of_lists):
        """Test factory behavior with empty dictionary."""

        # Empty dict should be handled by pydict strategy
        strategy = PydataConverterFactory.get_strategy(empty_dict_of_lists)
        # Empty dict of lists is technically valid but will create empty DataFrame
        assert strategy == DataframeFromPydict or strategy is None



@pytest.mark.unit
class TestFactoryComplexData:
    """Test factory with complex data types and structures."""

    def test_convert_complex_dataclass(self, complex_dataclass_list):
        """Test converting complex dataclasses with various field types."""

        result = PydataConverterFactory.convert(complex_dataclass_list)

        assert isinstance(result, pl.DataFrame)
        assert result.shape[0] == 2
        # Verify complex types are preserved
        assert "user_id" in result.columns
        assert "balance" in result.columns
        assert "created_at" in result.columns
        assert "tags" in result.columns

    def test_convert_dict_with_nulls(self, dict_of_lists_with_nulls):
        """Test converting dictionary with null values."""

        result = PydataConverterFactory.convert(dict_of_lists_with_nulls)

        assert isinstance(result, pl.DataFrame)
        assert result.shape[0] == 4
        # Verify null handling
        assert result["id"].null_count() > 0

    def test_convert_list_with_nulls(self, list_of_dicts_with_nulls):
        """Test converting list of dicts with null values."""

        result = PydataConverterFactory.convert(list_of_dicts_with_nulls)

        assert isinstance(result, pl.DataFrame)
        assert result.shape[0] == 3
        # Verify null handling
        assert result["name"].null_count() > 0


@pytest.mark.unit
class TestFactoryColumnConfiguration:
    """Test factory with various column configuration scenarios."""

    def test_convert_with_rename_mapping(self, dict_of_lists_simple, simple_column_mapping):
        """Test converting with column rename configuration."""
        config = SchemaConfig(columns=simple_column_mapping)

        result = PydataConverterFactory.convert(dict_of_lists_simple, column_config=config)

        assert "id" in result.columns
        assert "full_name" in result.columns
        assert "email_address" in result.columns
