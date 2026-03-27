"""
Tests for Series dictionary round-trip conversion.

This test suite validates:
1. DataFrames can be converted to Series dicts using the cast module
2. Series dicts can be converted back to DataFrames using the convert module
3. Round-trip conversion preserves data integrity
4. Both Polars and Pandas Series are supported
"""
from __future__ import annotations

import pytest

from mountainash.dataframes import DataFrameUtils
from mountainash.dataframes.cast import DataFrameCastFactory
from mountainash.dataframes.ingress import PydataConverterFactory, PydataConverter
from mountainash.dataframes.constants import CONST_PYTHON_DATAFORMAT


@pytest.fixture
def sample_dataframe_polars():
    """Sample Polars DataFrame."""
    return DataFrameUtils.create_polars({
        'id': [1, 2, 3],
        'name': ['Alice', 'Bob', 'Charlie'],
        'value': [100, 200, 300]
    })


class TestSeriesDictDetection:
    """Test that the factory correctly detects Series dict types."""

    def test_detect_polars_series_dict(self):
        """Test detection of Polars Series dictionary."""
        import polars as pl

        data = {
            'col1': pl.Series([1, 2, 3]),
            'col2': pl.Series(['a', 'b', 'c'])
        }
        # factory = PydataConverterFactory()

        strategy_key = PydataConverterFactory._get_strategy_key(data)
        assert strategy_key == CONST_PYTHON_DATAFORMAT.SERIES_DICT

    @pytest.mark.skipif(
        not pytest.importorskip("pandas", reason="pandas not installed"),
        reason="pandas not installed"
    )
    def test_detect_pandas_series_dict(self):
        """Test detection of Pandas Series dictionary."""
        import pandas as pd

        data = {
            'col1': pd.Series([1, 2, 3]),
            'col2': pd.Series(['a', 'b', 'c'])
        }
        # factory = PydataConverterFactory()

        strategy_key = PydataConverterFactory._get_strategy_key(data)
        assert strategy_key == CONST_PYTHON_DATAFORMAT.SERIES_DICT

    def test_pydict_not_detected_as_series_dict(self):
        """Test that regular dict of lists is not detected as Series dict."""
        data = {'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']}
        # factory = PydataConverterFactory()

        strategy_key = PydataConverterFactory._get_strategy_key(data)
        assert strategy_key == CONST_PYTHON_DATAFORMAT.PYDICT


class TestSeriesDictToDataFrame:
    """Test conversion from Series dicts to DataFrames."""

    def test_convert_polars_series_dict(self):
        """Test converting Polars Series dictionary to DataFrame."""
        import polars as pl

        data = {
            'id': pl.Series([1, 2, 3]),
            'name': pl.Series(['Alice', 'Bob', 'Charlie']),
            'value': pl.Series([100, 200, 300])
        }
        # factory = PydataConverterFactory()

        df = PydataConverter.convert(data)

        assert df.shape == (3, 3)
        assert list(df.columns) == ['id', 'name', 'value']
        assert df['id'].to_list() == [1, 2, 3]
        assert df['name'].to_list() == ['Alice', 'Bob', 'Charlie']

    @pytest.mark.skipif(
        not pytest.importorskip("pandas", reason="pandas not installed"),
        reason="pandas not installed"
    )
    def test_convert_pandas_series_dict(self):
        """Test converting Pandas Series dictionary to DataFrame."""
        import pandas as pd

        data = {
            'id': pd.Series([1, 2, 3]),
            'name': pd.Series(['Alice', 'Bob', 'Charlie']),
            'value': pd.Series([100, 200, 300])
        }
        # factory = PydataConverterFactory()

        df = PydataConverter.convert(data)

        assert df.shape == (3, 3)
        assert list(df.columns) == ['id', 'name', 'value']
        assert df['id'].to_list() == [1, 2, 3]
        assert df['name'].to_list() == ['Alice', 'Bob', 'Charlie']

    def test_empty_series_dict_returns_empty_dataframe(self):
        """Test that empty Series dict returns empty DataFrame."""
        # factory = PydataConverterFactory()

        df = PydataConverter.convert({})

        assert df.shape[0] == 0

    def test_series_dict_with_different_lengths_handled(self):
        """Test Series with different lengths (Polars should handle or error appropriately)."""
        import polars as pl

        data = {
            'col1': pl.Series([1, 2, 3]),
            'col2': pl.Series(['a', 'b'])  # Different length
        }

        # factory = PydataConverterFactory()

        # Polars will raise an error for mismatched lengths
        with pytest.raises(Exception):  # Could be various exception types
            PydataConverter.convert(data)


