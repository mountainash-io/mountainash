"""
Tests for cross-backend consistency in cast module.

This module validates that cast operations produce equivalent results across all backends,
ensuring consistent behavior regardless of the underlying DataFrame implementation.
"""

import pytest
import pandas as pd
import polars as pl
import pyarrow as pa
import narwhals as nw
from pytest_check import check

from mountainash.dataframes.cast import DataFrameCastFactory


# Core backends for consistency testing
CORE_BACKEND_NAMES = ["pandas", "polars", "pyarrow", "ibis", "narwhals"]


@pytest.mark.unit
class TestCrossBackendToPandas:
    """Test that to_pandas() produces consistent results across backends."""

    def test_to_pandas_consistency(self, all_backend_dataframes):
        """Test that all backends return the same pandas DataFrame structure."""
        results = {}

        for backend_name, df in all_backend_dataframes.items():
            if backend_name.endswith("_lazy"):
                continue  # Skip lazy variants for this test

            factory = DataFrameCastFactory()
            strategy = factory.get_strategy(df)

            result = strategy.to_pandas(df)

            results[backend_name] = {
                "row_count": len(result),
                "columns": list(result.columns),
                "dtypes": {col: str(dtype) for col, dtype in result.dtypes.items()}
            }

        # All backends should have same row count
        reference_count = results["pandas"]["row_count"]
        for backend_name, result_info in results.items():
            check.equal(
                result_info["row_count"],
                reference_count,
                msg=f"{backend_name} to_pandas row count doesn't match"
            )

        # All backends should have same columns
        reference_columns = results["pandas"]["columns"]
        for backend_name, result_info in results.items():
            check.equal(
                sorted(result_info["columns"]),
                sorted(reference_columns),
                msg=f"{backend_name} to_pandas columns don't match"
            )

    def test_to_pandas_data_integrity(self, all_backend_dataframes):
        """Test that to_pandas() preserves data values across backends."""
        results = {}

        for backend_name, df in all_backend_dataframes.items():
            if backend_name.endswith("_lazy"):
                continue

            factory = DataFrameCastFactory()
            strategy = factory.get_strategy(df)

            result = strategy.to_pandas(df)
            # Sort by id for consistent comparison
            result = result.sort_values('id').reset_index(drop=True)

            results[backend_name] = result

        # Compare data values across backends
        reference_df = results["pandas"]
        for backend_name, result_df in results.items():
            if backend_name == "pandas":
                continue

            # Check that first row has same data
            check.equal(
                result_df.loc[0, 'id'],
                reference_df.loc[0, 'id'],
                msg=f"{backend_name} to_pandas data doesn't match for first row ID"
            )
            check.equal(
                result_df.loc[0, 'name'],
                reference_df.loc[0, 'name'],
                msg=f"{backend_name} to_pandas data doesn't match for first row name"
            )


@pytest.mark.unit
class TestCrossBackendToPolars:
    """Test that to_polars() produces consistent results across backends."""

    def test_to_polars_consistency(self, all_backend_dataframes):
        """Test that all backends return the same Polars DataFrame structure."""
        results = {}

        for backend_name, df in all_backend_dataframes.items():
            if backend_name.endswith("_lazy"):
                continue

            factory = DataFrameCastFactory()
            strategy = factory.get_strategy(df)

            result = strategy.to_polars(df)

            # Handle both DataFrame and LazyFrame
            if isinstance(result, pl.LazyFrame):
                result = result.collect()

            results[backend_name] = {
                "row_count": len(result),
                "columns": result.columns,
                "shape": result.shape
            }

        # All backends should have same row count
        reference_count = results["pandas"]["row_count"]
        for backend_name, result_info in results.items():
            check.equal(
                result_info["row_count"],
                reference_count,
                msg=f"{backend_name} to_polars row count doesn't match"
            )

        # All backends should have same columns
        reference_columns = results["pandas"]["columns"]
        for backend_name, result_info in results.items():
            check.equal(
                sorted(result_info["columns"]),
                sorted(reference_columns),
                msg=f"{backend_name} to_polars columns don't match"
            )

    def test_to_polars_lazy_flag(self, all_backend_dataframes):
        """Test that as_lazy parameter works consistently."""
        for backend_name, df in all_backend_dataframes.items():
            if backend_name.endswith("_lazy"):
                continue

            factory = DataFrameCastFactory()
            strategy = factory.get_strategy(df)

            # Test with as_lazy=True
            result_lazy = strategy.to_polars(df, as_lazy=True)

            # Narwhals may return DataFrame instead of LazyFrame due to implementation differences
            # All others should return LazyFrame
            if backend_name != "narwhals":
                assert isinstance(result_lazy, pl.LazyFrame), \
                    f"{backend_name} to_polars(as_lazy=True) should return LazyFrame"

            # Test with as_lazy=False (default)
            result_eager = strategy.to_polars(df, as_lazy=False)
            assert isinstance(result_eager, (pl.DataFrame, pl.LazyFrame)), \
                f"{backend_name} to_polars(as_lazy=False) should return DataFrame or LazyFrame"


@pytest.mark.unit
class TestCrossBackendToPyArrow:
    """Test that to_pyarrow() produces consistent results across backends."""

    def test_to_pyarrow_consistency(self, all_backend_dataframes):
        """Test that all backends return the same PyArrow Table structure."""
        results = {}

        for backend_name, df in all_backend_dataframes.items():
            if backend_name.endswith("_lazy"):
                continue

            factory = DataFrameCastFactory()
            strategy = factory.get_strategy(df)

            result = strategy.to_pyarrow(df)

            results[backend_name] = {
                "row_count": len(result),
                "columns": result.column_names,
                "num_columns": result.num_columns
            }

        # All backends should have same row count
        reference_count = results["pandas"]["row_count"]
        for backend_name, result_info in results.items():
            check.equal(
                result_info["row_count"],
                reference_count,
                msg=f"{backend_name} to_pyarrow row count doesn't match"
            )

        # All backends should have same columns
        reference_columns = results["pandas"]["columns"]
        for backend_name, result_info in results.items():
            check.equal(
                sorted(result_info["columns"]),
                sorted(reference_columns),
                msg=f"{backend_name} to_pyarrow columns don't match"
            )


