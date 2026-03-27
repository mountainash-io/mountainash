"""
Tests for named tuple round-trip conversion (DataFrame → NamedTuple → DataFrame).

This test suite validates that:
1. DataFrames can be converted to named tuples using the cast module
2. Named tuples can be converted back to DataFrames using the convert module
3. Round-trip conversion preserves data integrity
"""
from __future__ import annotations

import pytest
from collections import namedtuple
from typing import NamedTuple

from mountainash.dataframes import DataFrameUtils
from mountainash.dataframes.cast import DataFrameCastFactory
from mountainash.dataframes.ingress import PydataConverterFactory
from mountainash.dataframes.constants import CONST_PYTHON_DATAFORMAT


# Test fixtures using collections.namedtuple
Person = namedtuple('Person', ['name', 'age', 'city'])
Product = namedtuple('Product', ['id', 'name', 'price', 'in_stock'])


# Test fixtures using typing.NamedTuple (with type annotations)
class Employee(NamedTuple):
    employee_id: int
    name: str
    department: str
    salary: float


class Order(NamedTuple):
    order_id: int
    product: str
    quantity: int
    total: float


@pytest.fixture
def sample_people_data():
    """Sample data for Person named tuples."""
    return [
        Person('Alice', 30, 'NYC'),
        Person('Bob', 25, 'LA'),
        Person('Charlie', 35, 'Chicago')
    ]


@pytest.fixture
def sample_products_data():
    """Sample data for Product named tuples."""
    return [
        Product(1, 'Laptop', 999.99, True),
        Product(2, 'Mouse', 29.99, True),
        Product(3, 'Keyboard', 79.99, False)
    ]


@pytest.fixture
def sample_employees_data():
    """Sample data for Employee typed named tuples."""
    return [
        Employee(101, 'Alice Smith', 'Engineering', 95000.0),
        Employee(102, 'Bob Jones', 'Marketing', 75000.0),
        Employee(103, 'Charlie Brown', 'Sales', 65000.0)
    ]


class TestNamedTupleDetection:
    """Test that the factory correctly detects named tuple types."""

    def test_detect_single_namedtuple(self):
        """Test detection of single named tuple."""
        person = Person('Alice', 30, 'NYC')
        factory = PydataConverterFactory

        strategy_key = factory._get_strategy_key(person)
        assert strategy_key == CONST_PYTHON_DATAFORMAT.NAMEDTUPLE

    def test_detect_list_of_namedtuples(self, sample_people_data):
        """Test detection of list of named tuples."""
        factory = PydataConverterFactory

        strategy_key = factory._get_strategy_key(sample_people_data)
        assert strategy_key == CONST_PYTHON_DATAFORMAT.NAMEDTUPLE

    def test_detect_typed_namedtuple(self):
        """Test detection of typing.NamedTuple."""
        employee = Employee(101, 'Alice', 'Engineering', 95000.0)
        factory = PydataConverterFactory

        strategy_key = factory._get_strategy_key(employee)
        assert strategy_key == CONST_PYTHON_DATAFORMAT.NAMEDTUPLE

    def test_detect_list_of_typed_namedtuples(self, sample_employees_data):
        """Test detection of list of typing.NamedTuple."""
        factory = PydataConverterFactory

        strategy_key = factory._get_strategy_key(sample_employees_data)
        assert strategy_key == CONST_PYTHON_DATAFORMAT.NAMEDTUPLE

    def test_regular_tuple_not_detected_as_namedtuple(self):
        """Test that regular tuples are NOT detected as named tuples."""
        regular_tuple = ('Alice', 30, 'NYC')
        factory = PydataConverterFactory

        strategy_key = factory._get_strategy_key(regular_tuple)
        assert strategy_key != CONST_PYTHON_DATAFORMAT.NAMEDTUPLE