class TestSeriesDictRoundTrip:
    """Test round-trip conversion: DataFrame → Series Dict → DataFrame."""

    def test_roundtrip_polars_series(self, sample_dataframe_polars):
        """Test round-trip using Polars Series."""
        df_original = sample_dataframe_polars

        # Step 1: DataFrame → Dict[str, Series]
        # cast_factory = DataFrameCastFactory()
        strategy = DataFrameCastFactory.get_strategy(df_original)
        series_dict = strategy.to_dictionary_of_series_polars(df_original)

        # Verify it's a dict of Polars Series
        assert isinstance(series_dict, dict)
        assert len(series_dict) == 3
        import polars as pl
        for key, value in series_dict.items():
            assert isinstance(value, pl.Series)

        # Step 2: Dict[str, Series] → DataFrame
        # convert_factory = PydataConverterFactory()
        df_final = PydataConverter.convert(series_dict)

        # Step 3: Verify data integrity
        assert df_final.shape == df_original.shape
        assert list(df_final.columns) == list(df_original.columns)
        assert df_final['id'].to_list() == df_original['id'].to_list()
        assert df_final['name'].to_list() == df_original['name'].to_list()
        assert df_final['value'].to_list() == df_original['value'].to_list()

    @pytest.mark.skipif(
        not pytest.importorskip("pandas", reason="pandas not installed"),
        reason="pandas not installed"
    )
    def test_roundtrip_pandas_series(self, sample_dataframe_polars):
        """Test round-trip using Pandas Series."""
        df_original = sample_dataframe_polars

        # Step 1: DataFrame → Dict[str, pd.Series]
        # cast_factory = DataFrameCastFactory()
        strategy = DataFrameCastFactory.get_strategy(df_original)
        series_dict = strategy.to_dictionary_of_series_pandas(df_original)

        # Verify it's a dict of Pandas Series
        assert isinstance(series_dict, dict)
        assert len(series_dict) == 3
        import pandas as pd
        for key, value in series_dict.items():
            assert isinstance(value, pd.Series)

        # Step 2: Dict[str, pd.Series] → DataFrame
        # convert_factory = PydataConverterFactory()
        df_final = PydataConverter.convert(series_dict)

        # Step 3: Verify data integrity
        assert df_final.shape == df_original.shape
        assert set(df_final.columns) == set(df_original.columns)
        # Note: Order might differ, so we check values
        assert sorted(df_final['id'].to_list()) == sorted(df_original['id'].to_list())
        assert sorted(df_final['name'].to_list()) == sorted(df_original['name'].to_list())

    @pytest.mark.parametrize("backend", ["polars"])
    def test_roundtrip_preserves_dtypes(self, backend):
        """Test that round-trip preserves data types."""
        # Create DataFrame with specific types
        df_original = DataFrameUtils.create_dataframe(
            {
                'int_col': [1, 2, 3],
                'float_col': [1.5, 2.5, 3.5],
                'str_col': ['a', 'b', 'c']
            },
            dataframe_framework=backend
        )

        # Convert to Series dict and back
        # cast_factory = DataFrameCastFactory()
        strategy = DataFrameCastFactory.get_strategy(df_original)
        series_dict = strategy.to_dictionary_of_series_polars(df_original)

        # convert_factory = PydataConverterFactory()
        df_final = PydataConverter.convert(series_dict)

        # Check dtypes are preserved (at least the general category)
        import polars as pl
        assert df_final['int_col'].dtype in [pl.Int64, pl.Int32]
        assert df_final['float_col'].dtype == pl.Float64
        assert df_final['str_col'].dtype == pl.String


class TestSeriesDictEdgeCases:
    """Test edge cases and error handling."""

    def test_series_with_none_values(self):
        """Test Series containing None/null values."""
        import polars as pl

        data = {
            'col1': pl.Series([1, None, 3]),
            'col2': pl.Series(['a', 'b', None])
        }
        # factory = PydataConverterFactory()

        df = PydataConverter.convert(data)

        assert df.shape == (3, 2)
        assert df['col1'][1] is None
        assert df['col2'][2] is None

    def test_large_series_dict(self):
        """Test conversion of large Series dictionary."""
        import polars as pl

        data = {
            'id': pl.Series(list(range(1000))),
            'value': pl.Series([i * 10 for i in range(1000)])
        }
        # factory = PydataConverterFactory()

        df = PydataConverter.convert(data)

        assert df.shape == (1000, 2)
        assert df['id'][999] == 999
        assert df['value'][999] == 9990

    def test_series_dict_with_column_config(self):
        """Test Series dict conversion with column transformations."""
        import polars as pl
        from mountainash.dataframes.schema_config import SchemaConfig

        data = {
            'old_name': pl.Series([1, 2, 3]),
            'another_col': pl.Series(['a', 'b', 'c'])
        }

        column_config = SchemaConfig(
            columns={'old_name': {'rename': 'new_name'}}
        )

        # factory = PydataConverterFactory()
        df = PydataConverter.convert(data, column_config=column_config)

        assert 'new_name' in df.columns
        assert 'old_name' not in df.columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
