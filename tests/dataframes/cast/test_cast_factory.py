"""
Tests for DataFrameCastFactory.

This module tests the factory's strategy selection and public API.
Cast logic is tested in backend-specific and cross-backend test files.
"""

from __future__ import annotations

import pytest
import pandas as pd
import polars as pl
import pyarrow as pa
import ibis
import narwhals as nw

from mountainash.dataframes.cast import DataFrameCastFactory
from mountainash.dataframes.cast.cast_from_pandas import CastFromPandas
from mountainash.dataframes.cast.cast_from_polars import CastFromPolars
from mountainash.dataframes.cast.cast_from_polars_lazyframe import CastFromPolarsLazyFrame
from mountainash.dataframes.cast.cast_from_pyarrow import CastFromPyArrow
from mountainash.dataframes.cast.cast_from_ibis import CastFromIbis
from mountainash.dataframes.cast.cast_from_narwhals import CastFromNarwhals
from mountainash.dataframes.cast.cast_from_narwhals_lazyframe import CastFromNarwhalsLazyFrame


@pytest.mark.unit
class TestFactoryStrategySelection:
    """Test that factory selects the correct strategy for each DataFrame type."""

    def test_factory_selects_pandas_strategy(self, pandas_df):
        """Test factory selects CastFromPandas for pandas DataFrame."""
        factory = DataFrameCastFactory()

        strategy = factory.get_strategy(pandas_df)
        assert strategy == CastFromPandas

    def test_factory_selects_polars_strategy(self, polars_df):
        """Test factory selects CastFromPolars for Polars DataFrame."""
        factory = DataFrameCastFactory()

        strategy = factory.get_strategy(polars_df)
        assert strategy == CastFromPolars

    def test_factory_selects_polars_lazy_strategy(self, polars_lazy):
        """Test factory selects CastFromPolarsLazyFrame for Polars LazyFrame."""
        factory = DataFrameCastFactory()

        strategy = factory.get_strategy(polars_lazy)
        assert strategy == CastFromPolarsLazyFrame

    def test_factory_selects_pyarrow_strategy(self, pyarrow_table):
        """Test factory selects CastFromPyArrow for PyArrow Table."""
        factory = DataFrameCastFactory()

        strategy = factory.get_strategy(pyarrow_table)
        assert strategy == CastFromPyArrow

    def test_factory_selects_ibis_strategy(self, ibis_table):
        """Test factory selects CastFromIbis for Ibis Table."""
        factory = DataFrameCastFactory()

        strategy = factory.get_strategy(ibis_table)
        assert strategy == CastFromIbis

    def test_factory_selects_narwhals_strategy(self, narwhals_df):
        """Test factory selects CastFromNarwhals for Narwhals DataFrame."""
        factory = DataFrameCastFactory()

        strategy = factory.get_strategy(narwhals_df)
        assert strategy == CastFromNarwhals

    def test_factory_selects_narwhals_lazy_strategy(self, narwhals_lazy):
        """Test factory selects CastFromNarwhalsLazyFrame for Narwhals LazyFrame."""
        factory = DataFrameCastFactory()

        strategy = factory.get_strategy(narwhals_lazy)
        assert strategy == CastFromNarwhalsLazyFrame


@pytest.mark.unit
class TestFactoryPublicAPI:
    """Test factory's public API methods for different cast operations."""

    def test_to_pandas_api(self, polars_df):
        """Test public to_pandas() API."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(polars_df)

        result = strategy.to_pandas(polars_df)

        # Verify result is a pandas DataFrame
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 5
        assert list(result.columns) == ["id", "name", "category", "value", "active"]

    def test_to_polars_api(self, pandas_df):
        """Test public to_polars() API."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(pandas_df)

        result = strategy.to_polars(pandas_df)

        # Verify result is a Polars DataFrame
        assert isinstance(result, pl.DataFrame)
        assert len(result) == 5

    def test_to_polars_lazy_api(self, pandas_df):
        """Test public to_polars() API with as_lazy=True."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(pandas_df)

        result = strategy.to_polars(pandas_df, as_lazy=True)

        # Verify result is a Polars LazyFrame
        assert isinstance(result, pl.LazyFrame)

    def test_to_pyarrow_api(self, pandas_df):
        """Test public to_pyarrow() API."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(pandas_df)

        result = strategy.to_pyarrow(pandas_df)

        # Verify result is a PyArrow Table
        assert isinstance(result, pa.Table)
        assert len(result) == 5

    def test_to_ibis_api(self, pandas_df):
        """Test public to_ibis() API."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(pandas_df)

        result = strategy.to_ibis(pandas_df)

        # Verify result is an Ibis Table
        assert result is not None
        assert hasattr(result, 'columns') or hasattr(result, 'schema')

    def test_to_narwhals_api(self, pandas_df):
        """Test public to_narwhals() API."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(pandas_df)

        result = strategy.to_narwhals(pandas_df)

        # Verify result is a Narwhals DataFrame
        assert isinstance(result, nw.DataFrame)

    def test_to_dict_of_lists_api(self, pandas_df):
        """Test public to_dictionary_of_lists() API."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(pandas_df)

        result = strategy.to_dictionary_of_lists(pandas_df)

        # Verify result is a dictionary
        assert isinstance(result, dict)
        assert "id" in result
        assert isinstance(result["id"], list)
        assert len(result["id"]) == 5

    def test_to_list_of_dicts_api(self, pandas_df):
        """Test public to_list_of_dictionaries() API."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(pandas_df)

        result = strategy.to_list_of_dictionaries(pandas_df)

        # Verify result is a list of dictionaries
        assert isinstance(result, list)
        assert len(result) == 5
        assert isinstance(result[0], dict)
        assert "id" in result[0]


