"""
Tests for individual backend conversion strategies.

This module tests each conversion strategy in isolation, ensuring correct
behavior for each Python data structure type.
"""

from __future__ import annotations

import pytest
import polars as pl
from dataclasses import dataclass
from typing import List

from mountainash.dataframes.ingress.dataframe_from_dataclass import DataframeFromDataclass
from mountainash.dataframes.ingress.dataframe_from_pydantic import DataframeFromPydantic
from mountainash.dataframes.ingress.dataframe_from_pydict import DataframeFromPydict
from mountainash.dataframes.ingress.dataframe_from_pylist import DataframeFromPylist
from mountainash.dataframes.schema_config import SchemaConfig


@pytest.mark.unit
class TestDataclassStrategy:
    """Test DataframeFromDataclass strategy."""

    def test_can_handle_single_dataclass(self, simple_dataclass_single):
        """Test can_handle identifies single dataclass instance."""
        assert DataframeFromDataclass.can_handle(simple_dataclass_single) is True

    def test_can_handle_list_of_dataclasses(self, simple_dataclass_list):
        """Test can_handle identifies list of dataclasses."""
        assert DataframeFromDataclass.can_handle(simple_dataclass_list) is True

    def test_can_handle_rejects_non_dataclass(self, dict_of_lists_simple):
        """Test can_handle rejects non-dataclass data."""
        assert DataframeFromDataclass.can_handle(dict_of_lists_simple) is False

    def test_can_handle_rejects_empty_list(self):
        """Test can_handle rejects empty list."""
        assert DataframeFromDataclass.can_handle([]) is False

    def test_convert_single_dataclass(self, simple_dataclass_single):
        """Test converting single dataclass instance."""
        result = DataframeFromDataclass.convert(simple_dataclass_single)

        assert isinstance(result, pl.DataFrame)
        assert result.shape[0] == 1
        assert "user_id" in result.columns
        assert "name" in result.columns
        assert "email" in result.columns
        assert result["user_id"][0] == 1
        assert result["name"][0] == "Alice"

    def test_convert_list_of_dataclasses(self, simple_dataclass_list):
        """Test converting list of dataclass instances."""
        result = DataframeFromDataclass.convert(simple_dataclass_list)

        assert isinstance(result, pl.DataFrame)
        assert result.shape[0] == 3
        assert result["user_id"].to_list() == [1, 2, 3]
        assert result["name"].to_list() == ["Alice", "Bob", "Charlie"]

    def test_convert_complex_dataclass(self, complex_dataclass_list):
        """Test converting complex dataclass with various field types."""
        result = DataframeFromDataclass.convert(complex_dataclass_list)

        assert isinstance(result, pl.DataFrame)
        assert result.shape[0] == 2
        assert "user_id" in result.columns
        assert "balance" in result.columns
        assert "created_at" in result.columns
        assert "tags" in result.columns

    def test_convert_with_column_config(self, simple_dataclass_list):
        """Test converting with column configuration."""
        config = SchemaConfig(columns={
            "user_id": {"rename": "id"},
            "name": {"rename": "full_name"}
        })

        result = DataframeFromDataclass.convert(simple_dataclass_list, column_config=config)

        assert "id" in result.columns
        assert "full_name" in result.columns
        assert result["id"].to_list() == [1, 2, 3]


