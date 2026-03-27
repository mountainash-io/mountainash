"""
Tests for Ibis-specific cast operations.

This module tests Ibis-specific features including backend management,
table naming, lazy evaluation, schema preservation, and cross-backend compatibility.
"""

import pytest
import pandas as pd
import polars as pl
import pyarrow as pa
import ibis
import narwhals as nw

from mountainash.dataframes import DataFrameUtils
from mountainash.dataframes.cast import DataFrameCastFactory
from mountainash.dataframes.cast.cast_from_ibis import CastFromIbis


@pytest.mark.unit
class TestIbisBackendManagement:
    """Test Ibis backend creation and management."""

    def test_pandas_to_ibis_creates_backend(self, pandas_df):
        """Test that pandas to ibis creates a valid Ibis backend."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(pandas_df)

        result = strategy.to_ibis(pandas_df)

        # Verify it's an Ibis table with a backend
        assert result is not None
        assert hasattr(result, 'get_backend')
        backend = result.get_backend()
        assert backend is not None

    def test_pandas_to_ibis_with_specific_backend(self, pandas_df, shared_ibis_backend):
        """Test pandas to ibis with a specific backend instance."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(pandas_df)

        result = strategy.to_ibis(pandas_df, ibis_backend=shared_ibis_backend)

        # Verify it uses the provided backend
        assert result is not None
        assert result.get_backend() == shared_ibis_backend

    def test_polars_to_ibis_creates_backend(self, polars_df):
        """Test that polars to ibis creates a valid Ibis backend."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(polars_df)

        result = strategy.to_ibis(polars_df)

        assert result is not None
        backend = result.get_backend()
        assert backend is not None

    def test_pyarrow_to_ibis_creates_backend(self, pyarrow_table):
        """Test that pyarrow to ibis creates a valid Ibis backend."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(pyarrow_table)

        result = strategy.to_ibis(pyarrow_table)

        assert result is not None
        backend = result.get_backend()
        assert backend is not None

    def test_ibis_to_ibis_preserves_backend(self, ibis_table):
        """Test that ibis to ibis preserves the same backend."""
        original_backend = ibis_table.get_backend()

        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(ibis_table)

        result = strategy.to_ibis(ibis_table)

        # Should preserve the same backend
        assert result.get_backend() == original_backend


@pytest.mark.unit
class TestIbisTableNaming:
    """Test Ibis table naming options."""

    def test_ibis_with_custom_tablename(self, pandas_df, shared_ibis_backend):
        """Test creating Ibis table with custom table name."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(pandas_df)

        result = strategy.to_ibis(
            pandas_df,
            ibis_backend=shared_ibis_backend,
            tablename="custom_table_name"
        )

        assert result is not None
        # Table should exist in backend
        assert hasattr(result, 'get_name')

    def test_ibis_with_tablename_prefix(self, pandas_df, shared_ibis_backend):
        """Test creating Ibis table with tablename prefix."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(pandas_df)

        result = strategy.to_ibis(
            pandas_df,
            ibis_backend=shared_ibis_backend,
            tablename_prefix="test_prefix_"
        )

        assert result is not None

    def test_ibis_with_temp_flag(self, pandas_df, shared_ibis_backend):
        """Test creating temporary Ibis table."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(pandas_df)

        result = strategy.to_ibis(
            pandas_df,
            ibis_backend=shared_ibis_backend,
            temp=True
        )

        assert result is not None

    def test_ibis_with_overwrite_flag(self, pandas_df, shared_ibis_backend):
        """Test creating Ibis table with overwrite."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(pandas_df)

        # Create table first
        result1 = strategy.to_ibis(
            pandas_df,
            ibis_backend=shared_ibis_backend,
            tablename="overwrite_test"
        )

        # Create again with overwrite
        result2 = strategy.to_ibis(
            pandas_df,
            ibis_backend=shared_ibis_backend,
            tablename="overwrite_test",
            overwrite=True
        )

        assert result2 is not None


