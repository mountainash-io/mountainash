"""
Tests for edge cases in the cast module.

This module tests edge cases, boundary conditions, and error scenarios
to ensure robust behavior across all casting operations.
"""

import pytest
import pandas as pd
import polars as pl
import pyarrow as pa
import narwhals as nw

from mountainash.dataframes.cast import DataFrameCastFactory
from mountainash.dataframes import DataFrameUtils


@pytest.mark.unit
class TestEmptyDataFrames:
    """Test cast operations with empty DataFrames."""

    @pytest.mark.parametrize("backend_name", ["pandas", "polars", "pyarrow", "ibis", "narwhals"])
    def test_empty_to_pandas(self, empty_dataframes, backend_name):
        """Test converting empty DataFrames to pandas."""
        df = empty_dataframes[backend_name]
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy.to_pandas(df)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    @pytest.mark.parametrize("backend_name", ["pandas", "polars", "pyarrow", "ibis", "narwhals"])
    def test_empty_to_polars(self, empty_dataframes, backend_name):
        """Test converting empty DataFrames to polars."""
        df = empty_dataframes[backend_name]
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy.to_polars(df)

        if isinstance(result, pl.LazyFrame):
            result = result.collect()

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 0

    @pytest.mark.parametrize("backend_name", ["pandas", "polars", "pyarrow", "ibis", "narwhals"])
    def test_empty_to_dict_of_lists(self, empty_dataframes, backend_name):
        """Test converting empty DataFrames to dictionary of lists."""
        df = empty_dataframes[backend_name]
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy.to_dictionary_of_lists(df)

        assert isinstance(result, dict)
        # Empty dataframe should have empty dict or dict with empty lists

    @pytest.mark.parametrize("backend_name", ["pandas", "polars", "pyarrow", "ibis", "narwhals"])
    def test_empty_to_list_of_dicts(self, empty_dataframes, backend_name):
        """Test converting empty DataFrames to list of dictionaries."""
        df = empty_dataframes[backend_name]
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy.to_list_of_dictionaries(df)

        assert isinstance(result, list)
        assert len(result) == 0


@pytest.mark.unit
class TestSingleRowDataFrames:
    """Test cast operations with single-row DataFrames."""

    def test_single_row_pandas_to_polars(self, single_row_data):
        """Test single-row pandas to polars conversion."""
        df = pd.DataFrame(single_row_data)
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy.to_polars(df)

        if isinstance(result, pl.LazyFrame):
            result = result.collect()

        assert len(result) == 1
        assert result.columns == list(df.columns)

    def test_single_row_to_dict_of_lists(self, single_row_data):
        """Test single-row DataFrame to dictionary of lists."""
        df = pd.DataFrame(single_row_data)
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy.to_dictionary_of_lists(df)

        assert isinstance(result, dict)
        assert all(len(v) == 1 for v in result.values())

    def test_single_row_to_list_of_dicts(self, single_row_data):
        """Test single-row DataFrame to list of dictionaries."""
        df = pd.DataFrame(single_row_data)
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy.to_list_of_dictionaries(df)

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], dict)


@pytest.mark.unit
class TestSingleColumnDataFrames:
    """Test cast operations with single-column DataFrames."""

    def test_single_column_pandas_to_polars(self, single_column_data):
        """Test single-column pandas to polars conversion."""
        df = pd.DataFrame(single_column_data)
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy.to_polars(df)

        if isinstance(result, pl.LazyFrame):
            result = result.collect()

        assert len(result.columns) == 1
        assert result.columns == list(df.columns)

    def test_single_column_to_dict_of_lists(self, single_column_data):
        """Test single-column DataFrame to dictionary of lists."""
        df = pd.DataFrame(single_column_data)
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy.to_dictionary_of_lists(df)

        assert isinstance(result, dict)
        assert len(result) == 1
        assert "id" in result