@pytest.mark.unit
class TestPydictStrategy:
    """Test DataframeFromPydict strategy."""

    def test_can_handle_dict_of_lists(self, dict_of_lists_simple):
        """Test can_handle identifies dictionary of lists."""
        assert DataframeFromPydict.can_handle(dict_of_lists_simple) is True

    def test_can_handle_rejects_list_of_dicts(self, list_of_dicts_simple):
        """Test can_handle rejects list of dictionaries."""
        assert DataframeFromPydict.can_handle(list_of_dicts_simple) is False

    def test_can_handle_rejects_dataclass(self, simple_dataclass_single):
        """Test can_handle rejects dataclass instances."""
        assert DataframeFromPydict.can_handle(simple_dataclass_single) is False

    def test_convert_simple_dict(self, dict_of_lists_simple):
        """Test converting simple dictionary of lists."""
        result = DataframeFromPydict.convert(dict_of_lists_simple)

        assert isinstance(result, pl.DataFrame)
        assert result.shape[0] == 3
        assert set(result.columns) == {"user_id", "name", "email"}
        assert result["user_id"].to_list() == [1, 2, 3]

    def test_convert_complex_dict(self, dict_of_lists_complex):
        """Test converting complex dictionary with various types."""
        result = DataframeFromPydict.convert(dict_of_lists_complex)

        assert isinstance(result, pl.DataFrame)
        assert result.shape[0] == 5
        assert "id" in result.columns
        assert "name" in result.columns
        assert "category" in result.columns
        assert "value" in result.columns
        assert "active" in result.columns

    def test_convert_with_nulls(self, dict_of_lists_with_nulls):
        """Test converting dictionary with null values."""
        result = DataframeFromPydict.convert(dict_of_lists_with_nulls)

        assert isinstance(result, pl.DataFrame)
        assert result.shape[0] == 4
        # Check null handling
        assert result["id"].null_count() > 0
        assert result["name"].null_count() > 0

    def test_convert_empty_dict(self, empty_dict_of_lists):
        """Test converting empty dictionary."""
        result = DataframeFromPydict.convert(empty_dict_of_lists)

        assert isinstance(result, pl.DataFrame)
        assert result.shape[0] == 0
        assert len(result.columns) == 0

    def test_convert_single_row(self, single_row_dict_of_lists):
        """Test converting dictionary with single row."""
        result = DataframeFromPydict.convert(single_row_dict_of_lists)

        assert isinstance(result, pl.DataFrame)
        assert result.shape[0] == 1
        assert result["user_id"][0] == 1

    def test_convert_with_column_config(self, dict_of_lists_simple):
        """Test converting with column configuration."""
        config = SchemaConfig(columns={
            "user_id": {"rename": "id"},
            "email": {"rename": "email_address"}
        })

        result = DataframeFromPydict.convert(dict_of_lists_simple, column_config=config)

        assert "id" in result.columns
        assert "email_address" in result.columns
        assert result["id"].to_list() == [1, 2, 3]


@pytest.mark.unit
class TestPylistStrategy:
    """Test DataframeFromPylist strategy."""

    def test_can_handle_list_of_dicts(self, list_of_dicts_simple):
        """Test can_handle identifies list of dictionaries."""
        assert DataframeFromPylist.can_handle(list_of_dicts_simple) is True

    def test_can_handle_rejects_dict_of_lists(self, dict_of_lists_simple):
        """Test can_handle rejects dictionary of lists."""
        assert DataframeFromPylist.can_handle(dict_of_lists_simple) is False

    def test_can_handle_rejects_empty_list(self):
        """Test can_handle rejects empty list."""
        assert DataframeFromPylist.can_handle([]) is False

    def test_can_handle_rejects_dataclass(self, simple_dataclass_single):
        """Test can_handle rejects dataclass instances."""
        assert DataframeFromPylist.can_handle(simple_dataclass_single) is False

    def test_convert_simple_list(self, list_of_dicts_simple):
        """Test converting simple list of dictionaries."""
        result = DataframeFromPylist.convert(list_of_dicts_simple)

        assert isinstance(result, pl.DataFrame)
        assert result.shape[0] == 3
        assert set(result.columns) == {"user_id", "name", "email"}
        assert result["user_id"].to_list() == [1, 2, 3]

    def test_convert_complex_list(self, list_of_dicts_complex):
        """Test converting complex list with various types."""
        result = DataframeFromPylist.convert(list_of_dicts_complex)

        assert isinstance(result, pl.DataFrame)
        assert result.shape[0] == 5
        assert "id" in result.columns
        assert "name" in result.columns
        assert "category" in result.columns
        assert "value" in result.columns
        assert "active" in result.columns

    def test_convert_with_nulls(self, list_of_dicts_with_nulls):
        """Test converting list with null values."""
        result = DataframeFromPylist.convert(list_of_dicts_with_nulls)

        assert isinstance(result, pl.DataFrame)
        assert result.shape[0] == 3
        # Check null handling
        assert result["name"].null_count() > 0

    def test_convert_single_item(self, single_item_list_of_dicts):
        """Test converting list with single dictionary."""
        result = DataframeFromPylist.convert(single_item_list_of_dicts)

        assert isinstance(result, pl.DataFrame)
        assert result.shape[0] == 1
        assert result["user_id"][0] == 1

    def test_convert_with_column_config(self, list_of_dicts_simple):
        """Test converting with column configuration."""
        config = SchemaConfig(columns={
            "user_id": {"rename": "id"},
            "name": {"rename": "full_name"}
        })

        result = DataframeFromPylist.convert(list_of_dicts_simple, column_config=config)

        assert "id" in result.columns
        assert "full_name" in result.columns
        assert result["id"].to_list() == [1, 2, 3]