@pytest.mark.unit
class TestIbisFromBackends:
    """Test converting different backends to Ibis."""

    def test_pandas_to_ibis_preserves_schema(self, pandas_df):
        """Test pandas to ibis preserves column names and types."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(pandas_df)

        result = strategy.to_ibis(pandas_df)

        # Verify columns are preserved
        assert set(result.columns) == set(pandas_df.columns)

    def test_polars_to_ibis_preserves_schema(self, polars_df):
        """Test polars to ibis preserves column names and types."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(polars_df)

        result = strategy.to_ibis(polars_df)

        # Verify columns are preserved
        assert set(result.columns) == set(polars_df.columns)

    def test_polars_lazy_to_ibis(self, polars_lazy):
        """Test polars lazy to ibis conversion."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(polars_lazy)

        result = strategy.to_ibis(polars_lazy)

        assert result is not None
        assert hasattr(result, 'columns')

    def test_pyarrow_to_ibis_preserves_schema(self, pyarrow_table):
        """Test pyarrow to ibis preserves column names."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(pyarrow_table)

        result = strategy.to_ibis(pyarrow_table)

        # Verify columns are preserved
        assert set(result.columns) == set(pyarrow_table.column_names)

    def test_narwhals_to_ibis(self, narwhals_df):
        """Test narwhals to ibis conversion."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(narwhals_df)

        result = strategy.to_ibis(narwhals_df)

        assert result is not None
        assert hasattr(result, 'columns')


@pytest.mark.unit
class TestIbisToBackends:
    """Test converting Ibis to different backends."""

    def test_ibis_to_pandas_execution(self, ibis_table):
        """Test ibis to pandas executes the query and returns data."""
        strategy = CastFromIbis

        result = strategy.to_pandas(ibis_table)

        # Should be a materialized pandas DataFrame
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0
        assert len(result.columns) > 0

    def test_ibis_to_polars_execution(self, ibis_table):
        """Test ibis to polars executes the query and returns data."""
        strategy = CastFromIbis

        result = strategy.to_polars(ibis_table)

        # Should be a materialized polars DataFrame
        if isinstance(result, pl.LazyFrame):
            result = result.collect()

        assert isinstance(result, pl.DataFrame)
        assert len(result) > 0
        assert len(result.columns) > 0

    def test_ibis_to_polars_lazy(self, ibis_table):
        """Test ibis to polars with lazy evaluation."""
        strategy = CastFromIbis

        result = strategy.to_polars(ibis_table, as_lazy=True)

        # May return LazyFrame depending on implementation
        assert isinstance(result, (pl.DataFrame, pl.LazyFrame))

    def test_ibis_to_pyarrow_execution(self, ibis_table):
        """Test ibis to pyarrow executes the query and returns data."""
        strategy = CastFromIbis

        result = strategy.to_pyarrow(ibis_table)

        # Should be a materialized PyArrow Table
        assert isinstance(result, pa.Table)
        assert len(result) > 0
        assert result.num_columns > 0

    def test_ibis_to_narwhals_execution(self, ibis_table):
        """Test ibis to narwhals executes the query and returns data."""
        strategy = CastFromIbis

        result = strategy.to_narwhals(ibis_table)

        # Should be a narwhals DataFrame
        assert isinstance(result, (nw.DataFrame, nw.LazyFrame))


@pytest.mark.unit
class TestIbisSchemaPreservation:
    """Test that Ibis conversions preserve schema information."""

    def test_column_names_preserved_pandas_to_ibis(self, pandas_df):
        """Test column names are preserved in pandas -> ibis conversion."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(pandas_df)

        result = strategy.to_ibis(pandas_df)

        assert sorted(result.columns) == sorted(pandas_df.columns)

    def test_column_names_preserved_ibis_to_pandas(self, ibis_table):
        """Test column names are preserved in ibis -> pandas conversion."""
        original_columns = sorted(ibis_table.columns)

        strategy = CastFromIbis
        result = strategy.to_pandas(ibis_table)

        assert sorted(result.columns) == original_columns

    def test_data_integrity_roundtrip_pandas_ibis_pandas(self, pandas_df):
        """Test data integrity in pandas -> ibis -> pandas roundtrip."""
        factory = DataFrameCastFactory()

        # pandas -> ibis
        pandas_strategy = factory.get_strategy(pandas_df)
        ibis_result = pandas_strategy.to_ibis(pandas_df)

        # ibis -> pandas
        ibis_strategy = factory.get_strategy(ibis_result)
        pandas_result = ibis_strategy.to_pandas(ibis_result)

        # Check data integrity
        assert len(pandas_result) == len(pandas_df)
        assert sorted(pandas_result.columns) == sorted(pandas_df.columns)

        # Sort both for comparison
        pandas_df_sorted = pandas_df.sort_values('id').reset_index(drop=True)
        pandas_result_sorted = pandas_result.sort_values('id').reset_index(drop=True)

        # Check first row data matches
        assert pandas_df_sorted.loc[0, 'id'] == pandas_result_sorted.loc[0, 'id']
        assert pandas_df_sorted.loc[0, 'name'] == pandas_result_sorted.loc[0, 'name']

    def test_data_integrity_roundtrip_polars_ibis_polars(self, polars_df):
        """Test data integrity in polars -> ibis -> polars roundtrip."""
        factory = DataFrameCastFactory()

        # polars -> ibis
        polars_strategy = factory.get_strategy(polars_df)
        ibis_result = polars_strategy.to_ibis(polars_df)

        # ibis -> polars
        ibis_strategy = factory.get_strategy(ibis_result)
        polars_result = ibis_strategy.to_polars(ibis_result)

        if isinstance(polars_result, pl.LazyFrame):
            polars_result = polars_result.collect()

        # Check data integrity
        assert len(polars_result) == len(polars_df)
        assert sorted(polars_result.columns) == sorted(polars_df.columns)