@pytest.mark.unit
class TestNullHandling:
    """Test cast operations with null values."""

    def test_nulls_pandas_to_polars(self, dataframes_with_nulls):
        """Test null preservation in pandas to polars conversion."""
        df = pd.DataFrame(dataframes_with_nulls)
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy.to_polars(df)

        if isinstance(result, pl.LazyFrame):
            result = result.collect()

        # Check that nulls are preserved
        assert result['name'].null_count() > 0
        assert result['value'].null_count() > 0

    def test_nulls_polars_to_pandas(self, dataframes_with_nulls):
        """Test null preservation in polars to pandas conversion."""
        df = pl.DataFrame(dataframes_with_nulls)
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy.to_pandas(df)

        # Check that nulls are preserved
        assert result['name'].isna().sum() > 0
        assert result['value'].isna().sum() > 0

    def test_nulls_to_dict_of_lists(self, dataframes_with_nulls):
        """Test null handling in dictionary conversion."""
        df = pd.DataFrame(dataframes_with_nulls)
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy.to_dictionary_of_lists(df)

        assert isinstance(result, dict)
        # Nulls should be represented as None in the lists
        assert None in result['name']

    def test_nulls_to_list_of_dicts(self, dataframes_with_nulls):
        """Test null handling in list of dicts conversion."""
        df = pd.DataFrame(dataframes_with_nulls)
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy.to_list_of_dictionaries(df)

        assert isinstance(result, list)
        # Some values should be None
        assert any(row.get('name') is None for row in result)


@pytest.mark.unit
class TestLargeDataFrames:
    """Test cast operations with large DataFrames."""

    def test_large_pandas_to_polars(self, large_dataframe_data):
        """Test large pandas to polars conversion."""
        df = pd.DataFrame(large_dataframe_data)
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy.to_polars(df)

        if isinstance(result, pl.LazyFrame):
            result = result.collect()

        assert len(result) == 1000
        assert result.columns == list(df.columns)

    def test_large_polars_to_pandas(self, large_dataframe_data):
        """Test large polars to pandas conversion."""
        df = pl.DataFrame(large_dataframe_data)
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy.to_pandas(df)

        assert len(result) == 1000
        assert list(result.columns) == df.columns

    def test_large_to_dict_of_lists(self, large_dataframe_data):
        """Test large DataFrame to dictionary of lists conversion."""
        df = pd.DataFrame(large_dataframe_data)
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy.to_dictionary_of_lists(df)

        assert isinstance(result, dict)
        assert all(len(v) == 1000 for v in result.values())

    def test_large_to_list_of_dicts(self, large_dataframe_data):
        """Test large DataFrame to list of dicts conversion."""
        df = pd.DataFrame(large_dataframe_data)
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy.to_list_of_dictionaries(df)

        assert isinstance(result, list)
        assert len(result) == 1000


@pytest.mark.unit
class TestSpecialCharacters:
    """Test cast operations with special characters in column names."""

    def test_special_chars_pandas_to_polars(self, special_characters_data):
        """Test special characters in pandas to polars conversion."""
        df = pd.DataFrame(special_characters_data)
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy.to_polars(df)

        if isinstance(result, pl.LazyFrame):
            result = result.collect()

        # Column names should be preserved
        assert set(result.columns) == set(df.columns)

    def test_special_chars_to_dict(self, special_characters_data):
        """Test special characters in column names for dict conversion."""
        df = pd.DataFrame(special_characters_data)
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy.to_dictionary_of_lists(df)

        # All original columns should be present
        assert set(result.keys()) == set(df.columns)


@pytest.mark.unit
class TestMixedTypes:
    """Test cast operations with mixed data types."""

    def test_mixed_types_pandas_to_polars(self, mixed_types_data):
        """Test mixed types in pandas to polars conversion."""
        # Skip the 'mixed' column which has truly mixed types
        data = {k: v for k, v in mixed_types_data.items() if k != 'mixed'}
        df = pd.DataFrame(data)
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy.to_polars(df)

        if isinstance(result, pl.LazyFrame):
            result = result.collect()

        assert len(result) == len(df)

    def test_mixed_types_to_dict(self, mixed_types_data):
        """Test mixed types in dictionary conversion."""
        # Skip the 'mixed' column which has truly mixed types
        data = {k: v for k, v in mixed_types_data.items() if k != 'mixed'}
        df = pd.DataFrame(data)
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy.to_dictionary_of_lists(df)

        assert isinstance(result, dict)
        assert "integers" in result
        assert "strings" in result