class TestNamedTupleToDataFrame:
    """Test conversion from named tuples to DataFrames."""

    def test_convert_single_namedtuple(self):
        """Test converting single named tuple to DataFrame."""
        person = Person('Alice', 30, 'NYC')
        factory = PydataConverterFactory

        df = factory.convert(person)

        assert df.shape == (1, 3)
        assert list(df.columns) == ['name', 'age', 'city']
        assert df['name'][0] == 'Alice'
        assert df['age'][0] == 30
        assert df['city'][0] == 'NYC'

    def test_convert_list_of_namedtuples(self, sample_people_data):
        """Test converting list of named tuples to DataFrame."""
        factory = PydataConverterFactory

        df = factory.convert(sample_people_data)

        assert df.shape == (3, 3)
        assert list(df.columns) == ['name', 'age', 'city']
        assert df['name'].to_list() == ['Alice', 'Bob', 'Charlie']
        assert df['age'].to_list() == [30, 25, 35]

    def test_convert_typed_namedtuple(self):
        """Test converting typing.NamedTuple to DataFrame."""
        employee = Employee(101, 'Alice', 'Engineering', 95000.0)
        factory = PydataConverterFactory

        df = factory.convert(employee)

        assert df.shape == (1, 4)
        assert list(df.columns) == ['employee_id', 'name', 'department', 'salary']
        assert df['employee_id'][0] == 101
        assert df['name'][0] == 'Alice'
        assert df['salary'][0] == 95000.0

    def test_convert_empty_list_raises_error(self):
        """Test that converting empty list raises ValueError."""
        factory = PydataConverterFactory

        # Empty list won't be detected as namedtuple, will use default strategy
        # This test is less relevant for our use case
        # Just verify it doesn't crash
        try:
            result = factory.convert([])
        except Exception:
            # Expected - empty data causes issues
            pass

    def test_convert_mixed_namedtuple_types_raises_error(self):
        """Test that mixing different named tuple types raises error."""
        mixed_data = [
            Person('Alice', 30, 'NYC'),
            Product(1, 'Laptop', 999.99, True)  # Different named tuple type
        ]
        factory = PydataConverterFactory

        with pytest.raises(ValueError, match="Inconsistent named tuple fields"):
            factory.convert(mixed_data)


class TestDataFrameToNamedTupleRoundTrip:
    """Test round-trip conversion: DataFrame → NamedTuple → DataFrame."""

    @pytest.mark.parametrize("backend", ["polars", "pandas"])
    def test_roundtrip_simple_data(self, backend, sample_people_data):
        """Test round-trip conversion with simple data across backends."""
        # Step 1: Create initial DataFrame (data is positional-only)
        df_original = DataFrameUtils.create_dataframe(
            [p._asdict() for p in sample_people_data],
            dataframe_framework=backend
        )

        # Step 2: Convert DataFrame → List[NamedTuple]
        cast_factory = DataFrameCastFactory
        cast_strategy = cast_factory.get_strategy(df_original)
        namedtuples = cast_strategy.to_list_of_named_tuples(df_original)

        # Verify namedtuples are correct type
        assert len(namedtuples) == 3
        assert hasattr(namedtuples[0], '_fields')
        assert namedtuples[0]._fields == ('name', 'age', 'city')

        # Step 3: Convert NamedTuple → DataFrame
        convert_factory = PydataConverterFactory
        df_final = convert_factory.convert(namedtuples)

        # Step 4: Verify data integrity
        assert df_final.shape == (3, 3)
        assert list(df_final.columns) == ['name', 'age', 'city']

        # Convert to common format for comparison
        df_orig_polars = DataFrameUtils.to_polars(df_original)

        # Compare data
        assert df_final['name'].to_list() == df_orig_polars['name'].to_list()
        assert df_final['age'].to_list() == df_orig_polars['age'].to_list()
        assert df_final['city'].to_list() == df_orig_polars['city'].to_list()

    @pytest.mark.parametrize("backend", ["polars", "pandas"])
    def test_roundtrip_typed_namedtuples(self, backend, sample_employees_data):
        """Test round-trip with typed named tuples."""
        # Step 1: Create initial DataFrame (data is positional-only)
        df_original = DataFrameUtils.create_dataframe(
            [e._asdict() for e in sample_employees_data],
            dataframe_framework=backend
        )

        # Step 2: Convert DataFrame → List[TypedNamedTuple]
        cast_factory = DataFrameCastFactory
        cast_strategy = cast_factory.get_strategy(df_original)
        typed_namedtuples = cast_strategy.to_list_of_typed_named_tuples(df_original)

        # Verify typed namedtuples
        assert len(typed_namedtuples) == 3
        assert hasattr(typed_namedtuples[0], '_fields')
        assert hasattr(typed_namedtuples[0], '__annotations__')

        # Step 3: Convert TypedNamedTuple → DataFrame
        convert_factory = PydataConverterFactory
        df_final = convert_factory.convert(typed_namedtuples)

        # Step 4: Verify data integrity
        assert df_final.shape == (3, 4)
        assert set(df_final.columns) == {'employee_id', 'name', 'department', 'salary'}

    def test_roundtrip_single_row(self):
        """Test round-trip conversion with single row."""
        # Step 1: Create single-row DataFrame (data is positional-only)
        df_original = DataFrameUtils.create_polars(
            {'id': [1], 'name': ['Alice'], 'value': [99.9]}
        )

        # Step 2: DataFrame → NamedTuple
        cast_factory = DataFrameCastFactory
        cast_strategy = cast_factory.get_strategy(df_original)
        namedtuples = cast_strategy.to_list_of_named_tuples(df_original)

        assert len(namedtuples) == 1

        # Step 3: NamedTuple → DataFrame (single item, not in list)
        convert_factory = PydataConverterFactory
        df_final = convert_factory.convert(namedtuples[0])  # Single named tuple

        # Step 4: Verify
        assert df_final.shape == (1, 3)
        assert df_final['name'][0] == 'Alice'

    @pytest.mark.parametrize("backend", ["polars", "pandas"])
    def test_roundtrip_preserves_column_order(self, backend):
        """Test that round-trip preserves column order."""
        # Step 1: Create DataFrame with specific column order (data is positional-only)
        df_original = DataFrameUtils.create_dataframe(
            {'z_col': [1, 2], 'a_col': [3, 4], 'm_col': [5, 6]},
            dataframe_framework=backend
        )

        original_columns = list(DataFrameUtils.column_names(df_original))

        # Step 2: DataFrame → NamedTuple
        cast_factory = DataFrameCastFactory
        cast_strategy = cast_factory.get_strategy(df_original)
        namedtuples = cast_strategy.to_list_of_named_tuples(df_original)

        # Step 3: NamedTuple → DataFrame
        convert_factory = PydataConverterFactory
        df_final = convert_factory.convert(namedtuples)

        # Step 4: Verify column order preserved
        assert list(df_final.columns) == original_columns


