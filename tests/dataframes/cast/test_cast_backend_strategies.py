"""
Tests for backend-specific cast strategies.

This module tests each backend strategy's specific implementation details
and unique features.
"""

import pytest
import pandas as pd
import polars as pl
import pyarrow as pa
import ibis
import narwhals as nw

from mountainash.dataframes import DataFrameUtils
from mountainash.dataframes.cast import DataFrameCastFactory
from mountainash.dataframes.cast.cast_from_pandas import CastFromPandas
from mountainash.dataframes.cast.cast_from_polars import CastFromPolars
from mountainash.dataframes.cast.cast_from_polars_lazyframe import CastFromPolarsLazyFrame
from mountainash.dataframes.cast.cast_from_pyarrow import CastFromPyArrow
from mountainash.dataframes.cast.cast_from_ibis import CastFromIbis
from mountainash.dataframes.cast.cast_from_narwhals import CastFromNarwhals


@pytest.mark.unit
class TestPandasStrategy:
    """Test CastFromPandas strategy specific features."""

    def test_pandas_to_pandas_returns_same_object(self, pandas_df):
        """Test that pandas to pandas returns the same object."""
        strategy = CastFromPandas

        result = strategy.to_pandas(pandas_df)

        # Should return the same object
        assert result is pandas_df

    def test_pandas_to_polars(self, pandas_df):
        """Test pandas to polars conversion."""
        strategy = CastFromPandas

        result = strategy.to_polars(pandas_df)

        assert isinstance(result, pl.DataFrame)
        assert len(result) == len(pandas_df)
        assert result.columns == list(pandas_df.columns)

    def test_pandas_to_polars_lazy(self, pandas_df):
        """Test pandas to polars lazy conversion."""
        strategy = CastFromPandas

        result = strategy.to_polars(pandas_df, as_lazy=True)

        assert isinstance(result, pl.LazyFrame)

    def test_pandas_to_pyarrow(self, pandas_df):
        """Test pandas to pyarrow conversion."""
        strategy = CastFromPandas

        result = strategy.to_pyarrow(pandas_df)

        assert isinstance(result, pa.Table)
        assert len(result) == len(pandas_df)

    def test_pandas_to_narwhals(self, pandas_df):
        """Test pandas to narwhals conversion."""
        strategy = CastFromPandas

        result = strategy.to_narwhals(pandas_df)

        assert isinstance(result, nw.DataFrame)

    def test_pandas_to_dict_of_lists(self, pandas_df):
        """Test pandas to dictionary of lists conversion."""
        strategy = CastFromPandas

        result = strategy.to_dictionary_of_lists(pandas_df)

        assert isinstance(result, dict)
        assert set(result.keys()) == set(pandas_df.columns)
        assert all(isinstance(v, list) for v in result.values())

    def test_pandas_to_dict_of_series_pandas(self, pandas_df):
        """Test pandas to dict of pandas Series conversion."""
        strategy = CastFromPandas

        result = strategy.to_dictionary_of_series_pandas(pandas_df)

        assert isinstance(result, dict)
        assert all(isinstance(v, pd.Series) for v in result.values())

    def test_pandas_to_dict_of_series_polars(self, pandas_df):
        """Test pandas to dict of polars Series conversion."""
        strategy = CastFromPandas

        result = strategy.to_dictionary_of_series_polars(pandas_df)

        assert isinstance(result, dict)
        assert all(isinstance(v, pl.Series) for v in result.values())

    def test_pandas_to_list_of_dicts(self, pandas_df):
        """Test pandas to list of dictionaries conversion."""
        strategy = CastFromPandas

        result = strategy.to_list_of_dictionaries(pandas_df)

        assert isinstance(result, list)
        assert len(result) == len(pandas_df)
        assert all(isinstance(row, dict) for row in result)


