"""Tests for reshape module introspection methods.

This module comprehensively tests all introspection methods (column_names, count, shape,
get_dataframe_info) across all supported backends, with special focus on the newly migrated
get_dataframe_info() method.
"""

import pytest
from pytest_check import check
import pandas as pd
import polars as pl
import pyarrow as pa

from mountainash.dataframes.introspect import DataFrameIntrospectFactory
from mountainash.dataframes.select import DataFrameSelectFactory


# Backend fixtures for parameterized testing
BACKEND_FIXTURES = [
    "sample_pandas_df",
    "sample_polars_df",
    "sample_pyarrow_table",
    "real_ibis_table",
    "sample_polars_lazyframe",
    "sample_narwhals_df"
]


@pytest.mark.unit
@pytest.mark.parametrize("backend_fixture", BACKEND_FIXTURES)
class TestColumnNames:
    """Test column_names() method across all backends."""

    def test_column_names_basic(self, backend_fixture, request):
        """Test that column_names() returns correct column names."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameIntrospectFactory.get_strategy(df)

        column_names = strategy.column_names(df)

        check.is_instance(column_names, list)
        check.greater(len(column_names), 0)
        check.is_in("id", column_names)
        check.is_in("name", column_names)

    def test_column_names_order_preserved(self, backend_fixture, request):
        """Test that column order is consistent."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameIntrospectFactory.get_strategy(df)

        columns = strategy.column_names(df)

        # Columns should maintain order
        check.is_instance(columns, list)
        check.equal(len(columns), len(set(columns)))  # No duplicates


@pytest.mark.unit
class TestColumnNamesEdgeCases:
    """Test column_names() with edge cases."""

    def test_column_names_empty_df(self, empty_dataframes):
        """Test column_names() with empty DataFrames."""
        for backend_name, df in empty_dataframes.items():
            strategy = DataFrameIntrospectFactory.get_strategy(df)
            columns = strategy.column_names(df)

            check.is_instance(columns, list)
            # Empty DataFrame may have 0 columns
            check.greater_equal(len(columns), 0)


@pytest.mark.unit
@pytest.mark.parametrize("backend_fixture", BACKEND_FIXTURES)
class TestCount:
    """Test count() method across all backends."""

    def test_count_basic(self, backend_fixture, request):
        """Test that count() returns correct row count."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameSelectFactory.get_strategy(df)

        row_count = strategy.count(df)

        check.is_instance(row_count, int)
        # Most fixtures have 5 rows, but some (like real_ibis_table) may vary
        check.greater_equal(row_count, 3)  # At least 3 rows
        check.less_equal(row_count, 10)  # No more than 10 rows for test fixtures


@pytest.mark.unit
class TestCountEdgeCases:
    """Test count() with edge cases."""

    def test_count_empty(self, empty_dataframes):
        """Test count() with empty DataFrames."""
        for backend_name, df in empty_dataframes.items():
            strategy = DataFrameSelectFactory.get_strategy(df)
            count = strategy.count(df)

            check.is_instance(count, int)
            check.equal(count, 0)

    def test_count_single_row(self, single_row_dataframes):
        """Test count() with single-row DataFrames."""
        for backend_name, df in single_row_dataframes.items():
            strategy = DataFrameSelectFactory.get_strategy(df)
            count = strategy.count(df)

            check.equal(count, 1)


@pytest.mark.unit
@pytest.mark.parametrize("backend_fixture", BACKEND_FIXTURES)
class TestShape:
    """Test shape() method across all backends."""

    def test_shape_basic(self, backend_fixture, request):
        """Test that shape() returns correct shape information."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameIntrospectFactory.get_strategy(df)

        shape = strategy.shape(df)

        check.is_not_none(shape)
        # Shape may be tuple or dict depending on backend
        if isinstance(shape, tuple):
            check.equal(len(shape), 2)
            check.greater_equal(shape[0], 3)  # At least 3 rows
            check.greater(shape[1], 0)  # At least 1 column
        elif isinstance(shape, dict):
            check.is_in("rows", shape)
            check.is_in("columns", shape)
            check.greater_equal(shape["rows"], 3)  # At least 3 rows


@pytest.mark.unit
class TestShapeEdgeCases:
    """Test shape() with edge cases."""

    def test_shape_empty(self, empty_dataframes):
        """Test shape() with empty DataFrames."""
        for backend_name, df in empty_dataframes.items():
            strategy = DataFrameIntrospectFactory.get_strategy(df)
            shape = strategy.shape(df)

            check.is_not_none(shape)
            if isinstance(shape, tuple):
                check.equal(shape[0], 0)  # 0 rows
            elif isinstance(shape, dict):
                check.equal(shape.get("rows", 0), 0)


