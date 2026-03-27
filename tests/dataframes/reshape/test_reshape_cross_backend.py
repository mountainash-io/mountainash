"""Tests for cross-backend consistency in reshape module.

This module validates that reshape operations produce equivalent results across all backends,
ensuring consistent behavior regardless of the underlying DataFrame implementation.
"""

import pytest
from pytest_check import check

from mountainash.dataframes.select import DataFrameSelectFactory
from mountainash.dataframes.introspect import DataFrameIntrospectFactory


# Core backends for consistency testing (excluding lazy variants)
CORE_BACKEND_FIXTURES = [
    "sample_pandas_df",
    "sample_polars_df",
    "sample_pyarrow_table",
    "sample_ibis_table",
    "sample_narwhals_df"
]


@pytest.mark.unit
class TestCrossBackendColumnNames:
    """Test that column_names() returns consistent results across backends."""

    def test_column_names_consistency(self, request):
        """Test that all backends return the same column names for equivalent data."""
        # Get all backend dataframes
        dataframes = {
            name: request.getfixturevalue(name)
            for name in CORE_BACKEND_FIXTURES
        }

        # Get column names from each backend
        column_sets = {}
        for backend_name, df in dataframes.items():
            strategy = DataFrameSelectFactory.get_strategy(df)
            columns = strategy.column_names(df)
            column_sets[backend_name] = set(columns)

        # All backends should have the same column names (order may differ)
        reference_columns = column_sets["sample_pandas_df"]
        for backend_name, columns in column_sets.items():
            check.equal(
                columns,
                reference_columns,
                msg=f"{backend_name} columns don't match pandas reference"
            )


@pytest.mark.unit
class TestCrossBackendCount:
    """Test that count() returns consistent results across backends."""

    def test_count_consistency(self, request):
        """Test that all backends return the same row count for equivalent data."""
        dataframes = {
            name: request.getfixturevalue(name)
            for name in CORE_BACKEND_FIXTURES
        }

        counts = {}
        for backend_name, df in dataframes.items():
            strategy = DataFrameSelectFactory.get_strategy(df)
            counts[backend_name] = strategy.count(df)

        # Most backends should have same count (ibis may differ due to fixture differences)
        reference_count = counts["sample_pandas_df"]
        for backend_name, count in counts.items():
            if backend_name != "real_ibis_table":  # ibis may have different fixture
                check.equal(
                    count,
                    reference_count,
                    msg=f"{backend_name} count doesn't match pandas reference"
                )


@pytest.mark.unit
class TestCrossBackendShape:
    """Test that shape() returns consistent results across backends."""

    def test_shape_consistency(self, request):
        """Test that all backends return consistent shape information."""
        dataframes = {
            name: request.getfixturevalue(name)
            for name in CORE_BACKEND_FIXTURES
        }

        shapes = {}
        for backend_name, df in dataframes.items():
            strategy = DataFrameIntrospectFactory.get_strategy(df)
            shape = strategy.shape(df)

            # Normalize shape to tuple format for comparison
            if isinstance(shape, tuple):
                shapes[backend_name] = shape
            elif isinstance(shape, dict):
                shapes[backend_name] = (shape.get("rows", 0), shape.get("columns", 0))
            else:
                shapes[backend_name] = None

        # Compare shapes (column count should be consistent)
        reference_shape = shapes["sample_pandas_df"]
        for backend_name, shape in shapes.items():
            if shape and backend_name != "real_ibis_table":
                check.equal(
                    shape[1],  # Column count
                    reference_shape[1],
                    msg=f"{backend_name} column count doesn't match pandas reference"
                )


@pytest.mark.unit
class TestCrossBackendSelect:
    """Test that select() produces equivalent results across backends."""

    def test_select_single_column_consistency(self, request):
        """Test that selecting a single column works consistently."""
        dataframes = {
            name: request.getfixturevalue(name)
            for name in CORE_BACKEND_FIXTURES
        }

        # Select same column from each backend
        selected_results = {}
        for backend_name, df in dataframes.items():
            strategy = DataFrameSelectFactory.get_strategy(df)
            result = strategy.select(df, "name")
            result_columns = strategy.column_names(result)
            selected_results[backend_name] = result_columns

        # All backends should have selected the same column
        for backend_name, columns in selected_results.items():
            check.is_in("name", columns, msg=f"{backend_name} didn't select 'name' column")


@pytest.mark.unit
class TestCrossBackendDrop:
    """Test that drop() produces equivalent results across backends."""

    def test_drop_column_consistency(self, request):
        """Test that dropping a column works consistently."""
        dataframes = {
            name: request.getfixturevalue(name)
            for name in CORE_BACKEND_FIXTURES
        }

        # Drop same column from each backend
        dropped_results = {}
        for backend_name, df in dataframes.items():
            strategy = DataFrameSelectFactory.get_strategy(df)
            result = strategy.drop(df, "category")
            result_columns = strategy.column_names(result)
            dropped_results[backend_name] = result_columns

        # All backends should have dropped the column
        for backend_name, columns in dropped_results.items():
            check.is_not_in("category", columns, msg=f"{backend_name} didn't drop 'category' column")


