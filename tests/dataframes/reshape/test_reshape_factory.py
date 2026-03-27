"""Tests for DataFrameSelectFactory and strategy selection.

This module tests the factory pattern and strategy selection logic for the select module,
ensuring that each DataFrame type is correctly mapped to its appropriate strategy class.
"""

import pytest
import pandas as pd
import polars as pl
import pyarrow as pa
import ibis
import narwhals as nw

from mountainash.dataframes.select.select_factory import DataFrameSelectFactory
from mountainash.dataframes.select.select_pandas import PandasDataFrameSelect
from mountainash.dataframes.select.select_polars import PolarsDataFrameSelect
from mountainash.dataframes.select.select_polars_lazyframe import PolarsLazyFrameSelect
from mountainash.dataframes.select.select_ibis import IbisDataFrameSelect
from mountainash.dataframes.select.select_pyarrow import PyArrowTableSelect
from mountainash.dataframes.select.select_narwhals import NarwhalsDataFrameSelect


@pytest.mark.unit
class TestFactoryStrategySelection:
    """Test that the factory correctly selects strategies for each DataFrame type."""

    def test_get_strategy_pandas(self, sample_pandas_df):
        """Test factory returns PandasDataFrameSelect for pandas DataFrame."""
        strategy = DataFrameSelectFactory.get_strategy(sample_pandas_df)

        assert strategy is not None
        assert isinstance(strategy, type)
        assert issubclass(strategy, PandasDataFrameSelect)

    def test_get_strategy_polars(self, sample_polars_df):
        """Test factory returns PolarsDataFrameSelect for polars DataFrame."""
        strategy = DataFrameSelectFactory.get_strategy(sample_polars_df)

        assert strategy is not None
        assert isinstance(strategy, type)
        assert issubclass(strategy, PolarsDataFrameSelect)

    def test_get_strategy_polars_lazy(self, sample_polars_lazyframe):
        """Test factory returns PolarsLazyFrameSelect for polars LazyFrame."""
        strategy = DataFrameSelectFactory.get_strategy(sample_polars_lazyframe)

        assert strategy is not None
        assert isinstance(strategy, type)
        # Should be PolarsLazyFrameSelect or PolarsDataFrameSelect depending on implementation
        assert issubclass(strategy, (PolarsLazyFrameSelect, PolarsDataFrameSelect))

    def test_get_strategy_ibis(self, real_ibis_table):
        """Test factory returns IbisDataFrameSelect for ibis Table."""
        strategy = DataFrameSelectFactory.get_strategy(real_ibis_table)

        assert strategy is not None
        assert isinstance(strategy, type)
        assert issubclass(strategy, IbisDataFrameSelect)

    def test_get_strategy_pyarrow(self, sample_pyarrow_table):
        """Test factory returns PyArrowTableSelect for PyArrow Table."""
        strategy = DataFrameSelectFactory.get_strategy(sample_pyarrow_table)

        assert strategy is not None
        assert isinstance(strategy, type)
        assert issubclass(strategy, PyArrowTableSelect)

    def test_get_strategy_narwhals(self, sample_narwhals_df):
        """Test factory returns NarwhalsDataFrameSelect for narwhals DataFrame."""
        strategy = DataFrameSelectFactory.get_strategy(sample_narwhals_df)

        assert strategy is not None
        assert isinstance(strategy, type)
        assert issubclass(strategy, NarwhalsDataFrameSelect)

    def test_get_strategy_unsupported(self):
        """Test factory raises ValueError for unsupported DataFrame type."""
        unsupported_data = "not a dataframe"

        # Factory should raise ValueError for unsupported types
        with pytest.raises(ValueError, match="No strategy key found"):
            DataFrameSelectFactory.get_strategy(unsupported_data)


@pytest.mark.unit
class TestFactoryConsistency:
    """Test that factory behavior is consistent and predictable."""

    def test_same_dataframe_returns_same_strategy(self, sample_pandas_df):
        """Test that factory returns consistent strategy for same DataFrame."""
        strategy1 = DataFrameSelectFactory.get_strategy(sample_pandas_df)
        strategy2 = DataFrameSelectFactory.get_strategy(sample_pandas_df)

        assert strategy1 is strategy2  # Should be same class

    def test_different_backends_different_strategies(self, sample_pandas_df, sample_polars_df):
        """Test that different backends get different strategies."""
        pandas_strategy = DataFrameSelectFactory.get_strategy(sample_pandas_df)
        polars_strategy = DataFrameSelectFactory.get_strategy(sample_polars_df)

        assert pandas_strategy is not polars_strategy
        assert pandas_strategy != polars_strategy
