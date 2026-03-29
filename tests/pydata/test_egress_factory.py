"""Tests for DataFrameEgressFactory dispatch across backends."""
from __future__ import annotations

import polars as pl
import pytest

from mountainash.pydata.egress.egress_factory import DataFrameEgressFactory


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def polars_df():
    return pl.DataFrame({"name": ["Alice", "Bob"], "age": [30, 25]})


@pytest.fixture
def polars_lazy(polars_df):
    return polars_df.lazy()


@pytest.fixture
def pyarrow_table(polars_df):
    import pyarrow as pa
    return pa.table({"name": ["Alice", "Bob"], "age": [30, 25]})


@pytest.fixture
def narwhals_df(polars_df):
    import narwhals as nw
    return nw.from_native(polars_df)


@pytest.fixture
def ibis_table(polars_df):
    import ibis
    return ibis.memtable(polars_df)


# ---------------------------------------------------------------------------
# TestEgressFactoryDispatch
# ---------------------------------------------------------------------------


class TestEgressFactoryDispatch:
    def test_polars_dataframe_returns_strategy(self, polars_df):
        strategy = DataFrameEgressFactory.get_strategy(polars_df)
        assert strategy is not None

    def test_polars_lazyframe_returns_strategy(self, polars_lazy):
        strategy = DataFrameEgressFactory.get_strategy(polars_lazy)
        assert strategy is not None

    def test_pyarrow_table_returns_strategy(self, pyarrow_table):
        strategy = DataFrameEgressFactory.get_strategy(pyarrow_table)
        assert strategy is not None

    def test_narwhals_dataframe_returns_strategy(self, narwhals_df):
        strategy = DataFrameEgressFactory.get_strategy(narwhals_df)
        assert strategy is not None

    def test_ibis_table_returns_strategy(self, ibis_table):
        strategy = DataFrameEgressFactory.get_strategy(ibis_table)
        assert strategy is not None

    def test_polars_strategy_has_to_pandas(self, polars_df):
        strategy = DataFrameEgressFactory.get_strategy(polars_df)
        assert hasattr(strategy, "_to_pandas")

    def test_polars_strategy_has_to_list_of_dictionaries(self, polars_df):
        strategy = DataFrameEgressFactory.get_strategy(polars_df)
        assert hasattr(strategy, "_to_list_of_dictionaries")

    def test_polars_strategy_has_to_dictionary_of_lists(self, polars_df):
        strategy = DataFrameEgressFactory.get_strategy(polars_df)
        assert hasattr(strategy, "_to_dictionary_of_lists")

    def test_polars_strategy_has_to_index_methods(self, polars_df):
        strategy = DataFrameEgressFactory.get_strategy(polars_df)
        assert hasattr(strategy, "_to_index_of_dictionaries")
        assert hasattr(strategy, "_to_index_of_tuples")
        assert hasattr(strategy, "_to_index_of_named_tuples")

    def test_pandas_dataframe_raises(self):
        """Pandas DataFrames are not registered in the egress factory."""
        import pandas as pd
        df = pd.DataFrame({"name": ["Alice"], "age": [30]})
        with pytest.raises((ValueError, TypeError)):
            DataFrameEgressFactory.get_strategy(df)