@pytest.mark.unit
class TestPolarsStrategy:
    """Test CastFromPolars strategy specific features."""

    def test_polars_to_polars_returns_same_object(self, polars_df):
        """Test that polars to polars returns the same object."""
        strategy = CastFromPolars

        result = strategy.to_polars(polars_df)

        # Should return the same object
        assert result is polars_df

    def test_polars_to_polars_lazy(self, polars_df):
        """Test polars to lazy conversion."""
        strategy = CastFromPolars

        result = strategy.to_polars(polars_df, as_lazy=True)

        assert isinstance(result, pl.LazyFrame)

    def test_polars_to_pandas(self, polars_df):
        """Test polars to pandas conversion."""
        strategy = CastFromPolars

        result = strategy.to_pandas(polars_df)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(polars_df)

    def test_polars_to_pyarrow(self, polars_df):
        """Test polars to pyarrow conversion."""
        strategy = CastFromPolars

        result = strategy.to_pyarrow(polars_df)

        assert isinstance(result, pa.Table)
        assert len(result) == len(polars_df)

    def test_polars_to_narwhals(self, polars_df):
        """Test polars to narwhals conversion."""
        strategy = CastFromPolars

        result = strategy.to_narwhals(polars_df)

        assert isinstance(result, nw.DataFrame)

    def test_polars_to_dict_of_lists(self, polars_df):
        """Test polars to dictionary of lists conversion."""
        strategy = CastFromPolars

        result = strategy.to_dictionary_of_lists(polars_df)

        assert isinstance(result, dict)
        assert set(result.keys()) == set(polars_df.columns)

    def test_polars_to_list_of_dicts(self, polars_df):
        """Test polars to list of dictionaries conversion."""
        strategy = CastFromPolars

        result = strategy.to_list_of_dictionaries(polars_df)

        assert isinstance(result, list)
        assert len(result) == len(polars_df)


@pytest.mark.unit
class TestPolarsLazyStrategy:
    """Test CastFromPolarsLazyFrame strategy specific features."""

    def test_polars_lazy_to_polars(self, polars_lazy):
        """Test polars lazy to polars conversion preserves laziness."""
        strategy = CastFromPolarsLazyFrame

        result = strategy.to_polars(polars_lazy)

        # Default behavior (as_lazy=None) should preserve input type (lazy)
        assert isinstance(result, pl.LazyFrame)

    def test_polars_lazy_to_polars_lazy(self, polars_lazy):
        """Test polars lazy to lazy conversion."""
        strategy = CastFromPolarsLazyFrame

        result = strategy.to_polars(polars_lazy, as_lazy=True)

        assert isinstance(result, pl.LazyFrame)

    def test_polars_lazy_to_pandas(self, polars_lazy):
        """Test polars lazy to pandas conversion."""
        strategy = CastFromPolarsLazyFrame

        result = strategy.to_pandas(polars_lazy)

        assert isinstance(result, pd.DataFrame)

    def test_polars_lazy_to_pyarrow(self, polars_lazy):
        """Test polars lazy to pyarrow conversion."""
        strategy = CastFromPolarsLazyFrame

        result = strategy.to_pyarrow(polars_lazy)

        assert isinstance(result, pa.Table)


@pytest.mark.unit
class TestPyArrowStrategy:
    """Test CastFromPyArrow strategy specific features."""

    def test_pyarrow_to_pyarrow_returns_same_object(self, pyarrow_table):
        """Test that pyarrow to pyarrow returns the same object."""
        strategy = CastFromPyArrow

        result = strategy.to_pyarrow(pyarrow_table)

        # Should return the same object
        assert result is pyarrow_table

    def test_pyarrow_to_pandas(self, pyarrow_table):
        """Test pyarrow to pandas conversion."""
        strategy = CastFromPyArrow

        result = strategy.to_pandas(pyarrow_table)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(pyarrow_table)

    def test_pyarrow_to_polars(self, pyarrow_table):
        """Test pyarrow to polars conversion."""
        strategy = CastFromPyArrow

        result = strategy.to_polars(pyarrow_table)

        assert isinstance(result, pl.DataFrame)
        assert len(result) == len(pyarrow_table)

    def test_pyarrow_to_narwhals(self, pyarrow_table):
        """Test pyarrow to narwhals conversion."""
        strategy = CastFromPyArrow

        result = strategy.to_narwhals(pyarrow_table)

        assert isinstance(result, nw.DataFrame)

    def test_pyarrow_to_dict_of_lists(self, pyarrow_table):
        """Test pyarrow to dictionary of lists conversion."""
        strategy = CastFromPyArrow

        result = strategy.to_dictionary_of_lists(pyarrow_table)

        assert isinstance(result, dict)
        assert set(result.keys()) == set(pyarrow_table.column_names)

    def test_pyarrow_to_list_of_dicts(self, pyarrow_table):
        """Test pyarrow to list of dictionaries conversion."""
        strategy = CastFromPyArrow

        result = strategy.to_list_of_dictionaries(pyarrow_table)

        assert isinstance(result, list)
        assert len(result) == len(pyarrow_table)


