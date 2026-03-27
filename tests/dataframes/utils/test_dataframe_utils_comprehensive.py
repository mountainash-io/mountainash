"""Comprehensive parameterized testing for DataFrameUtils public interface.

This module provides extensive cross-backend testing for all public methods in DataFrameUtils,
using parameterized tests to validate consistency across pandas, polars, pyarrow, ibis, and
narwhals backends. Tests cover the complete user-facing API including DataFrame creation,
conversion, utilities, and operations.
"""

import pytest
from pytest_check import check
import pandas as pd
import polars as pl
import pyarrow as pa
import ibis
import narwhals as nw
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Any, Union, Optional
import time
import tracemalloc

from mountainash.dataframes import DataFrameUtils
from mountainash.dataframes.constants import CONST_DATAFRAME_FRAMEWORK
from mountainash.dataframes.typing import SupportedDataFrames

import ibis
ibis.set_backend("polars")

# ===================================
# Test Data Fixtures for Matrix Testing
# ===================================

@pytest.fixture
def sample_data_clean() -> Dict[str, List[Any]]:
    """Clean test data with consistent types and lengths across all backends."""
    return {
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "value": [10.5, 20.0, 30.5, 40.0, 50.5],
        "active": [True, False, True, True, False],
        "created_date": [
            date(2023, 1, 1),
            date(2023, 1, 2),
            date(2023, 1, 3),
            date(2023, 1, 4),
            date(2023, 1, 5)
        ]
    }

@pytest.fixture
def sample_data_join_left() -> Dict[str, List[Any]]:
    """Left DataFrame for join operations."""
    return {
        "id": [1, 2, 3, 4],
        "left_value": ["A", "B", "C", "D"],
        "score": [10, 20, 30, 40]
    }

@pytest.fixture
def sample_data_join_right() -> Dict[str, List[Any]]:
    """Right DataFrame for join operations."""
    return {
        "id": [2, 3, 4, 5],
        "right_value": ["X", "Y", "Z", "W"],
        "rating": [1.5, 2.5, 3.5, 4.5]
    }

@pytest.fixture
def sample_data_complex_types() -> Dict[str, List[Any]]:
    """Test data with complex types and edge cases."""
    return {
        "integers": [1, 2, 3, None],
        "floats": [1.1, 2.2, None, 4.4],
        "strings": ["test", None, "hello", ""],
        "booleans": [True, False, None, True],
        "decimals": [Decimal("1.1"), Decimal("2.2"), None, Decimal("4.4")]
    }


# ===================================
# Backend Configuration and Parametrization
# ===================================

# All supported DataFrame types for comprehensive testing
DATAFRAME_BACKENDS = [
    CONST_DATAFRAME_FRAMEWORK.PANDAS,
    CONST_DATAFRAME_FRAMEWORK.POLARS,
    CONST_DATAFRAME_FRAMEWORK.PYARROW,
    CONST_DATAFRAME_FRAMEWORK.IBIS
]

# Backends supported for conversion (includes narwhals)
CONVERSION_BACKENDS = DATAFRAME_BACKENDS + [CONST_DATAFRAME_FRAMEWORK.NARWHALS]

# Conversion matrix: test conversions between all backend pairs
CONVERSION_MATRIX = [
    (source, target) for source in DATAFRAME_BACKENDS
    for target in CONVERSION_BACKENDS
]

# Join operations to test
JOIN_OPERATIONS = ["inner_join", "left_join", "outer_join"]

# Utility operations to test across backends
UTILITY_OPERATIONS = [
    "column_names", "count", "head", "get_first_row_as_dict",
    "to_list_of_dictionaries", "to_dictionary_of_lists"
]


# ===================================
# DataFrame Creation Tests (Matrix Parametrized)
# ===================================

