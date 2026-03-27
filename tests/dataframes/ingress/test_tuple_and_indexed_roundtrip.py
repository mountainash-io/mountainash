"""
Tests for plain tuple and indexed data round-trip conversion.

This test suite validates:
1. DataFrames can be converted to tuples/indexed data using the cast module
2. Tuples/indexed data can be converted back to DataFrames using the convert module
3. Round-trip conversion preserves data integrity
"""
from __future__ import annotations

import pytest
from collections import namedtuple

from mountainash.dataframes import DataFrameUtils
from mountainash.dataframes.cast import DataFrameCastFactory
from mountainash.dataframes.ingress import PydataConverterFactory, PydataConverter
from mountainash.dataframes.constants import CONST_PYTHON_DATAFORMAT


# Test fixtures
Person = namedtuple('Person', ['name', 'age', 'city'])


@pytest.fixture
def sample_dataframe_polars():
    """Sample Polars DataFrame."""
    return DataFrameUtils.create_polars({
        'id': [1, 2, 3],
        'name': ['Alice', 'Bob', 'Charlie'],
        'value': [100, 200, 300]
    })


class TestTupleDetection:
    """Test that the factory correctly detects plain tuple types."""

    def test_detect_single_tuple(self):
        """Test detection of single plain tuple."""
        data = (1, 'Alice', 30)
        # factory = PydataConverterFactory()

        strategy_key = PydataConverterFactory._get_strategy_key(data)
        assert strategy_key == CONST_PYTHON_DATAFORMAT.TUPLE

    def test_detect_list_of_tuples(self):
        """Test detection of list of plain tuples."""
        data = [(1, 'Alice', 30), (2, 'Bob', 25)]
        # factory = PydataConverterFactory()

        strategy_key = PydataConverterFactory._get_strategy_key(data)
        assert strategy_key == CONST_PYTHON_DATAFORMAT.TUPLE

    def test_named_tuple_not_detected_as_plain_tuple(self):
        """Test that named tuples are NOT detected as plain tuples."""
        data = Person('Alice', 30, 'NYC')
        # factory = PydataConverterFactory()

        strategy_key = PydataConverterFactory._get_strategy_key(data)
        assert strategy_key == CONST_PYTHON_DATAFORMAT.NAMEDTUPLE


class TestTupleToDataFrame:
    """Test conversion from plain tuples to DataFrames."""

    def test_convert_single_tuple_auto_names(self):
        """Test converting single tuple with auto-generated column names."""
        data = (1, 'Alice', 30)
        # factory = PydataConverterFactory()

        df = PydataConverter.convert(data)

        assert df.shape == (1, 3)
        assert list(df.columns) == ['col_0', 'col_1', 'col_2']
        assert df['col_0'][0] == 1
        assert df['col_1'][0] == 'Alice'
        assert df['col_2'][0] == 30

    def test_convert_list_of_tuples_with_column_names(self):
        """Test converting list of tuples with explicit column names."""
        data = [(1, 'Alice', 30), (2, 'Bob', 25), (3, 'Charlie', 35)]
        # factory = PydataConverterFactory()

        # Note: column_names must be passed as kwarg to convert method
        from mountainash.dataframes.ingress.dataframe_from_tuple import DataframeFromTuple
        df = DataframeFromTuple.convert(data, column_names=['id', 'name', 'age'])

        assert df.shape == (3, 3)
        assert list(df.columns) == ['id', 'name', 'age']
        assert df['name'].to_list() == ['Alice', 'Bob', 'Charlie']

    def test_convert_empty_list_raises_error(self):
        """Test that converting empty list raises ValueError."""
        from mountainash.dataframes.ingress.dataframe_from_tuple import DataframeFromTuple

        with pytest.raises(ValueError, match="Cannot convert empty sequence"):
            DataframeFromTuple.convert([])

    def test_convert_mixed_tuple_lengths_raises_error(self):
        """Test that tuples with inconsistent lengths raise error."""
        from mountainash.dataframes.ingress.dataframe_from_tuple import DataframeFromTuple
        data = [(1, 'Alice', 30), (2, 'Bob')]  # Second tuple is shorter

        with pytest.raises(ValueError, match="Inconsistent tuple length"):
            DataframeFromTuple.convert(data)

    def test_column_name_count_mismatch_raises_error(self):
        """Test that wrong number of column names raises error."""
        from mountainash.dataframes.ingress.dataframe_from_tuple import DataframeFromTuple
        data = [(1, 'Alice', 30), (2, 'Bob', 25)]

        with pytest.raises(ValueError, match="Column name count mismatch"):
            DataframeFromTuple.convert(data, column_names=['id', 'name'])  # Missing 'age'