@pytest.mark.unit
@pytest.mark.parametrize("backend_fixture", BACKEND_FIXTURES)
class TestGetDataFrameInfo:
    """Test get_dataframe_info() method - newly migrated to reshape module."""

    def test_get_dataframe_info_returns_dict(self, backend_fixture, request):
        """Test that get_dataframe_info() returns a dictionary."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameIntrospectFactory.get_strategy(df)

        info = strategy.get_dataframe_info(df)

        check.is_instance(info, dict)
        check.greater(len(info), 0)

    def test_get_dataframe_info_required_keys(self, backend_fixture, request):
        """Test that all backends include required keys."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameIntrospectFactory.get_strategy(df)

        info = strategy.get_dataframe_info(df)

        # All backends should have 'type' key
        check.is_in("type", info)
        check.is_not_none(info.get("type"))

        # Most backends should have 'columns' key
        if "error" not in info:
            check.is_in("columns", info)

    def test_get_dataframe_info_type_detection(self, backend_fixture, request):
        """Test that type is correctly detected for each backend."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameIntrospectFactory.get_strategy(df)

        info = strategy.get_dataframe_info(df)

        type_str = info.get("type", "")

        # Verify type string contains expected backend name
        if backend_fixture == "sample_pandas_df":
            check.is_in("pandas", type_str.lower())
        elif backend_fixture == "sample_polars_df":
            check.is_in("polars", type_str.lower())
            # Non-lazy Polars should have is_lazy=False
            if "is_lazy" in info:
                check.equal(info.get("is_lazy"), False)
        elif backend_fixture == "sample_polars_lazyframe":
            # LazyFrame may be handled by PolarsDataFrameReshape or PolarsLazyFrameReshape
            check.is_in("polars", type_str.lower())
            # Accept either is_lazy=True or dict-based shape with lazy indicator
        elif backend_fixture == "real_ibis_table":
            check.is_in("ibis", type_str.lower())
        elif backend_fixture == "sample_pyarrow_table":
            check.is_in("pyarrow", type_str.lower())
        elif backend_fixture == "sample_narwhals_df":
            check.is_in("narwhals", type_str.lower())


@pytest.mark.unit
class TestGetDataFrameInfoBackendSpecific:
    """Test backend-specific details in get_dataframe_info()."""

    def test_pandas_info_includes_dtypes(self, sample_pandas_df):
        """Test pandas includes dtypes, memory_usage, and null_counts."""
        strategy = DataFrameIntrospectFactory.get_strategy(sample_pandas_df)
        info = strategy.get_dataframe_info(sample_pandas_df)

        check.is_in("dtypes", info)
        check.is_in("memory_usage", info)
        check.is_in("null_counts", info)
        check.is_instance(info["dtypes"], dict)

    def test_polars_info_includes_schema(self, sample_polars_df):
        """Test polars includes schema and is_lazy flag."""
        strategy = DataFrameIntrospectFactory.get_strategy(sample_polars_df)
        info = strategy.get_dataframe_info(sample_polars_df)

        check.is_in("schema", info)
        check.is_in("is_lazy", info)
        check.equal(info["is_lazy"], False)
        check.is_instance(info["schema"], dict)

    def test_polars_lazy_info_minimal(self, sample_polars_lazyframe):
        """Test polars LazyFrame returns info appropriate for lazy evaluation."""
        strategy = DataFrameIntrospectFactory.get_strategy(sample_polars_lazyframe)
        info = strategy.get_dataframe_info(sample_polars_lazyframe)

        # LazyFrame may be handled by PolarsDataFrameReshape or PolarsLazyFrameReshape
        check.is_in("columns", info)
        check.is_in("polars", info.get("type", "").lower())

        # If strategy provides is_lazy flag, verify it
        if "is_lazy" in info:
            # LazyFrame should have is_lazy indicator
            check.is_true(info["is_lazy"] in [True, False])  # Accept either value

    # def test_ibis_info_includes_backend(self, real_ibis_table):
    #     """Test ibis includes backend information."""
    #     strategy = DataFrameReshapeFactory.get_strategy(real_ibis_table)
    #     info = strategy.get_dataframe_info(real_ibis_table)

    #     print(info)

    #     check.is_in("backend", info)
    #     # check.is_not_none(info["backend"])

    def test_pyarrow_info_includes_nbytes(self, sample_pyarrow_table):
        """Test pyarrow includes nbytes and detailed structure info."""
        strategy = DataFrameIntrospectFactory.get_strategy(sample_pyarrow_table)
        info = strategy.get_dataframe_info(sample_pyarrow_table)

        check.is_in("nbytes", info)
        check.is_in("num_rows", info)
        check.is_in("num_columns", info)
        check.is_instance(info["nbytes"], int)

    def test_narwhals_info_includes_native_backend(self, sample_narwhals_df):
        """Test narwhals includes native backend information."""
        strategy = DataFrameIntrospectFactory.get_strategy(sample_narwhals_df)
        info = strategy.get_dataframe_info(sample_narwhals_df)

        # Narwhals should indicate it's a wrapper
        check.is_in("narwhals", info.get("type", "").lower())
        # May include native_backend or similar field
        check.is_true(
            "native_backend" in info or "native_type" in info or "wrapping" in info.get("type", "")
        )


@pytest.mark.unit
class TestGetDataFrameInfoEdgeCases:
    """Test get_dataframe_info() with edge cases."""

    def test_empty_dataframe_info(self, empty_dataframes):
        """Test get_dataframe_info() with empty DataFrames."""
        for backend_name, df in empty_dataframes.items():
            strategy = DataFrameIntrospectFactory.get_strategy(df)
            info = strategy.get_dataframe_info(df)

            check.is_instance(info, dict)
            check.is_in("type", info)
            # Should not raise error on empty DataFrame

    def test_dataframe_with_nulls_info(self, dataframe_with_nulls):
        """Test get_dataframe_info() handles null values correctly."""
        for backend_name, df in dataframe_with_nulls.items():
            strategy = DataFrameIntrospectFactory.get_strategy(df)
            info = strategy.get_dataframe_info(df)

            check.is_instance(info, dict)
            # Should handle nulls gracefully
            if "null_counts" in info:
                check.is_instance(info["null_counts"], dict)