@pytest.mark.parametrize("backend", DATAFRAME_BACKENDS)
@pytest.mark.unit
def test_create_dataframe_basic(sample_data_clean, backend):
    """Test basic DataFrame creation across all backends."""

    # Test creation with valid backend
    df = DataFrameUtils.create_dataframe(
        sample_data_clean,
        dataframe_framework=backend
    )

    # Validate creation was successful
    check.is_not_none(df)

    # Get column names to verify structure
    col_names = DataFrameUtils.column_names(df)
    expected_cols = list(sample_data_clean.keys())
    check.equal(sorted(col_names), sorted(expected_cols))

    # Validate row count
    row_count = DataFrameUtils.count(df)
    check.equal(row_count, len(sample_data_clean["id"]))

    # Test specific backend types
    if backend == CONST_DATAFRAME_FRAMEWORK.PANDAS:
        check.is_instance(df, pd.DataFrame)
    elif backend == CONST_DATAFRAME_FRAMEWORK.POLARS:
        check.is_instance(df, pl.DataFrame)
    elif backend == CONST_DATAFRAME_FRAMEWORK.PYARROW:
        check.is_instance(df, pa.Table)
    elif backend == CONST_DATAFRAME_FRAMEWORK.IBIS:
        # Ibis returns Table type
        check.is_true(hasattr(df, 'schema'))
    # Note: narwhals backend not supported by create_dataframe method


@pytest.mark.parametrize("backend", DATAFRAME_BACKENDS)
@pytest.mark.unit
def test_create_dataframe_edge_cases(sample_data_complex_types, backend):
    """Test DataFrame creation with complex types and null values."""

    df = DataFrameUtils.create_dataframe(
        sample_data_complex_types,
        dataframe_framework=backend
    )

    check.is_not_none(df)

    # Verify all columns created despite nulls
    col_names = DataFrameUtils.column_names(df)
    expected_cols = list(sample_data_complex_types.keys())
    check.equal(sorted(col_names), sorted(expected_cols))

    # Verify row count matches input
    row_count = DataFrameUtils.count(df)
    check.equal(row_count, len(sample_data_complex_types["integers"]))


@pytest.mark.unit
def test_create_dataframe_invalid_backend(sample_data_clean):
    """Test error handling for invalid backend specification."""

    with pytest.raises(ValueError, match="Unsupported dataframe framework"):
        DataFrameUtils.create_dataframe(
            sample_data_clean,
            dataframe_framework="invalid_backend"
        )


# ===================================
# DataFrame Conversion Tests (Matrix Parametrized)
# ===================================

@pytest.mark.parametrize("source_backend,target_backend", CONVERSION_MATRIX)
@pytest.mark.integration
def test_dataframe_conversion_matrix(sample_data_clean, source_backend, target_backend):
    """Test DataFrame conversion between all backend pairs."""

    # Create source DataFrame
    source_df = DataFrameUtils.create_dataframe(
        sample_data_clean,
        dataframe_framework=source_backend
    )

    # Convert to target backend
    target_df = DataFrameUtils.cast_dataframe(
        source_df,
        dataframe_framework=target_backend
    )

    check.is_not_none(target_df)

    # Verify structure preservation
    source_cols = DataFrameUtils.column_names(source_df)
    target_cols = DataFrameUtils.column_names(target_df)
    check.equal(sorted(source_cols), sorted(target_cols))

    # Verify row count preservation
    source_count = DataFrameUtils.count(source_df)
    target_count = DataFrameUtils.count(target_df)
    check.equal(source_count, target_count)

    # Verify data content preservation (basic check)
    source_first_row = DataFrameUtils.get_first_row_as_dict(source_df)
    target_first_row = DataFrameUtils.get_first_row_as_dict(target_df)

    # Compare basic values (allowing for type conversions)
    check.equal(source_first_row["id"], target_first_row["id"])
    check.equal(source_first_row["name"], target_first_row["name"])