@pytest.mark.unit
class TestFactoryErrorHandling:
    """Test factory error handling for unsupported types and edge cases."""

    def test_factory_handles_unknown_type(self):
        """Test factory behavior with unsupported DataFrame type."""
        # A list is not a supported DataFrame type
        unsupported = [{"id": 1, "name": "Alice"}]

        factory = DataFrameCastFactory()

        # Factory should raise an error for unsupported types
        with pytest.raises((ValueError, TypeError, KeyError, AttributeError)):
            strategy = factory.get_strategy(unsupported)

    def test_factory_handles_none_input(self):
        """Test factory behavior with None input."""
        factory = DataFrameCastFactory()

        # Should raise an error
        with pytest.raises((ValueError, TypeError, AttributeError)):
            strategy = factory.get_strategy(None)

    def test_factory_handles_string_input(self):
        """Test factory behavior with string input."""
        factory = DataFrameCastFactory()

        # Should raise an error
        with pytest.raises((ValueError, TypeError, KeyError, AttributeError)):
            strategy = factory.get_strategy("not a dataframe")


@pytest.mark.unit
class TestFactoryConsistency:
    """Test factory behaves consistently across instances and calls."""

    def test_factory_instances_independent(self, pandas_df):
        """Test that separate factory instances work independently."""
        factory1 = DataFrameCastFactory()
        factory2 = DataFrameCastFactory()

        strategy1 = factory1.get_strategy(pandas_df)
        strategy2 = factory2.get_strategy(pandas_df)

        # Both should select the same strategy
        assert strategy1 == strategy2

    def test_factory_multiple_calls_consistent(self, pandas_df):
        """Test that multiple calls to same factory are consistent."""
        factory = DataFrameCastFactory()

        result1 = factory.get_strategy(pandas_df)
        result2 = factory.get_strategy(pandas_df)

        assert result1 == result2

    def test_factory_same_strategy_for_same_type(self, pandas_df):
        """Test factory selects same strategy for same DataFrame type."""
        factory = DataFrameCastFactory()

        # Create another pandas DataFrame
        df2 = pd.DataFrame({"x": [1, 2, 3]})

        strategy1 = factory.get_strategy(pandas_df)
        strategy2 = factory.get_strategy(df2)

        # Both pandas DataFrames should get same strategy
        assert strategy1 == strategy2


@pytest.mark.unit
class TestFactoryLazyLoading:
    """Test factory's lazy loading behavior."""

    def test_factory_lazy_loading(self, pandas_df):
        """Test that factory uses lazy loading for strategies."""
        # Create fresh factory
        factory = DataFrameCastFactory()

        # First call should trigger lazy loading
        strategy1 = factory.get_strategy(pandas_df)
        assert strategy1 is not None

        # Second call should use cached strategy
        strategy2 = factory.get_strategy(pandas_df)
        assert strategy2 == strategy1

    def test_factory_handles_multiple_backends(self, pandas_df, polars_df, ibis_table):
        """Test factory correctly handles multiple backend types."""
        factory = DataFrameCastFactory()

        pandas_strategy = factory.get_strategy(pandas_df)
        polars_strategy = factory.get_strategy(polars_df)
        ibis_strategy = factory.get_strategy(ibis_table)

        # Each backend should get its own strategy
        assert pandas_strategy == CastFromPandas
        assert polars_strategy == CastFromPolars
        assert ibis_strategy == CastFromIbis


@pytest.mark.unit
class TestFactoryCrossBackendAPI:
    """Test factory API works across all backends."""

    @pytest.mark.parametrize("backend_name", [
        "pandas", "polars", "pyarrow", "ibis", "narwhals"
    ])
    def test_to_pandas_across_backends(self, all_backend_dataframes, backend_name):
        """Test to_pandas() works from all backends."""
        df = all_backend_dataframes[backend_name]
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy.to_pandas(df)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 5

    @pytest.mark.parametrize("backend_name", [
        "pandas", "polars", "pyarrow", "ibis", "narwhals"
    ])
    def test_to_polars_across_backends(self, all_backend_dataframes, backend_name):
        """Test to_polars() works from all backends."""
        df = all_backend_dataframes[backend_name]
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy.to_polars(df)

        assert isinstance(result, (pl.DataFrame, pl.LazyFrame))

    @pytest.mark.parametrize("backend_name", [
        "pandas", "polars", "pyarrow", "ibis", "narwhals"
    ])
    def test_to_pyarrow_across_backends(self, all_backend_dataframes, backend_name):
        """Test to_pyarrow() works from all backends."""
        df = all_backend_dataframes[backend_name]
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy.to_pyarrow(df)

        assert isinstance(result, pa.Table)
        assert len(result) == 5