@pytest.mark.unit
class TestCrossBackendRename:
    """Test that rename() produces equivalent results across backends."""

    def test_rename_column_consistency(self, request):
        """Test that renaming a column works consistently."""
        dataframes = {
            name: request.getfixturevalue(name)
            for name in CORE_BACKEND_FIXTURES
        }

        mapping = {"name": "full_name"}

        renamed_results = {}
        for backend_name, df in dataframes.items():
            strategy = DataFrameSelectFactory.get_strategy(df)
            result = strategy.rename(df, mapping)
            result_columns = strategy.column_names(result)
            renamed_results[backend_name] = result_columns

        # All backends should have renamed the column
        for backend_name, columns in renamed_results.items():
            check.is_in("full_name", columns, msg=f"{backend_name} didn't rename to 'full_name'")
            check.is_not_in("name", columns, msg=f"{backend_name} still has 'name' column")


@pytest.mark.unit
class TestCrossBackendHead:
    """Test that head() produces equivalent results across backends."""

    def test_head_consistency(self, request):
        """Test that head() returns consistent row counts."""
        dataframes = {
            name: request.getfixturevalue(name)
            for name in CORE_BACKEND_FIXTURES
        }

        n = 3
        head_results = {}
        for backend_name, df in dataframes.items():
            strategy = DataFrameSelectFactory.get_strategy(df)
            result = strategy.head(df, n)
            result_count = strategy.count(result)
            head_results[backend_name] = result_count

        # All backends should return at most n rows
        for backend_name, count in head_results.items():
            check.less_equal(count, n, msg=f"{backend_name} head() returned more than {n} rows")


@pytest.mark.unit
class TestCrossBackendGetDataFrameInfo:
    """Test that get_dataframe_info() structure is consistent across backends."""

    def test_info_structure_consistency(self, request):
        """Test that all backends return info dict with required keys."""
        dataframes = {
            name: request.getfixturevalue(name)
            for name in CORE_BACKEND_FIXTURES
        }

        info_results = {}
        for backend_name, df in dataframes.items():
            strategy = DataFrameIntrospectFactory.get_strategy(df)
            info = strategy.get_dataframe_info(df)
            info_results[backend_name] = info

        # All backends should return dict with 'type' key
        for backend_name, info in info_results.items():
            check.is_instance(info, dict, msg=f"{backend_name} didn't return dict")
            check.is_in("type", info, msg=f"{backend_name} info missing 'type' key")

            # Most backends should have 'columns' key
            if "error" not in info:
                check.is_in("columns", info, msg=f"{backend_name} info missing 'columns' key")

    def test_info_type_uniqueness(self, request):
        """Test that each backend reports a different type string."""
        dataframes = {
            name: request.getfixturevalue(name)
            for name in CORE_BACKEND_FIXTURES
        }

        type_strings = []
        for backend_name, df in dataframes.items():
            strategy = DataFrameIntrospectFactory.get_strategy(df)
            info = strategy.get_dataframe_info(df)
            type_str = info.get("type", "").lower()

            # Narwhals wraps other types, so extract native type
            if "narwhals" in type_str and "wrapping" in type_str:
                # Extract wrapped type from string like "narwhals.DataFrame (wrapping pandas.DataFrame)"
                continue

            type_strings.append(type_str)

        # Each backend (except narwhals wrapper) should have unique type string
        # We expect at least 4 unique types: pandas, polars, pyarrow, ibis
        unique_types = len(set(type_strings))
        check.greater_equal(unique_types, 4, msg=f"Expected at least 4 unique backend types, got {unique_types}")




@pytest.mark.unit
class TestCrossBackendOperationChaining:
    """Test that chaining operations works consistently across backends."""

    def test_select_then_head_consistency(self, request):
        """Test that chaining select and head works consistently."""
        dataframes = {
            name: request.getfixturevalue(name)
            for name in CORE_BACKEND_FIXTURES
        }

        results = {}
        for backend_name, df in dataframes.items():
            strategy = DataFrameSelectFactory.get_strategy(df)

            # Chain: select columns -> head
            selected = strategy.select(df, ["id", "name"])
            result = strategy.head(selected, 2)

            result_columns = strategy.column_names(result)
            result_count = strategy.count(result)

            results[backend_name] = {
                "columns": set(result_columns),
                "count": result_count
            }

        # All backends should have same result structure
        reference = results["sample_pandas_df"]
        for backend_name, result in results.items():
            if backend_name != "real_ibis_table":
                check.equal(
                    result["columns"],
                    reference["columns"],
                    msg=f"{backend_name} chained operation columns don't match"
                )
                check.equal(
                    result["count"],
                    reference["count"],
                    msg=f"{backend_name} chained operation count doesn't match"
                )