@pytest.mark.parametrize("backend", DATAFRAME_BACKENDS)
@pytest.mark.unit
def test_specific_conversion_methods(sample_data_clean, backend):
    """Test specific conversion methods (to_pandas, to_polars, etc.)."""

    # Create source DataFrame
    source_df = DataFrameUtils.create_dataframe(
        sample_data_clean,
        dataframe_framework=backend
    )

    # Test conversion to pandas
    pandas_df = DataFrameUtils.to_pandas(source_df)
    check.is_instance(pandas_df, pd.DataFrame)


    check.equal(DataFrameUtils.count(pandas_df), len(sample_data_clean["id"]))

    # Test conversion to polars
    # Note: Ibis is inherently lazy, so with as_lazy=None (default),
    # it will return a LazyFrame. Other backends return eager DataFrames.
    polars_df = DataFrameUtils.to_polars(source_df)
    if backend == CONST_DATAFRAME_FRAMEWORK.IBIS:
        check.is_instance(polars_df, (pl.DataFrame, pl.LazyFrame))
    else:
        check.is_instance(polars_df, pl.DataFrame)
    check.equal(DataFrameUtils.count(polars_df), len(sample_data_clean["id"]))

    # Test conversion to pyarrow
    pyarrow_table = DataFrameUtils.to_pyarrow(source_df)
    check.is_instance(pyarrow_table, pa.Table)
    check.equal(DataFrameUtils.count(pyarrow_table), len(sample_data_clean["id"]))

    # Test conversion to narwhals
    narwhals_df = DataFrameUtils.to_narwhals(source_df)
    check.is_not_none(narwhals_df)
    check.equal(DataFrameUtils.count(narwhals_df), len(sample_data_clean["id"]))


# ===================================
# DataFrame Utility Operations Tests (Matrix Parametrized)
# ===================================

@pytest.mark.parametrize("backend", DATAFRAME_BACKENDS)
@pytest.mark.parametrize("operation", UTILITY_OPERATIONS)
@pytest.mark.unit
def test_utility_operations_matrix(sample_data_clean, backend, operation):
    """Test utility operations across all backends."""

    # Create DataFrame
    df = DataFrameUtils.create_dataframe(
        sample_data_clean,
        dataframe_framework=backend
    )

    # Execute operation and validate
    if operation == "column_names":
        result = DataFrameUtils.column_names(df)
        check.is_instance(result, list)
        check.equal(len(result), len(sample_data_clean.keys()))
        check.is_in("id", result)
        check.is_in("name", result)

    elif operation == "count":
        result = DataFrameUtils.count(df)
        check.is_instance(result, int)
        check.equal(result, len(sample_data_clean["id"]))

    elif operation == "head":
        result = DataFrameUtils.head(df, n=3)
        check.is_not_none(result)
        head_count = DataFrameUtils.count(result)
        check.equal(head_count, 3)

    elif operation == "get_first_row_as_dict":
        result = DataFrameUtils.get_first_row_as_dict(df)
        check.is_instance(result, dict)
        check.is_in("id", result)
        check.equal(result["id"], 1)
        check.equal(result["name"], "Alice")

    elif operation == "to_list_of_dictionaries":
        result = DataFrameUtils.to_list_of_dictionaries(df)
        check.is_instance(result, list)
        check.equal(len(result), len(sample_data_clean["id"]))
        check.is_instance(result[0], dict)
        check.is_in("id", result[0])

    elif operation == "to_dictionary_of_lists":
        result = DataFrameUtils.to_dictionary_of_lists(df)
        check.is_instance(result, dict)
        check.is_in("id", result)
        check.is_instance(result["id"], list)
        check.equal(len(result["id"]), len(sample_data_clean["id"]))


# ===================================
# DataFrame Join Operations Tests (Matrix Parametrized)
# ===================================