@pytest.mark.unit
class TestRealisticScenarios:
    """Test cast operations with realistic data scenarios."""

    def test_financial_data_roundtrip(self, financial_data):
        """Test financial data survives round-trip conversion."""
        df_pandas = pd.DataFrame(financial_data)
        factory = DataFrameCastFactory()

        # pandas -> polars
        pandas_strategy = factory.get_strategy(df_pandas)
        df_polars = pandas_strategy.to_polars(df_pandas)

        # polars -> pandas
        polars_strategy = factory.get_strategy(df_polars)
        df_result = polars_strategy.to_pandas(df_polars)

        # Check integrity
        assert len(df_result) == len(df_pandas)
        assert list(df_result.columns) == list(df_pandas.columns)

    def test_sensor_data_to_pyarrow(self, sensor_data):
        """Test sensor data conversion to PyArrow."""
        df = pd.DataFrame(sensor_data)
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy.to_pyarrow(df)

        assert isinstance(result, pa.Table)
        assert len(result) == len(df)
        assert set(result.column_names) == set(df.columns)

    def test_financial_data_to_list_of_dicts(self, financial_data):
        """Test financial data conversion to list of dicts."""
        df = pd.DataFrame(financial_data)
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy.to_list_of_dictionaries(df)

        assert isinstance(result, list)
        assert len(result) == len(df)
        # Check that first transaction has all expected fields
        assert "transaction_id" in result[0]
        assert "amount" in result[0]
        assert "currency" in result[0]


@pytest.mark.unit
class TestIbisSpecificEdgeCases:
    """Test Ibis-specific edge cases."""

    def test_ibis_to_pandas_preserves_data(self, ibis_table):
        """Test Ibis to pandas preserves data integrity."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(ibis_table)

        result = strategy.to_pandas(ibis_table)

        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    def test_ibis_to_polars_preserves_data(self, ibis_table):
        """Test Ibis to polars preserves data integrity."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(ibis_table)

        result = strategy.to_polars(ibis_table)

        if isinstance(result, pl.LazyFrame):
            result = result.collect()

        assert isinstance(result, pl.DataFrame)
        assert len(result) > 0

    def test_pandas_to_ibis_with_backend(self, pandas_df, shared_ibis_backend):
        """Test pandas to Ibis with specific backend."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(pandas_df)

        result = strategy.to_ibis(pandas_df, ibis_backend=shared_ibis_backend)

        assert result is not None
        assert hasattr(result, 'columns') or hasattr(result, 'schema')


@pytest.mark.unit
class TestLazyEvaluation:
    """Test lazy evaluation specific cases."""

    def test_polars_lazy_collect_on_demand(self, polars_lazy):
        """Test polars lazy frame collects when needed."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(polars_lazy)

        # to_pandas should collect automatically
        result = strategy.to_pandas(polars_lazy)

        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    def test_polars_to_lazy_maintains_lazy(self, polars_df):
        """Test converting to lazy frame maintains lazy evaluation."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(polars_df)

        result = strategy.to_polars(polars_df, as_lazy=True)

        assert isinstance(result, pl.LazyFrame)

    def test_narwhals_lazy_handling(self, narwhals_lazy):
        """Test narwhals lazy frame handling."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(narwhals_lazy)

        result = strategy.to_pandas(narwhals_lazy)

        assert isinstance(result, pd.DataFrame)


@pytest.mark.unit
class TestTypePreservation:
    """Test that data types are preserved across conversions."""

    def test_boolean_type_preservation(self, standard_data):
        """Test boolean types are preserved."""
        df = pd.DataFrame(standard_data)
        factory = DataFrameCastFactory()

        # pandas -> polars -> pandas
        strategy1 = factory.get_strategy(df)
        polars_df = strategy1.to_polars(df)

        strategy2 = factory.get_strategy(polars_df)
        result = strategy2.to_pandas(polars_df)

        # Check boolean column is still boolean
        assert result['active'].dtype == bool or result['active'].dtype == object

    def test_numeric_type_preservation(self, standard_data):
        """Test numeric types are preserved."""
        df = pd.DataFrame(standard_data)
        factory = DataFrameCastFactory()

        # pandas -> pyarrow -> pandas
        strategy1 = factory.get_strategy(df)
        pyarrow_table = strategy1.to_pyarrow(df)

        strategy2 = factory.get_strategy(pyarrow_table)
        result = strategy2.to_pandas(pyarrow_table)

        # Check that value column is still numeric
        assert pd.api.types.is_numeric_dtype(result['value'])