@pytest.mark.unit
class TestIbisEdgeCases:
    """Test Ibis edge cases and error scenarios."""

    def test_empty_dataframe_to_ibis(self, empty_dataframes):
        """Test converting empty DataFrame to Ibis."""
        pandas_empty = empty_dataframes["pandas"]
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(pandas_empty)

        result = strategy.to_ibis(pandas_empty)

        assert result is not None

    def test_ibis_empty_to_pandas(self, shared_ibis_backend):
        """Test converting empty Ibis table to pandas."""
        # Create empty Ibis table
        empty_data = pd.DataFrame()
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(empty_data)

        ibis_empty = strategy.to_ibis(empty_data, ibis_backend=shared_ibis_backend)

        # Convert back to pandas
        result = CastFromIbis.to_pandas(ibis_empty)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    def test_single_row_to_ibis(self, single_row_data):
        """Test converting single-row DataFrame to Ibis."""
        df = pd.DataFrame(single_row_data)
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy.to_ibis(df)

        assert result is not None
        assert len(result.columns) > 0

    def test_single_column_to_ibis(self, single_column_data):
        """Test converting single-column DataFrame to Ibis."""
        df = pd.DataFrame(single_column_data)
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy.to_ibis(df)

        assert result is not None
        assert len(result.columns) == 1

    def test_nulls_to_ibis(self, dataframes_with_nulls):
        """Test converting DataFrame with nulls to Ibis."""
        df = pd.DataFrame(dataframes_with_nulls)
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy.to_ibis(df)

        assert result is not None

        # Convert back to check nulls preserved
        result_pandas = CastFromIbis.to_pandas(result)
        assert result_pandas['name'].isna().sum() > 0

    def test_special_chars_to_ibis(self, special_characters_data):
        """Test converting DataFrame with special characters to Ibis."""
        df = pd.DataFrame(special_characters_data)
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy.to_ibis(df)

        assert result is not None
        # Column names should be preserved or sanitized
        assert len(result.columns) == len(df.columns)

    def test_large_dataframe_to_ibis(self, large_dataframe_data):
        """Test converting large DataFrame to Ibis."""
        df = pd.DataFrame(large_dataframe_data)
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy.to_ibis(df)

        assert result is not None

        # Convert back and check row count
        result_pandas = CastFromIbis.to_pandas(result)
        assert len(result_pandas) == 1000