@pytest.mark.parametrize("backend", DATAFRAME_BACKENDS)
@pytest.mark.parametrize("join_type", JOIN_OPERATIONS)
@pytest.mark.integration
def test_join_operations_matrix(sample_data_join_left, sample_data_join_right, backend, join_type):
    """Test join operations across all backends."""

    # Create left and right DataFrames
    left_df = DataFrameUtils.create_dataframe(
        sample_data_join_left,
        dataframe_framework=backend
    )

    right_df = DataFrameUtils.create_dataframe(
        sample_data_join_right,
        dataframe_framework=backend
    )

    # Execute join operation
    if join_type == "inner_join":
        result_df = DataFrameUtils.inner_join(
            left_df, right_df,
            ["id"]
        )
        # Inner join should have 3 rows (ids 2, 3, 4)
        expected_count = 3

    elif join_type == "left_join":
        result_df = DataFrameUtils.left_join(
            left_df, right_df,
            ["id"]
        )
        # Left join should have 4 rows (all from left)
        expected_count = 4

    elif join_type == "outer_join":
        result_df = DataFrameUtils.outer_join(
            left_df, right_df,
            ["id"]
        )
        # Outer join should have 5 rows (ids 1, 2, 3, 4, 5)
        expected_count = 5

    # Validate join result
    check.is_not_none(result_df)

    result_count = DataFrameUtils.count(result_df)
    check.equal(result_count, expected_count)

    # Verify columns from both sides exist
    result_cols = DataFrameUtils.column_names(result_df)
    check.is_in("left_value", result_cols)
    check.is_in("right_value", result_cols)


# ===================================
# Performance and Regression Tests
# ===================================

@pytest.mark.parametrize("backend", DATAFRAME_BACKENDS)
@pytest.mark.performance
def test_creation_performance_regression(sample_data_clean, backend):
    """Test DataFrame creation performance to catch regressions."""

    # Measure creation time
    start_time = time.time()

    df = DataFrameUtils.create_dataframe(
        sample_data_clean,
        dataframe_framework=backend
    )

    creation_time = time.time() - start_time

    # Basic validation
    check.is_not_none(df)

    # Performance assertion (generous threshold for CI)
    check.is_true(creation_time < 5.0, f"Creation took {creation_time:.3f}s for {backend}")


@pytest.mark.parametrize("source_backend,target_backend", [
    (CONST_DATAFRAME_FRAMEWORK.POLARS, CONST_DATAFRAME_FRAMEWORK.PANDAS),
    (CONST_DATAFRAME_FRAMEWORK.PANDAS, CONST_DATAFRAME_FRAMEWORK.POLARS),
    (CONST_DATAFRAME_FRAMEWORK.PYARROW, CONST_DATAFRAME_FRAMEWORK.POLARS)
])
@pytest.mark.performance
def test_conversion_performance_regression(sample_data_clean, source_backend, target_backend):
    """Test DataFrame conversion performance for common scenarios."""

    # Create source DataFrame
    source_df = DataFrameUtils.create_dataframe(
        sample_data_clean,
        dataframe_framework=source_backend
    )

    # Measure conversion time
    start_time = time.time()

    target_df = DataFrameUtils.cast_dataframe(
        source_df,
        dataframe_framework=target_backend
    )

    conversion_time = time.time() - start_time

    # Basic validation
    check.is_not_none(target_df)

    # Performance assertion
    check.is_true(conversion_time < 2.0,
                 f"Conversion {source_backend}->{target_backend} took {conversion_time:.3f}s")


# ===================================
# Memory Usage Tests
# ===================================

@pytest.mark.parametrize("backend", DATAFRAME_BACKENDS)
@pytest.mark.performance
def test_memory_usage_regression(backend):
    """Test memory usage to catch memory leaks or regressions."""

    # Large-ish dataset for memory testing
    large_data = {
        "id": list(range(10000)),
        "value": [f"value_{i}" for i in range(10000)],
        "score": [i * 1.5 for i in range(10000)]
    }

    # Start memory tracking
    tracemalloc.start()

    # Create DataFrame
    df = DataFrameUtils.create_dataframe(
        large_data,
        dataframe_framework=backend
    )

    # Perform some operations
    _ = DataFrameUtils.count(df)
    _ = DataFrameUtils.column_names(df)
    _ = DataFrameUtils.head(df, n=100)

    # Get memory usage
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Basic validation
    check.is_not_none(df)

    # Memory assertion (generous threshold - 100MB)
    peak_mb = peak / 1024 / 1024
    check.is_true(peak_mb < 100, f"Peak memory usage: {peak_mb:.2f}MB for {backend}")


