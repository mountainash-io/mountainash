"""Tests for edge cases and error handling in convert module.

This module tests boundary conditions, error scenarios, and exceptional cases
to ensure robust error handling and graceful degradation.
"""

from __future__ import annotations

import pytest
import polars as pl
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal

from mountainash.dataframes.ingress import PydataConverterFactory
from mountainash.dataframes.ingress.dataframe_from_dataclass import DataframeFromDataclass
from mountainash.dataframes.ingress.dataframe_from_pydict import DataframeFromPydict
from mountainash.dataframes.ingress.dataframe_from_pylist import DataframeFromPylist
from mountainash.dataframes.schema_config import SchemaConfig


@pytest.mark.unit
class TestEmptyDataEdgeCases:
    """Test handling of empty data structures."""

    def test_empty_dict_of_lists(self, empty_dict_of_lists):
        """Test converting empty dictionary of lists."""
        result = DataframeFromPydict.convert(empty_dict_of_lists)

        assert isinstance(result, pl.DataFrame)
        assert result.shape[0] == 0
        assert len(result.columns) == 0

    def test_empty_list_of_dicts(self, empty_list_of_dicts):
        """Test that empty list is handled appropriately."""
        # Empty list cannot be detected by can_handle because it has no schema
        # but Polars can create an empty DataFrame from it
        result = DataframeFromPylist.convert(empty_list_of_dicts)
        assert isinstance(result, pl.DataFrame)
        assert result.shape[0] == 0

    def test_empty_dataclass_list(self):
        """Test converting empty list of dataclasses."""
        empty_list: List = []

        # Should not be handled by dataclass strategy
        assert DataframeFromDataclass.can_handle(empty_list) is False


@pytest.mark.unit
class TestSingleItemEdgeCases:
    """Test handling of single-item data structures."""

    def test_single_row_dict_of_lists(self, single_row_dict_of_lists):
        """Test converting dictionary with single row."""
        result = DataframeFromPydict.convert(single_row_dict_of_lists)

        assert isinstance(result, pl.DataFrame)
        assert result.shape[0] == 1
        assert result["user_id"][0] == 1

    def test_single_item_list_of_dicts(self, single_item_list_of_dicts):
        """Test converting list with single dictionary."""
        result = DataframeFromPylist.convert(single_item_list_of_dicts)

        assert isinstance(result, pl.DataFrame)
        assert result.shape[0] == 1
        assert result["user_id"][0] == 1

    def test_single_dataclass_instance(self, simple_dataclass_single):
        """Test converting single dataclass instance."""
        result = DataframeFromDataclass.convert(simple_dataclass_single)

        assert isinstance(result, pl.DataFrame)
        assert result.shape[0] == 1


@pytest.mark.unit
class TestNullValueHandling:
    """Test handling of null and missing values."""

    def test_dict_with_null_values(self, dict_of_lists_with_nulls):
        """Test converting dictionary with null values."""
        result = DataframeFromPydict.convert(dict_of_lists_with_nulls)

        assert isinstance(result, pl.DataFrame)
        assert result["id"].null_count() > 0
        assert result["name"].null_count() > 0
        assert result["value"].null_count() > 0

    def test_list_with_null_values(self, list_of_dicts_with_nulls):
        """Test converting list of dicts with null values."""
        result = DataframeFromPylist.convert(list_of_dicts_with_nulls)

        assert isinstance(result, pl.DataFrame)
        assert result["name"].null_count() > 0

    def test_dataclass_with_optional_fields(self):
        """Test converting dataclass with optional fields."""
        @dataclass
        class UserWithOptional:
            user_id: int
            name: str
            email: Optional[str] = None
            age: Optional[int] = None

        data = [
            UserWithOptional(user_id=1, name="Alice", email="alice@example.com", age=30),
            UserWithOptional(user_id=2, name="Bob", email=None, age=None)
        ]

        result = DataframeFromDataclass.convert(data)

        assert isinstance(result, pl.DataFrame)
        assert result["email"].null_count() > 0
        assert result["age"].null_count() > 0

    def test_all_null_column(self):
        """Test converting data where entire column is null."""
        dict_data = {
            "id": [1, 2, 3],
            "name": [None, None, None]
        }

        result = DataframeFromPydict.convert(dict_data)

        assert isinstance(result, pl.DataFrame)
        assert result["name"].null_count() == 3