class TestIndexedDataDetection:
    """Test that the factory correctly detects indexed data structures."""

    def test_detect_indexed_with_tuple_rows(self):
        """Test detection of indexed data with tuple rows."""
        data = {'A': [(1, 'x'), (2, 'y')], 'B': [(3, 'z')]}
        # factory = PydataConverterFactory()

        strategy_key = PydataConverterFactory._get_strategy_key(data)
        assert strategy_key == CONST_PYTHON_DATAFORMAT.INDEXED_DATA

    def test_detect_indexed_with_dict_rows(self):
        """Test detection of indexed data with dict rows."""
        data = {'A': [{'value': 1}, {'value': 2}], 'B': [{'value': 3}]}
        # factory = PydataConverterFactory()

        strategy_key = PydataConverterFactory._get_strategy_key(data)
        assert strategy_key == CONST_PYTHON_DATAFORMAT.INDEXED_DATA

    def test_detect_indexed_with_namedtuple_rows(self):
        """Test detection of indexed data with named tuple rows."""
        data = {'A': [Person('Alice', 30, 'NYC')], 'B': [Person('Bob', 25, 'LA')]}
        # factory = PydataConverterFactory()

        strategy_key = PydataConverterFactory._get_strategy_key(data)
        assert strategy_key == CONST_PYTHON_DATAFORMAT.INDEXED_DATA

    def test_pydict_not_detected_as_indexed(self):
        """Test that PYDICT (column data) is not detected as indexed data."""
        data = {'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']}  # Column values (scalars)
        # factory = PydataConverterFactory()

        strategy_key = PydataConverterFactory._get_strategy_key(data)
        assert strategy_key == CONST_PYTHON_DATAFORMAT.PYDICT


class TestIndexedDataToDataFrame:
    """Test conversion from indexed data to DataFrames."""

    def test_convert_simple_indexed_with_tuples(self):
        """Test converting indexed data with tuple rows."""
        data = {'A': [(1, 'x'), (2, 'y')], 'B': [(3, 'z')]}
        # factory = PydataConverterFactory()

        df = PydataConverter.convert(data)

        assert df.shape == (3, 3)  # 3 rows, 3 columns (index + 2 data cols)
        assert 'index' in df.columns
        assert df['index'].to_list() == ['A', 'A', 'B']

    def test_convert_indexed_with_dict_rows(self):
        """Test converting indexed data with dict rows."""
        data = {
            'A': [{'value': 1, 'label': 'x'}],
            'B': [{'value': 2, 'label': 'y'}]
        }
        # factory = PydataConverterFactory()

        df = PydataConverter.convert(data)

        assert df.shape == (2, 3)  # 2 rows, 3 columns
        assert set(df.columns) == {'index', 'value', 'label'}
        assert df['value'].to_list() == [1, 2]

    def test_convert_indexed_with_namedtuples(self):
        """Test converting indexed data with named tuple rows."""
        data = {
            'A': [Person('Alice', 30, 'NYC'), Person('Bob', 25, 'LA')],
            'B': [Person('Charlie', 35, 'Chicago')]
        }
        # factory = PydataConverterFactory()

        df = PydataConverter.convert(data)

        assert df.shape == (3, 4)  # 3 rows, 4 columns (index + 3 data cols)
        assert 'index' in df.columns
        assert 'name' in df.columns
        assert df['name'].to_list() == ['Alice', 'Bob', 'Charlie']

    def test_convert_indexed_with_composite_keys(self):
        """Test converting indexed data with composite (tuple) keys."""
        from mountainash.dataframes.ingress.dataframe_from_indexed import DataframeFromIndexedData

        data = {
            ('2024', 'Q1'): [{'revenue': 100}],
            ('2024', 'Q2'): [{'revenue': 120}],
            ('2025', 'Q1'): [{'revenue': 150}]
        }

        df = DataframeFromIndexedData.convert(data)

        assert df.shape == (3, 3)  # 3 rows, 3 columns (2 index + 1 data)
        assert 'index_0' in df.columns
        assert 'index_1' in df.columns
        assert df['revenue'].to_list() == [100, 120, 150]

    def test_convert_indexed_with_custom_index_names(self):
        """Test converting indexed data with custom index column names."""
        from mountainash.dataframes.ingress.dataframe_from_indexed import DataframeFromIndexedData

        data = {
            ('2024', 'Q1'): [{'revenue': 100}],
            ('2024', 'Q2'): [{'revenue': 120}]
        }

        df = DataframeFromIndexedData.convert(
            data,
            index_column_names=['year', 'quarter']
        )

        assert 'year' in df.columns
        assert 'quarter' in df.columns
        assert df['year'].to_list() == ['2024', '2024']
        assert df['quarter'].to_list() == ['Q1', 'Q2']

    def test_empty_indexed_data_returns_empty_dataframe(self):
        """Test that empty indexed data returns empty DataFrame."""
        # factory = PydataConverterFactory()

        df = PydataConverter.convert({})

        assert df.shape[0] == 0