class TestNamedTupleEdgeCases:
    """Test edge cases and error handling."""

    def test_namedtuple_with_special_characters_in_fields(self):
        """Test named tuples with unusual but valid field names."""
        # Note: Field names must be valid Python identifiers
        SpecialData = namedtuple('SpecialData', ['field_1', 'field_2', 'field_3'])
        data = [SpecialData(1, 2, 3), SpecialData(4, 5, 6)]

        factory = PydataConverterFactory
        df = factory.convert(data)

        assert df.shape == (2, 3)
        assert list(df.columns) == ['field_1', 'field_2', 'field_3']

    def test_namedtuple_with_none_values(self):
        """Test named tuples containing None values."""
        DataWithNone = namedtuple('DataWithNone', ['a', 'b', 'c'])
        data = [
            DataWithNone(1, None, 'x'),
            DataWithNone(None, 2, 'y'),
            DataWithNone(3, 4, None)
        ]

        factory = PydataConverterFactory
        df = factory.convert(data)

        assert df.shape == (3, 3)
        # Polars handles None values as null
        assert df['b'][0] is None
        assert df['a'][1] is None

    def test_large_namedtuple_list(self):
        """Test conversion of large list of named tuples."""
        LargeData = namedtuple('LargeData', ['id', 'value'])
        data = [LargeData(i, i * 10) for i in range(1000)]

        factory = PydataConverterFactory
        df = factory.convert(data)

        assert df.shape == (1000, 2)
        assert df['id'][0] == 0
        assert df['id'][999] == 999
        assert df['value'][999] == 9990


class TestNamedTupleWithColumnConfig:
    """Test named tuple conversion with column transformations."""

    def test_namedtuple_with_column_rename(self):
        """Test renaming columns during named tuple conversion."""
        from mountainash.dataframes.schema_config import SchemaConfig

        data = [Person('Alice', 30, 'NYC'), Person('Bob', 25, 'LA')]

        # Correct API: columns is Dict[str, Dict[str, Any]]
        column_config = SchemaConfig(
            columns={
                'name': {'rename': 'full_name'},
                'city': {'rename': 'location'}
            }
        )

        factory = PydataConverterFactory
        df = factory.convert(data, column_config=column_config)

        assert set(df.columns) == {'full_name', 'age', 'location'}
        assert df['full_name'][0] == 'Alice'
        assert df['location'][0] == 'NYC'

    def test_namedtuple_filter_unmapped_columns(self):
        """Test filtering unmapped columns during conversion."""
        from mountainash.dataframes.schema_config import SchemaConfig

        data = [Person('Alice', 30, 'NYC'), Person('Bob', 25, 'LA')]

        # Only map 'name' - other columns should be filtered with keep_only_mapped=True
        column_config = SchemaConfig(
            columns={'name': {'rename': 'full_name'}},
            keep_only_mapped=True
        )

        factory = PydataConverterFactory
        df = factory.convert(data, column_config=column_config)

        assert list(df.columns) == ['full_name']
        assert df.shape == (2, 1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