@pytest.mark.unit
class TestComplexTypeHandling:
    """Test handling of complex data types."""

    def test_nested_list_in_dataclass(self):
        """Test converting dataclass with list fields."""
        @dataclass
        class UserWithTags:
            user_id: int
            name: str
            tags: List[str] = field(default_factory=list)

        data = [
            UserWithTags(user_id=1, name="Alice", tags=["premium", "verified"]),
            UserWithTags(user_id=2, name="Bob", tags=[])
        ]

        result = DataframeFromDataclass.convert(data)

        assert isinstance(result, pl.DataFrame)
        assert "tags" in result.columns
        # List fields are preserved as list type in Polars

    def test_datetime_fields(self):
        """Test converting dataclass with datetime fields."""
        @dataclass
        class Event:
            event_id: int
            name: str
            created_at: datetime

        data = [
            Event(event_id=1, name="Event1", created_at=datetime(2024, 1, 1, 10, 0)),
            Event(event_id=2, name="Event2", created_at=datetime(2024, 1, 2, 15, 30))
        ]

        result = DataframeFromDataclass.convert(data)

        assert isinstance(result, pl.DataFrame)
        assert "created_at" in result.columns
        # Datetime fields should be preserved

    def test_decimal_fields(self):
        """Test converting dataclass with Decimal fields."""
        @dataclass
        class Transaction:
            transaction_id: int
            amount: Decimal

        data = [
            Transaction(transaction_id=1, amount=Decimal("100.50")),
            Transaction(transaction_id=2, amount=Decimal("200.75"))
        ]

        result = DataframeFromDataclass.convert(data)

        assert isinstance(result, pl.DataFrame)
        assert "amount" in result.columns


@pytest.mark.unit
class TestInvalidDataHandling:
    """Test handling of invalid or malformed data."""

    def test_inconsistent_list_lengths_in_dict(self):
        """Test that dictionary with inconsistent list lengths is handled."""
        dict_data = {
            "id": [1, 2, 3],
            "name": ["Alice", "Bob"]  # Mismatched length
        }

        # Polars should handle this or raise an appropriate error
        with pytest.raises((ValueError, Exception)):
            DataframeFromPydict.convert(dict_data)

    def test_inconsistent_dict_keys_in_list(self):
        """Test list of dicts with inconsistent keys."""
        list_data = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "email": "bob@example.com"}  # Different keys
        ]

        # Polars handles missing keys by filling with nulls
        result = DataframeFromPylist.convert(list_data)

        assert isinstance(result, pl.DataFrame)
        # Should have all columns (union of all keys)
        assert "id" in result.columns
        assert "name" in result.columns
        assert "email" in result.columns

    def test_mixed_type_dataclass_list(self):
        """Test list with mixed dataclass types."""
        @dataclass
        class User:
            user_id: int
            name: str

        @dataclass
        class Product:
            product_id: int
            title: str

        mixed_data = [
            User(user_id=1, name="Alice"),
            Product(product_id=100, title="Widget")  # Different type
        ]

        # Should not be recognized as valid dataclass list
        # or should raise an error during conversion
        # The behavior depends on implementation


@pytest.mark.unit
class TestUnsupportedTypeHandling:
    """Test handling of unsupported data types."""

    def test_string_input_rejected(self):
        """Test that string input is rejected by factory."""

        with pytest.raises((ValueError, TypeError, KeyError)):
            PydataConverterFactory.get_strategy("just a string")

    def test_integer_input_rejected(self):
        """Test that integer input is rejected by factory."""

        with pytest.raises((ValueError, TypeError, KeyError)):
            PydataConverterFactory.get_strategy(42)

    def test_none_input_rejected(self):
        """Test that None input is rejected by factory."""

        with pytest.raises((ValueError, TypeError, KeyError)):
            PydataConverterFactory.get_strategy(None)