class TestTupleRoundTrip:
    """Test round-trip conversion: DataFrame → Tuple → DataFrame."""

    def test_roundtrip_to_plain_tuples(self, sample_dataframe_polars):
        """Test round-trip using plain tuples (note: no tuple export in cast currently)."""
        # Note: Cast module doesn't have a direct "to_list_of_tuples" method
        # But we can test using rows() which returns tuples
        df_original = sample_dataframe_polars

        # Get tuples from DataFrame using Polars .rows() method
        tuples = df_original.rows()

        # Convert back to DataFrame
        from mountainash.dataframes.ingress.dataframe_from_tuple import DataframeFromTuple
        df_final = DataframeFromTuple.convert(
            tuples,
            column_names=list(df_original.columns)
        )

        # Verify shape
        assert df_final.shape == df_original.shape

        # Verify data
        assert df_final['name'].to_list() == df_original['name'].to_list()


class TestIndexedDataRoundTrip:
    """Test round-trip conversion: DataFrame → Indexed Data → DataFrame."""

    @pytest.mark.parametrize("backend", ["polars"])
    def test_roundtrip_index_of_tuples(self, backend):
        """Test round-trip using index_of_tuples."""
        # Step 1: Create initial DataFrame
        df_original = DataFrameUtils.create_dataframe(
            {'category': ['A', 'A', 'B'], 'value': [1, 2, 3], 'label': ['x', 'y', 'z']},
            dataframe_framework=backend
        )

        # Step 2: Convert DataFrame → Indexed Tuples
        # cast_factory = DataFrameCastFactory()
        strategy = DataFrameCastFactory.get_strategy(df_original)
        indexed_data = strategy.to_index_of_tuples(df_original, index_fields='category')

        # Verify indexed structure
        assert 'A' in indexed_data
        assert 'B' in indexed_data
        assert len(indexed_data['A']) == 2  # Two rows with category='A'

        # Step 3: Convert Indexed Data → DataFrame
        # convert_factory = PydataConverterFactory()
        df_final = PydataConverter.convert(indexed_data)

        # Step 4: Verify data integrity
        # Note: Order may differ, so we just check the values are present
        assert df_final.shape[0] == 3
        assert set(df_final['index'].to_list()) == {'A', 'B'}

    @pytest.mark.parametrize("backend", ["polars"])
    def test_roundtrip_index_of_dictionaries(self, backend):
        """Test round-trip using index_of_dictionaries."""
        # Step 1: Create initial DataFrame
        df_original = DataFrameUtils.create_dataframe(
            {'category': ['A', 'A', 'B'], 'value': [10, 20, 30]},
            dataframe_framework=backend
        )

        # Step 2: DataFrame → Indexed Dictionaries
        # cast_factory = DataFrameCastFactory()
        strategy = DataFrameCastFactory.get_strategy(df_original)
        indexed_data = strategy.to_index_of_dictionaries(df_original, index_fields='category')

        # Step 3: Indexed Data → DataFrame
        # convert_factory = PydataConverterFactory()
        df_final = PydataConverter.convert(indexed_data)

        # Step 4: Verify
        assert df_final.shape[0] == 3
        assert 'index' in df_final.columns
        assert 'value' in df_final.columns

    @pytest.mark.parametrize("backend", ["polars"])
    def test_roundtrip_index_of_namedtuples(self, backend):
        """Test round-trip using index_of_named_tuples."""
        # Step 1: Create DataFrame
        df_original = DataFrameUtils.create_dataframe(
            [
                {'region': 'North', 'sales': 100, 'cost': 50},
                {'region': 'North', 'sales': 110, 'cost': 55},
                {'region': 'South', 'sales': 90, 'cost': 45}
            ],
            dataframe_framework=backend
        )

        # Step 2: DataFrame → Indexed Named Tuples
        # cast_factory = DataFrameCastFactory()
        strategy = DataFrameCastFactory.get_strategy(df_original)
        indexed_data = strategy.to_index_of_named_tuples(df_original, index_fields='region')

        # Verify structure
        assert 'North' in indexed_data
        assert 'South' in indexed_data
        assert hasattr(indexed_data['North'][0], '_fields')

        # Step 3: Indexed Data → DataFrame
        # convert_factory = PydataConverterFactory()
        df_final = PydataConverter.convert(indexed_data)

        # Step 4: Verify
        assert df_final.shape[0] == 3
        assert set(df_final.columns) == {'index', 'region', 'sales', 'cost'}
        assert set(df_final['index'].to_list()) == {'North', 'South'}


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_tuple_with_none_values(self):
        """Test tuples containing None values."""
        from mountainash.dataframes.ingress.dataframe_from_tuple import DataframeFromTuple

        data = [(1, None, 'x'), (None, 2, 'y'), (3, 4, None)]
        df = DataframeFromTuple.convert(data, column_names=['a', 'b', 'c'])

        assert df.shape == (3, 3)
        assert df['b'][0] is None
        assert df['a'][1] is None

    def test_large_tuple_list(self):
        """Test conversion of large list of tuples."""
        from mountainash.dataframes.ingress.dataframe_from_tuple import DataframeFromTuple

        data = [(i, i * 10) for i in range(1000)]
        df = DataframeFromTuple.convert(data, column_names=['id', 'value'])

        assert df.shape == (1000, 2)
        assert df['id'][999] == 999
        assert df['value'][999] == 9990


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