@pytest.mark.unit
class TestIbisStrategy:
    """Test CastFromIbis strategy specific features."""

    def test_ibis_to_pandas(self, ibis_table):
        """Test ibis to pandas conversion."""
        strategy = CastFromIbis

        result = strategy.to_pandas(ibis_table)

        assert isinstance(result, pd.DataFrame)

    def test_ibis_to_polars(self, ibis_table):
        """Test ibis to polars conversion."""
        strategy = CastFromIbis

        result = strategy.to_polars(ibis_table)

        assert isinstance(result, (pl.DataFrame, pl.LazyFrame))

    def test_ibis_to_pyarrow(self, ibis_table):
        """Test ibis to pyarrow conversion."""
        strategy = CastFromIbis

        result = strategy.to_pyarrow(ibis_table)

        assert isinstance(result, pa.Table)

    def test_ibis_to_narwhals(self, ibis_table):
        """Test ibis to narwhals conversion."""
        strategy = CastFromIbis

        result = strategy.to_narwhals(ibis_table)

        assert isinstance(result, (nw.DataFrame, nw.LazyFrame))

    def test_ibis_to_dict_of_lists(self, ibis_table):
        """Test ibis to dictionary of lists conversion."""
        strategy = CastFromIbis

        result = strategy.to_dictionary_of_lists(ibis_table)

        assert isinstance(result, dict)

    def test_ibis_to_list_of_dicts(self, ibis_table):
        """Test ibis to list of dictionaries conversion."""
        strategy = CastFromIbis

        result = strategy.to_list_of_dictionaries(ibis_table)

        assert isinstance(result, list)


@pytest.mark.unit
class TestNarwhalsStrategy:
    """Test CastFromNarwhals strategy specific features."""

    def test_narwhals_to_pandas(self, narwhals_df):
        """Test narwhals to pandas conversion."""
        strategy = CastFromNarwhals

        result = strategy.to_pandas(narwhals_df)

        assert isinstance(result, pd.DataFrame)

    def test_narwhals_to_polars(self, narwhals_df):
        """Test narwhals to polars conversion."""
        strategy = CastFromNarwhals

        result = strategy.to_polars(narwhals_df)

        assert isinstance(result, (pl.DataFrame, pl.LazyFrame))

    def test_narwhals_to_pyarrow(self, narwhals_df):
        """Test narwhals to pyarrow conversion."""
        strategy = CastFromNarwhals

        result = strategy.to_pyarrow(narwhals_df)

        assert isinstance(result, pa.Table)

    def test_narwhals_to_narwhals(self, narwhals_df):
        """Test narwhals to narwhals conversion."""
        strategy = CastFromNarwhals

        result = strategy.to_narwhals(narwhals_df)

        # Should return the same object or a narwhals DataFrame
        assert isinstance(result, (nw.DataFrame, nw.LazyFrame))

    def test_narwhals_to_dict_of_lists(self, narwhals_df):
        """Test narwhals to dictionary of lists conversion."""
        strategy = CastFromNarwhals

        result = strategy.to_dictionary_of_lists(narwhals_df)

        assert isinstance(result, dict)

    def test_narwhals_to_list_of_dicts(self, narwhals_df):
        """Test narwhals to list of dictionaries conversion."""
        strategy = CastFromNarwhals

        result = strategy.to_list_of_dictionaries(narwhals_df)

        assert isinstance(result, list)


@pytest.mark.unit
class TestStrategyWithNulls:
    """Test all strategies handle null values correctly."""

    @pytest.mark.parametrize("backend_fixture", [
        "pandas_df", "polars_df", "pyarrow_table", "ibis_table", "narwhals_df"
    ])
    def test_null_handling_to_pandas(self, request, dataframes_with_nulls, backend_fixture):
        """Test that null values are preserved when converting to pandas."""
        # Create dataframe with nulls for the specific backend
        if backend_fixture == "pandas_df":
            df = pd.DataFrame(dataframes_with_nulls)
        elif backend_fixture == "polars_df":
            df = pl.DataFrame(dataframes_with_nulls)
        elif backend_fixture == "pyarrow_table":
            df = pa.table(dataframes_with_nulls)
        elif backend_fixture == "ibis_table":
            df = DataFrameUtils.create_ibis(dataframes_with_nulls)
        elif backend_fixture == "narwhals_df":
            df = nw.from_native(pd.DataFrame(dataframes_with_nulls))
        else:
            pytest.skip(f"Unknown backend fixture: {backend_fixture}")

        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy.to_pandas(df)

        # Check that nulls are preserved
        assert result['name'].isna().sum() > 0
        assert result['value'].isna().sum() > 0


@pytest.mark.unit
class TestStrategyErrorHandling:
    """Test that strategies handle errors appropriately."""

    def test_pandas_invalid_input(self):
        """Test CastFromPandas handles invalid input."""
        strategy = CastFromPandas

        with pytest.raises((ValueError, TypeError, AttributeError)):
            strategy.to_polars("not a dataframe")

    def test_polars_invalid_input(self):
        """Test CastFromPolars handles invalid input."""
        strategy = CastFromPolars

        with pytest.raises((ValueError, TypeError, AttributeError)):
            strategy.to_pandas([1, 2, 3])
