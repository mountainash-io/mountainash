"""Tests for cross-backend consistency in convert module.

This module validates that different Python data structures (dataclass, dict, list)
produce equivalent DataFrames when containing the same data, ensuring consistent
behavior regardless of the input format.
"""

import pytest
from pytest_check import check
import polars as pl
from dataclasses import dataclass

from mountainash.dataframes.ingress import PydataConverterFactory
from mountainash.dataframes.ingress.dataframe_from_dataclass import DataframeFromDataclass
from mountainash.dataframes.ingress.dataframe_from_pydict import DataframeFromPydict
from mountainash.dataframes.ingress.dataframe_from_pylist import DataframeFromPylist


@dataclass
class CrossBackendUser:
    """User dataclass for cross-backend testing."""
    user_id: int
    name: str
    email: str


@pytest.mark.unit
class TestCrossBackendEquivalence:
    """Test that different input formats produce equivalent DataFrames."""

    def test_dataclass_vs_dict_vs_list_equivalence(self):
        """Test that dataclass, dict, and list produce equivalent DataFrames."""
        # Create equivalent data in three formats
        dataclass_data = [
            CrossBackendUser(user_id=1, name="Alice", email="alice@example.com"),
            CrossBackendUser(user_id=2, name="Bob", email="bob@example.com"),
            CrossBackendUser(user_id=3, name="Charlie", email="charlie@example.com")
        ]

        dict_data = {
            "user_id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "email": ["alice@example.com", "bob@example.com", "charlie@example.com"]
        }

        list_data = [
            {"user_id": 1, "name": "Alice", "email": "alice@example.com"},
            {"user_id": 2, "name": "Bob", "email": "bob@example.com"},
            {"user_id": 3, "name": "Charlie", "email": "charlie@example.com"}
        ]

        # Convert all three
        df_from_dataclass = DataframeFromDataclass.convert(dataclass_data)
        df_from_dict = DataframeFromPydict.convert(dict_data)
        df_from_list = DataframeFromPylist.convert(list_data)

        # All should have same shape
        check.equal(df_from_dataclass.shape, df_from_dict.shape)
        check.equal(df_from_dataclass.shape, df_from_list.shape)

        # All should have same columns
        check.equal(set(df_from_dataclass.columns), set(df_from_dict.columns))
        check.equal(set(df_from_dataclass.columns), set(df_from_list.columns))

        # All should have same data
        check.equal(df_from_dataclass["user_id"].to_list(), [1, 2, 3])
        check.equal(df_from_dict["user_id"].to_list(), [1, 2, 3])
        check.equal(df_from_list["user_id"].to_list(), [1, 2, 3])


@pytest.mark.unit
class TestCrossBackendRowCount:
    """Test that row count is consistent across input formats."""

    def test_row_count_consistency(self, simple_dataclass_list, dict_of_lists_simple, list_of_dicts_simple):
        """Test that all formats produce DataFrames with correct row count."""
        df_from_dataclass = DataframeFromDataclass.convert(simple_dataclass_list)
        df_from_dict = DataframeFromPydict.convert(dict_of_lists_simple)
        df_from_list = DataframeFromPylist.convert(list_of_dicts_simple)

        # All should have 3 rows
        check.equal(df_from_dataclass.shape[0], 3)
        check.equal(df_from_dict.shape[0], 3)
        check.equal(df_from_list.shape[0], 3)

    def test_single_row_consistency(self):
        """Test single-row data produces consistent results."""
        dataclass_single = [CrossBackendUser(user_id=1, name="Alice", email="alice@example.com")]
        dict_single = {"user_id": [1], "name": ["Alice"], "email": ["alice@example.com"]}
        list_single = [{"user_id": 1, "name": "Alice", "email": "alice@example.com"}]

        df_from_dataclass = DataframeFromDataclass.convert(dataclass_single)
        df_from_dict = DataframeFromPydict.convert(dict_single)
        df_from_list = DataframeFromPylist.convert(list_single)

        # All should have exactly 1 row
        check.equal(df_from_dataclass.shape[0], 1)
        check.equal(df_from_dict.shape[0], 1)
        check.equal(df_from_list.shape[0], 1)


@pytest.mark.unit
class TestCrossBackendColumnNames:
    """Test that column names are consistent across input formats."""

    def test_column_names_consistency(self, simple_dataclass_list, dict_of_lists_simple, list_of_dicts_simple):
        """Test that all formats produce DataFrames with same column names."""
        df_from_dataclass = DataframeFromDataclass.convert(simple_dataclass_list)
        df_from_dict = DataframeFromPydict.convert(dict_of_lists_simple)
        df_from_list = DataframeFromPylist.convert(list_of_dicts_simple)

        expected_columns = {"user_id", "name", "email"}

        check.equal(set(df_from_dataclass.columns), expected_columns)
        check.equal(set(df_from_dict.columns), expected_columns)
        check.equal(set(df_from_list.columns), expected_columns)