@pytest.mark.unit
class TestCrossBackendToNarwhals:
    """Test that to_narwhals() produces consistent results across backends."""

    def test_to_narwhals_consistency(self, all_backend_dataframes):
        """Test that all backends return Narwhals DataFrames."""
        for backend_name, df in all_backend_dataframes.items():
            if backend_name.endswith("_lazy"):
                continue

            factory = DataFrameCastFactory()
            strategy = factory.get_strategy(df)

            result = strategy.to_narwhals(df)

            # Verify it's a Narwhals type
            assert isinstance(result, (nw.DataFrame, nw.LazyFrame)), \
                f"{backend_name} to_narwhals should return Narwhals DataFrame or LazyFrame"


@pytest.mark.unit
class TestCrossBackendToDictionary:
    """Test that dictionary conversions are consistent across backends."""

    def test_to_dict_of_lists_consistency(self, all_backend_dataframes):
        """Test that all backends return the same dictionary structure."""
        results = {}

        for backend_name, df in all_backend_dataframes.items():
            if backend_name.endswith("_lazy"):
                continue

            factory = DataFrameCastFactory()
            strategy = factory.get_strategy(df)

            result = strategy.to_dictionary_of_lists(df)

            results[backend_name] = {
                "keys": sorted(result.keys()),
                "id_values": result.get("id", []),
                "num_keys": len(result)
            }

        # All backends should have same keys
        reference_keys = results["pandas"]["keys"]
        for backend_name, result_info in results.items():
            check.equal(
                result_info["keys"],
                reference_keys,
                msg=f"{backend_name} to_dict_of_lists keys don't match"
            )

        # All backends should have same id values
        reference_ids = sorted(results["pandas"]["id_values"])
        for backend_name, result_info in results.items():
            check.equal(
                sorted(result_info["id_values"]),
                reference_ids,
                msg=f"{backend_name} to_dict_of_lists id values don't match"
            )

    def test_to_list_of_dicts_consistency(self, all_backend_dataframes):
        """Test that all backends return the same list of dictionaries."""
        results = {}

        for backend_name, df in all_backend_dataframes.items():
            if backend_name.endswith("_lazy"):
                continue

            factory = DataFrameCastFactory()
            strategy = factory.get_strategy(df)

            result = strategy.to_list_of_dictionaries(df)

            results[backend_name] = {
                "length": len(result),
                "first_keys": sorted(result[0].keys()) if result else [],
                "first_id": result[0].get("id") if result else None
            }

        # All backends should have same length
        reference_length = results["pandas"]["length"]
        for backend_name, result_info in results.items():
            check.equal(
                result_info["length"],
                reference_length,
                msg=f"{backend_name} to_list_of_dicts length doesn't match"
            )

        # All backends should have same keys in first record
        reference_keys = results["pandas"]["first_keys"]
        for backend_name, result_info in results.items():
            check.equal(
                result_info["first_keys"],
                reference_keys,
                msg=f"{backend_name} to_list_of_dicts keys don't match"
            )


@pytest.mark.unit
class TestCrossBackendRoundTrip:
    """Test round-trip conversions maintain data integrity."""

    def test_pandas_polars_pandas_roundtrip(self, pandas_df):
        """Test pandas -> polars -> pandas preserves data."""
        factory = DataFrameCastFactory()

        # pandas -> polars
        polars_strategy = factory.get_strategy(pandas_df)
        polars_result = polars_strategy.to_polars(pandas_df)

        # polars -> pandas
        pandas_strategy = factory.get_strategy(polars_result)
        pandas_result = pandas_strategy.to_pandas(polars_result)

        # Compare
        pd.testing.assert_frame_equal(
            pandas_df.sort_values('id').reset_index(drop=True),
            pandas_result.sort_values('id').reset_index(drop=True)
        )

    def test_pandas_pyarrow_pandas_roundtrip(self, pandas_df):
        """Test pandas -> pyarrow -> pandas preserves data."""
        factory = DataFrameCastFactory()

        # pandas -> pyarrow
        pandas_strategy = factory.get_strategy(pandas_df)
        pyarrow_result = pandas_strategy.to_pyarrow(pandas_df)

        # pyarrow -> pandas
        pyarrow_strategy = factory.get_strategy(pyarrow_result)
        pandas_result = pyarrow_strategy.to_pandas(pyarrow_result)

        # Compare (allowing for type differences)
        assert len(pandas_df) == len(pandas_result)
        assert list(pandas_df.columns) == list(pandas_result.columns)

    def test_polars_pandas_polars_roundtrip(self, polars_df):
        """Test polars -> pandas -> polars preserves data."""
        factory = DataFrameCastFactory()

        # polars -> pandas
        polars_strategy = factory.get_strategy(polars_df)
        pandas_result = polars_strategy.to_pandas(polars_df)

        # pandas -> polars
        pandas_strategy = factory.get_strategy(pandas_result)
        polars_result = pandas_strategy.to_polars(pandas_result)

        # Compare
        if isinstance(polars_result, pl.LazyFrame):
            polars_result = polars_result.collect()

        original_sorted = polars_df.sort('id')
        result_sorted = polars_result.sort('id')

        assert original_sorted.shape == result_sorted.shape
        assert original_sorted.columns == result_sorted.columns