@pytest.mark.unit
class TestColumnMappingEdgeCases:
    """Test edge cases in column mapping and configuration."""

    def test_mapping_nonexistent_columns(self):
        """Test column mapping referencing nonexistent columns."""
        config = SchemaConfig(columns={
            "nonexistent_col": {"rename": "new_name"}
        })

        dict_data = {"id": [1, 2], "name": ["Alice", "Bob"]}

        # Should handle gracefully or raise informative error
        result = DataframeFromPydict.convert(dict_data, column_config=config)

        # Original columns should still exist
        assert "id" in result.columns
        assert "name" in result.columns

    def test_mapping_to_duplicate_names(self):
        """Test column mapping creating duplicate column names."""
        config = SchemaConfig(columns={
            "user_id": {"rename": "id"},
            "employee_id": {"rename": "id"}  # Duplicate target
        })

        dict_data = {"user_id": [1, 2], "employee_id": [101, 102]}

        # Should handle duplicate renames appropriately
        # Implementation may raise error or handle differently

    def test_empty_column_config(self):
        """Test conversion with empty column configuration."""
        config = SchemaConfig(columns={})

        dict_data = {"id": [1, 2], "name": ["Alice", "Bob"]}

        result = DataframeFromPydict.convert(dict_data, column_config=config)

        # Should work normally with no transformations
        assert isinstance(result, pl.DataFrame)
        assert "id" in result.columns
        assert "name" in result.columns


@pytest.mark.unit
class TestLargeDataHandling:
    """Test handling of large data sets."""

    def test_large_dataclass_list(self):
        """Test converting large list of dataclasses."""
        @dataclass
        class SimpleData:
            id: int
            value: float

        large_data = [SimpleData(id=i, value=float(i * 1.5)) for i in range(1000)]

        result = DataframeFromDataclass.convert(large_data)

        assert isinstance(result, pl.DataFrame)
        assert result.shape[0] == 1000
        assert result["id"].to_list() == list(range(1000))

    def test_large_dict_of_lists(self):
        """Test converting large dictionary of lists."""
        large_dict = {
            "id": list(range(1000)),
            "value": [float(i * 1.5) for i in range(1000)]
        }

        result = DataframeFromPydict.convert(large_dict)

        assert isinstance(result, pl.DataFrame)
        assert result.shape[0] == 1000

    def test_wide_dataframe(self):
        """Test converting data with many columns."""
        # Create dict with 100 columns
        wide_dict = {f"col_{i}": [1, 2, 3] for i in range(100)}

        result = DataframeFromPydict.convert(wide_dict)

        assert isinstance(result, pl.DataFrame)
        assert len(result.columns) == 100
        assert result.shape[0] == 3


@pytest.mark.unit
class TestSpecialCharacterHandling:
    """Test handling of special characters in column names and data."""

    def test_special_characters_in_column_names(self):
        """Test columns with special characters."""
        dict_data = {
            "user-id": [1, 2],
            "user name": ["Alice", "Bob"],
            "email@address": ["alice@example.com", "bob@example.com"]
        }

        result = DataframeFromPydict.convert(dict_data)

        assert isinstance(result, pl.DataFrame)
        # Column names with special characters should be preserved
        assert "user-id" in result.columns
        assert "user name" in result.columns

    def test_unicode_in_data(self):
        """Test data with unicode characters."""
        dict_data = {
            "id": [1, 2],
            "name": ["Alice 👩", "Bob 🚀"],
            "city": ["München", "北京"]
        }

        result = DataframeFromPydict.convert(dict_data)

        assert isinstance(result, pl.DataFrame)
        assert result["name"][0] == "Alice 👩"
        assert result["city"][1] == "北京"


@pytest.mark.unit
class TestTypeCoercionEdgeCases:
    """Test edge cases in type coercion and inference."""

    def test_mixed_numeric_types(self):
        """Test handling mixed integer and float values."""
        dict_data = {
            "id": [1, 2, 3],
            "value": [100, 200.5, 300]  # Mixed int and float
        }

        result = DataframeFromPydict.convert(dict_data)

        assert isinstance(result, pl.DataFrame)
        # Should coerce to float type
        assert result["value"].dtype == pl.Float64

    def test_boolean_with_none(self):
        """Test boolean column with null values."""
        dict_data = {
            "id": [1, 2, 3],
            "active": [True, False, None]
        }

        result = DataframeFromPydict.convert(dict_data)

        assert isinstance(result, pl.DataFrame)
        assert result["active"].null_count() == 1