# ===================================
# Cross-Backend Consistency Tests
# ===================================

@pytest.mark.integration
def test_cross_backend_result_consistency(sample_data_clean):
    """Test that operations produce consistent results across backends."""

    # Create same data in all backends
    dataframes = {}
    for backend in DATAFRAME_BACKENDS:
        dataframes[backend] = DataFrameUtils.create_dataframe(
            sample_data_clean,
            dataframe_framework=backend
        )

    # Test count consistency
    counts = {backend: DataFrameUtils.count(df) for backend, df in dataframes.items()}
    reference_count = list(counts.values())[0]

    for backend, count in counts.items():
        check.equal(count, reference_count,
                   f"Count mismatch for {backend}: {count} vs {reference_count}")

    # Test column names consistency
    column_sets = {
        backend: set(DataFrameUtils.column_names(df))
        for backend, df in dataframes.items()
    }
    reference_columns = list(column_sets.values())[0]

    for backend, columns in column_sets.items():
        check.equal(columns, reference_columns,
                   f"Column mismatch for {backend}")

    # Test first row consistency (basic values)
    first_rows = {
        backend: DataFrameUtils.get_first_row_as_dict(df)
        for backend, df in dataframes.items()
    }
    reference_first_row = list(first_rows.values())[0]

    for backend, first_row in first_rows.items():
        check.equal(first_row["id"], reference_first_row["id"],
                   f"First row ID mismatch for {backend}")
        check.equal(first_row["name"], reference_first_row["name"],
                   f"First row name mismatch for {backend}")


# ===================================
# Error Handling Tests
# ===================================

@pytest.mark.parametrize("backend", DATAFRAME_BACKENDS)
@pytest.mark.unit
def test_null_dataframe_handling(backend):
    """Test handling of None/null DataFrame inputs."""

    # Test conversion methods with None input
    check.is_none(DataFrameUtils.to_pandas(None))
    check.is_none(DataFrameUtils.to_polars(None))
    check.is_none(DataFrameUtils.to_pyarrow(None))
    check.is_none(DataFrameUtils.to_narwhals(None))

    # Test cast_dataframe with None input
    check.is_none(DataFrameUtils.cast_dataframe(None, backend))


@pytest.mark.unit
def test_empty_data_handling():
    """Test handling of empty data structures."""

    empty_data = {}

    # Should handle empty data gracefully
    for backend in DATAFRAME_BACKENDS:
        try:
            df = DataFrameUtils.create_dataframe(
                empty_data,
                dataframe_framework=backend
            )

            # If creation succeeds, validate it's empty
            if df is not None:
                count = DataFrameUtils.count(df)
                check.equal(count, 0)

        except (ValueError, TypeError):
            # Some backends may reject empty data - that's acceptable
            pass


# ===================================
# API Signature Validation Tests
# ===================================

@pytest.mark.unit
def test_public_api_availability():
    """Test that all expected public API methods are available."""

    expected_methods = [
        'create_dataframe', 'create_pandas', 'create_polars',
        'create_pyarrow', 'create_ibis',
        'cast_dataframe', 'to_pandas', 'to_polars', 'to_pyarrow',
        'to_ibis', 'to_narwhals',
        'column_names', 'count', 'head', 'get_first_row_as_dict',
        'to_list_of_dictionaries', 'to_dictionary_of_lists',
        'inner_join', 'left_join', 'outer_join',
        'filter', 'select', 'drop'
    ]

    for method_name in expected_methods:
        check.is_true(hasattr(DataFrameUtils, method_name),
                     f"Missing method: {method_name}")

        method = getattr(DataFrameUtils, method_name)
        check.is_true(callable(method),
                     f"Method {method_name} is not callable")


if __name__ == "__main__":
    # Run with: python -m pytest tests/test_dataframe_utils_comprehensive.py -v
    pytest.main([__file__, "-v", "--tb=short"])