@pytest.mark.unit
class TestCrossBackendDataValues:
    """Test that data values are consistent across input formats."""

    def test_integer_values_consistency(self):
        """Test that integer values are preserved consistently."""
        dataclass_data = [
            CrossBackendUser(user_id=1, name="Alice", email="alice@example.com"),
            CrossBackendUser(user_id=2, name="Bob", email="bob@example.com")
        ]
        dict_data = {"user_id": [1, 2], "name": ["Alice", "Bob"], "email": ["alice@example.com", "bob@example.com"]}
        list_data = [
            {"user_id": 1, "name": "Alice", "email": "alice@example.com"},
            {"user_id": 2, "name": "Bob", "email": "bob@example.com"}
        ]

        df_from_dataclass = DataframeFromDataclass.convert(dataclass_data)
        df_from_dict = DataframeFromPydict.convert(dict_data)
        df_from_list = DataframeFromPylist.convert(list_data)

        check.equal(df_from_dataclass["user_id"].to_list(), [1, 2])
        check.equal(df_from_dict["user_id"].to_list(), [1, 2])
        check.equal(df_from_list["user_id"].to_list(), [1, 2])

    def test_string_values_consistency(self):
        """Test that string values are preserved consistently."""
        dataclass_data = [
            CrossBackendUser(user_id=1, name="Alice", email="alice@example.com"),
            CrossBackendUser(user_id=2, name="Bob", email="bob@example.com")
        ]
        dict_data = {"user_id": [1, 2], "name": ["Alice", "Bob"], "email": ["alice@example.com", "bob@example.com"]}
        list_data = [
            {"user_id": 1, "name": "Alice", "email": "alice@example.com"},
            {"user_id": 2, "name": "Bob", "email": "bob@example.com"}
        ]

        df_from_dataclass = DataframeFromDataclass.convert(dataclass_data)
        df_from_dict = DataframeFromPydict.convert(dict_data)
        df_from_list = DataframeFromPylist.convert(list_data)

        check.equal(df_from_dataclass["name"].to_list(), ["Alice", "Bob"])
        check.equal(df_from_dict["name"].to_list(), ["Alice", "Bob"])
        check.equal(df_from_list["name"].to_list(), ["Alice", "Bob"])


@pytest.mark.unit
class TestCrossBackendNullHandling:
    """Test that null values are handled consistently across input formats."""

    def test_null_handling_consistency(self):
        """Test that null values produce consistent results."""
        @dataclass
        class UserWithOptional:
            user_id: int
            name: str
            email: str | None

        dataclass_data = [
            UserWithOptional(user_id=1, name="Alice", email="alice@example.com"),
            UserWithOptional(user_id=2, name="Bob", email=None)
        ]

        dict_data = {
            "user_id": [1, 2],
            "name": ["Alice", "Bob"],
            "email": ["alice@example.com", None]
        }

        list_data = [
            {"user_id": 1, "name": "Alice", "email": "alice@example.com"},
            {"user_id": 2, "name": "Bob", "email": None}
        ]

        df_from_dataclass = DataframeFromDataclass.convert(dataclass_data)
        df_from_dict = DataframeFromPydict.convert(dict_data)
        df_from_list = DataframeFromPylist.convert(list_data)

        # All should have one null in email column
        check.equal(df_from_dataclass["email"].null_count(), 1)
        check.equal(df_from_dict["email"].null_count(), 1)
        check.equal(df_from_list["email"].null_count(), 1)


@pytest.mark.unit
class TestCrossBackendEmptyData:
    """Test that empty data is handled consistently across input formats."""

    def test_empty_data_consistency(self):
        """Test that empty data produces consistent empty DataFrames."""
        dict_empty = {}
        list_empty = []

        df_from_dict = DataframeFromPydict.convert(dict_empty)

        # Empty dict produces empty DataFrame
        check.equal(df_from_dict.shape[0], 0)
        check.equal(len(df_from_dict.columns), 0)

        # Empty list cannot be processed (no schema information)
        # This is expected behavior - list needs at least one item to determine columns