@pytest.mark.unit
class TestIbisLazyEvaluation:
    """Test Ibis lazy evaluation characteristics."""

    def test_ibis_table_is_lazy(self, ibis_table):
        """Test that Ibis tables are lazy by default."""
        # Ibis tables should not execute until materialized
        assert hasattr(ibis_table, 'execute') or hasattr(ibis_table, 'to_pandas')

    def test_ibis_to_pandas_materializes(self, ibis_table):
        """Test that converting to pandas materializes the Ibis query."""
        strategy = CastFromIbis

        result = strategy.to_pandas(ibis_table)

        # Should be materialized
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    def test_ibis_operations_remain_lazy(self, ibis_table):
        """Test that Ibis operations remain lazy until materialization."""
        # Filter operation should still be lazy
        filtered = ibis_table.filter(ibis_table['id'] > 2)

        # Should still be an Ibis expression
        assert hasattr(filtered, 'execute') or hasattr(filtered, 'to_pandas')

        # Materialize to pandas
        result = CastFromIbis.to_pandas(filtered)
        assert isinstance(result, pd.DataFrame)
        # Should have fewer rows due to filter
        assert len(result) < 5


@pytest.mark.unit
class TestIbisDictionaryConversions:
    """Test Ibis dictionary conversion methods."""

    def test_ibis_to_dict_of_lists(self, ibis_table):
        """Test converting Ibis table to dictionary of lists."""
        strategy = CastFromIbis

        result = strategy.to_dictionary_of_lists(ibis_table)

        assert isinstance(result, dict)
        assert len(result) > 0
        assert all(isinstance(v, list) for v in result.values())

    def test_ibis_to_list_of_dicts(self, ibis_table):
        """Test converting Ibis table to list of dictionaries."""
        strategy = CastFromIbis

        result = strategy.to_list_of_dictionaries(ibis_table)

        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(item, dict) for item in result)

    def test_ibis_to_dict_preserves_columns(self, ibis_table):
        """Test dictionary conversion preserves column names."""
        original_columns = set(ibis_table.columns)

        strategy = CastFromIbis
        result = strategy.to_dictionary_of_lists(ibis_table)

        assert set(result.keys()) == original_columns


@pytest.mark.unit
class TestIbisCrossBackendCompatibility:
    """Test Ibis compatibility with different source backends."""

    @pytest.mark.parametrize("backend_name", ["pandas", "polars", "pyarrow", "narwhals"])
    def test_all_backends_to_ibis(self, all_backend_dataframes, backend_name):
        """Test that all backends can convert to Ibis."""
        df = all_backend_dataframes[backend_name]
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy.to_ibis(df)

        assert result is not None
        assert hasattr(result, 'columns')
        assert len(result.columns) == 5  # Standard data has 5 columns

    def test_all_to_ibis_produce_same_schema(self, all_backend_dataframes):
        """Test that converting from all backends to Ibis produces same schema."""
        ibis_results = {}

        for backend_name in ["pandas", "polars", "pyarrow", "narwhals"]:
            df = all_backend_dataframes[backend_name]
            factory = DataFrameCastFactory()
            strategy = factory.get_strategy(df)

            ibis_table = strategy.to_ibis(df)
            ibis_results[backend_name] = set(ibis_table.columns)

        # All should have same columns
        reference_columns = ibis_results["pandas"]
        for backend_name, columns in ibis_results.items():
            assert columns == reference_columns, \
                f"{backend_name} to Ibis columns don't match pandas"


@pytest.mark.unit
class TestIbisRealisticScenarios:
    """Test Ibis with realistic data scenarios."""

    def test_financial_data_to_ibis(self, financial_data):
        """Test financial data conversion to Ibis."""
        df = pd.DataFrame(financial_data)
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy.to_ibis(df)

        assert result is not None

        # Verify can query back
        result_pandas = CastFromIbis.to_pandas(result)
        assert len(result_pandas) == len(df)
        assert 'transaction_id' in result_pandas.columns
        assert 'amount' in result_pandas.columns

    def test_sensor_data_to_ibis_with_operations(self, sensor_data):
        """Test sensor data to Ibis with operations."""
        df = pd.DataFrame(sensor_data)
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        ibis_table = strategy.to_ibis(df)

        # Perform an operation (filter)
        filtered = ibis_table.filter(ibis_table['temperature'] > 22.0)

        # Materialize
        result = CastFromIbis.to_pandas(filtered)

        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0
        assert all(result['temperature'] > 22.0)