@pytest.mark.unit
@pytest.mark.skipif(
    not hasattr(pytest, "PYDANTIC_AVAILABLE"),
    reason="Pydantic not available"
)
class TestPydanticStrategy:
    """Test DataframeFromPydantic strategy (when Pydantic is available)."""

    def test_can_handle_single_pydantic(self, simple_pydantic_single):
        """Test can_handle identifies single Pydantic model."""
        if simple_pydantic_single is None:
            pytest.skip("Pydantic not available")
        assert DataframeFromPydantic.can_handle(simple_pydantic_single) is True

    def test_can_handle_list_of_pydantic(self, simple_pydantic_list):
        """Test can_handle identifies list of Pydantic models."""
        if simple_pydantic_list is None:
            pytest.skip("Pydantic not available")
        assert DataframeFromPydantic.can_handle(simple_pydantic_list) is True

    def test_can_handle_rejects_non_pydantic(self, dict_of_lists_simple):
        """Test can_handle rejects non-Pydantic data."""
        assert DataframeFromPydantic.can_handle(dict_of_lists_simple) is False

    def test_convert_single_pydantic(self, simple_pydantic_single):
        """Test converting single Pydantic model."""
        if simple_pydantic_single is None:
            pytest.skip("Pydantic not available")

        result = DataframeFromPydantic.convert(simple_pydantic_single)

        assert isinstance(result, pl.DataFrame)
        assert result.shape[0] == 1
        assert "user_id" in result.columns
        assert "name" in result.columns
        assert "email" in result.columns

    def test_convert_list_of_pydantic(self, simple_pydantic_list):
        """Test converting list of Pydantic models."""
        if simple_pydantic_list is None:
            pytest.skip("Pydantic not available")

        result = DataframeFromPydantic.convert(simple_pydantic_list)

        assert isinstance(result, pl.DataFrame)
        assert result.shape[0] == 3
        assert result["user_id"].to_list() == [1, 2, 3]


@pytest.mark.unit
class TestStrategyColumnMapping:
    """Test column mapping functionality across strategies."""

    def test_dataclass_preserves_all_fields(self, complex_dataclass_list):
        """Test that dataclass conversion preserves all fields."""
        result = DataframeFromDataclass.convert(complex_dataclass_list)

        expected_fields = {"user_id", "name", "email", "balance", "created_at", "birth_date", "tags", "is_verified"}
        assert expected_fields.issubset(set(result.columns))

    def test_pydict_preserves_all_columns(self, dict_of_lists_complex):
        """Test that dictionary conversion preserves all columns."""
        result = DataframeFromPydict.convert(dict_of_lists_complex)

        expected_columns = {"id", "name", "category", "value", "active"}
        assert set(result.columns) == expected_columns

    def test_pylist_preserves_all_keys(self, list_of_dicts_complex):
        """Test that list conversion preserves all dictionary keys."""
        result = DataframeFromPylist.convert(list_of_dicts_complex)

        expected_columns = {"id", "name", "category", "value", "active"}
        assert set(result.columns) == expected_columns


@pytest.mark.unit
class TestStrategyTypePreservation:
    """Test that strategies preserve data types correctly."""

    def test_dataclass_preserves_types(self, employee_dataclass_list):
        """Test that dataclass field types are preserved."""
        result = DataframeFromDataclass.convert(employee_dataclass_list)

        # Check integer type
        assert result["employee_id"].dtype in [pl.Int64, pl.Int32]
        # Check float type
        assert result["salary"].dtype == pl.Float64
        # Check boolean type
        assert result["is_active"].dtype == pl.Boolean

    def test_pydict_handles_mixed_types(self, dict_of_lists_complex):
        """Test that dictionary handles mixed data types."""
        result = DataframeFromPydict.convert(dict_of_lists_complex)

        # Check that different types are handled
        assert result["id"].dtype in [pl.Int64, pl.Int32]
        assert result["name"].dtype == pl.String
        assert result["value"].dtype == pl.Float64
        assert result["active"].dtype == pl.Boolean

    def test_pylist_handles_mixed_types(self, list_of_dicts_complex):
        """Test that list handles mixed data types."""
        result = DataframeFromPylist.convert(list_of_dicts_complex)

        # Check that different types are handled
        assert result["id"].dtype in [pl.Int64, pl.Int32]
        assert result["name"].dtype == pl.String
        assert result["value"].dtype == pl.Float64
        assert result["active"].dtype == pl.Boolean