@pytest.mark.unit
class TestCrossBackendColumnMapping:
    """Test that column mapping produces consistent results across input formats."""

    def test_column_mapping_consistency(self):
        """Test that column mapping works consistently across formats."""
        from mountainash.dataframes.schema_config import SchemaConfig

        config = SchemaConfig(columns={
            "user_id": {"rename": "id"},
            "name": {"rename": "full_name"}
        })

        dataclass_data = [
            CrossBackendUser(user_id=1, name="Alice", email="alice@example.com"),
            CrossBackendUser(user_id=2, name="Bob", email="bob@example.com")
        ]
        dict_data = {"user_id": [1, 2], "name": ["Alice", "Bob"], "email": ["alice@example.com", "bob@example.com"]}
        list_data = [
            {"user_id": 1, "name": "Alice", "email": "alice@example.com"},
            {"user_id": 2, "name": "Bob", "email": "bob@example.com"}
        ]

        df_from_dataclass = DataframeFromDataclass.convert(dataclass_data, column_config=config)
        df_from_dict = DataframeFromPydict.convert(dict_data, column_config=config)
        df_from_list = DataframeFromPylist.convert(list_data, column_config=config)

        # All should have renamed columns
        check.is_in("id", df_from_dataclass.columns)
        check.is_in("id", df_from_dict.columns)
        check.is_in("id", df_from_list.columns)

        check.is_in("full_name", df_from_dataclass.columns)
        check.is_in("full_name", df_from_dict.columns)
        check.is_in("full_name", df_from_list.columns)


@pytest.mark.unit
class TestCrossBackendFactoryRouting:
    """Test that factory correctly routes to appropriate strategy."""

    def test_factory_routes_correctly(self):
        """Test that factory selects correct strategy for each data type."""
        factory = PydataConverterFactory()

        dataclass_data = [CrossBackendUser(user_id=1, name="Alice", email="alice@example.com")]
        dict_data = {"user_id": [1], "name": ["Alice"], "email": ["alice@example.com"]}
        list_data = [{"user_id": 1, "name": "Alice", "email": "alice@example.com"}]

        # Factory should select correct strategy for each
        dataclass_strategy = factory.get_strategy(dataclass_data)
        dict_strategy = factory.get_strategy(dict_data)
        list_strategy = factory.get_strategy(list_data)

        check.equal(dataclass_strategy, DataframeFromDataclass)
        check.equal(dict_strategy, DataframeFromPydict)
        check.equal(list_strategy, DataframeFromPylist)

    def test_factory_conversion_consistency(self):
        """Test that factory produces consistent results for different formats."""
        factory = PydataConverterFactory()

        dataclass_data = [
            CrossBackendUser(user_id=1, name="Alice", email="alice@example.com"),
            CrossBackendUser(user_id=2, name="Bob", email="bob@example.com")
        ]
        dict_data = {"user_id": [1, 2], "name": ["Alice", "Bob"], "email": ["alice@example.com", "bob@example.com"]}
        list_data = [
            {"user_id": 1, "name": "Alice", "email": "alice@example.com"},
            {"user_id": 2, "name": "Bob", "email": "bob@example.com"}
        ]

        df_from_dataclass = factory.convert(dataclass_data)
        df_from_dict = factory.convert(dict_data)
        df_from_list = factory.convert(list_data)

        # All should produce equivalent DataFrames
        check.equal(df_from_dataclass.shape, df_from_dict.shape)
        check.equal(df_from_dataclass.shape, df_from_list.shape)
        check.equal(set(df_from_dataclass.columns), set(df_from_dict.columns))
        check.equal(set(df_from_dataclass.columns), set(df_from_list.columns))


@pytest.mark.unit
class TestCrossBackendTypePreservation:
    """Test that data types are preserved consistently across input formats."""

    def test_type_preservation_integers(self):
        """Test that integer types are preserved consistently."""
        @dataclass
        class IntData:
            value: int

        dataclass_data = [IntData(value=42), IntData(value=100)]
        dict_data = {"value": [42, 100]}
        list_data = [{"value": 42}, {"value": 100}]

        df_from_dataclass = DataframeFromDataclass.convert(dataclass_data)
        df_from_dict = DataframeFromPydict.convert(dict_data)
        df_from_list = DataframeFromPylist.convert(list_data)

        # All should have integer type
        check.is_true(df_from_dataclass["value"].dtype in [pl.Int64, pl.Int32])
        check.is_true(df_from_dict["value"].dtype in [pl.Int64, pl.Int32])
        check.is_true(df_from_list["value"].dtype in [pl.Int64, pl.Int32])

    def test_type_preservation_booleans(self):
        """Test that boolean types are preserved consistently."""
        @dataclass
        class BoolData:
            active: bool

        dataclass_data = [BoolData(active=True), BoolData(active=False)]
        dict_data = {"active": [True, False]}
        list_data = [{"active": True}, {"active": False}]

        df_from_dataclass = DataframeFromDataclass.convert(dataclass_data)
        df_from_dict = DataframeFromPydict.convert(dict_data)
        df_from_list = DataframeFromPylist.convert(list_data)

        # All should have boolean type
        check.equal(df_from_dataclass["active"].dtype, pl.Boolean)
        check.equal(df_from_dict["active"].dtype, pl.Boolean)
        check.equal(df_from_list["active"].dtype, pl.Boolean)
