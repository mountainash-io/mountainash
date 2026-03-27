"""Shared fixtures for filter_expressions module tests."""

import pytest
import pandas as pd
import polars as pl
import pyarrow as pa
import ibis
import narwhals as nw
from typing import Dict, List, Any

from mountainash.dataframes import DataFrameUtils


# ============================================================================
# STANDARD TEST DATA
# ============================================================================

@pytest.fixture(scope="module")
def filter_test_data() -> Dict[str, List[Any]]:
    """Standard test data for filter expression tests."""
    return {
        "id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry", "Iris", "Jack"],
        "age": [25, 30, 35, 28, 42, 31, 27, 38, 29, 33],
        "department": ["Engineering", "Sales", "Engineering", "HR", "Sales", "Engineering", "HR", "Sales", "Engineering", "HR"],
        "salary": [75000.0, 65000.0, 85000.0, 70000.0, 95000.0, 80000.0, 68000.0, 72000.0, 78000.0, 71000.0],
        "is_active": [True, True, False, True, True, False, True, True, False, True]
    }


# ============================================================================
# BACKEND-SPECIFIC FIXTURES
# ============================================================================

@pytest.fixture
def pandas_df(filter_test_data) -> pd.DataFrame:
    """Pandas DataFrame for filter tests."""
    return pd.DataFrame(filter_test_data)


@pytest.fixture
def polars_df(filter_test_data) -> pl.DataFrame:
    """Polars DataFrame for filter tests."""
    return pl.DataFrame(filter_test_data)


@pytest.fixture
def polars_lazy(filter_test_data) -> pl.LazyFrame:
    """Polars LazyFrame for filter tests."""
    return pl.DataFrame(filter_test_data).lazy()


@pytest.fixture
def pyarrow_table(filter_test_data) -> pa.Table:
    """PyArrow Table for filter tests."""
    return pa.table(filter_test_data)


@pytest.fixture(scope="module")
def shared_ibis_backend():
    """Shared Ibis backend for testing."""
    temp_table = DataFrameUtils.create_ibis({"id": [1]})
    return temp_table.get_backend()


@pytest.fixture
def ibis_table(filter_test_data, shared_ibis_backend) -> ibis.expr.types.Table:
    """Ibis Table for filter tests."""
    df = pd.DataFrame(filter_test_data)
    return DataFrameUtils.to_ibis(df, ibis_backend=shared_ibis_backend)


@pytest.fixture
def narwhals_df(filter_test_data) -> nw.DataFrame:
    """Narwhals DataFrame for filter tests."""
    pandas_df = pd.DataFrame(filter_test_data)
    return nw.from_native(pandas_df)


# ============================================================================
# EXPRESSION FIXTURES
# ============================================================================

@pytest.fixture
def pandas_expression_single_column(pandas_df) -> pd.Series:
    """Simple pandas boolean expression for single column filter."""
    return pandas_df["age"] > 30


@pytest.fixture
def polars_expression_single_column() -> pl.Expr:
    """Simple polars expression for single column filter."""
    return pl.col("age") > 30


@pytest.fixture
def ibis_expression_single_column(ibis_table) -> Any:
    """Simple ibis expression for single column filter."""
    return ibis_table.age > 30


@pytest.fixture
def narwhals_expression_single_column() -> nw.Expr:
    """Simple narwhals expression for single column filter."""
    return nw.col("age") > 30


@pytest.fixture
def polars_expression_multiple_conditions() -> pl.Expr:
    """Complex polars expression with multiple conditions."""
    return (pl.col("age") > 30) & (pl.col("salary") >= 75000.0)


@pytest.fixture
def narwhals_expression_multiple_conditions() -> nw.Expr:
    """Complex narwhals expression with multiple conditions."""
    return (nw.col("age") > 30) & (nw.col("salary") >= 75000.0)


@pytest.fixture
def ibis_expression_multiple_conditions(ibis_table) -> Any:
    """Complex ibis expression with multiple conditions."""
    return (ibis_table.age > 30) & (ibis_table.salary >= 75000.0)


# ============================================================================
# CROSS-BACKEND TEST DATA
# ============================================================================

@pytest.fixture(scope="module")
def all_backend_filter_dataframes(filter_test_data):
    """All backend DataFrames with identical data for cross-backend testing."""
    ibis_table = DataFrameUtils.create_ibis(filter_test_data)

    return {
        "pandas": pd.DataFrame(filter_test_data),
        "polars": pl.DataFrame(filter_test_data),
        "polars_lazy": pl.DataFrame(filter_test_data).lazy(),
        "pyarrow": pa.table(filter_test_data),
        "ibis": ibis_table,
        "narwhals": nw.from_native(pd.DataFrame(filter_test_data))
    }


# ============================================================================
# EDGE CASE FIXTURES
# ============================================================================

@pytest.fixture
def empty_dataframes() -> Dict[str, Any]:
    """Empty DataFrames for all backends."""
    empty_data = {}
    return {
        "pandas": pd.DataFrame(empty_data),
        "polars": pl.DataFrame(empty_data),
        "pyarrow": pa.table({}),
        "ibis": DataFrameUtils.create_ibis({}),
        "narwhals": nw.from_native(pd.DataFrame(empty_data))
    }


@pytest.fixture
def single_row_dataframes() -> Dict[str, List[Any]]:
    """Single-row DataFrames for filter testing."""
    return {
        "id": [1],
        "name": ["Alice"],
        "age": [25],
        "department": ["Engineering"],
        "salary": [75000.0],
        "is_active": [True]
    }


@pytest.fixture
def dataframes_with_nulls() -> Dict[str, List[Any]]:
    """DataFrames with null values for testing null handling in filters."""
    return {
        "id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "name": ["Alice", None, "Charlie", "Diana", None, "Frank", "Grace", None, "Iris", "Jack"],
        "age": [25, 30, None, 28, 42, 31, None, 38, 29, None],
        "department": ["Engineering", "Sales", None, "HR", "Sales", None, "HR", "Sales", "Engineering", None],
        "salary": [75000.0, None, 85000.0, 70000.0, None, 80000.0, 68000.0, None, 78000.0, 71000.0],
        "is_active": [True, True, None, True, None, False, True, None, False, True]
    }


@pytest.fixture
def all_matching_filter_data() -> Dict[str, List[Any]]:
    """DataFrames where all rows match the filter condition."""
    return {
        "id": [1, 2, 3, 4, 5],
        "age": [35, 40, 45, 50, 55],  # All > 30
        "department": ["Engineering", "Engineering", "Engineering", "Engineering", "Engineering"]
    }


@pytest.fixture
def no_matching_filter_data() -> Dict[str, List[Any]]:
    """DataFrames where no rows match the filter condition."""
    return {
        "id": [1, 2, 3, 4, 5],
        "age": [20, 22, 25, 28, 30],  # All <= 30
        "department": ["Sales", "Sales", "Sales", "Sales", "Sales"]
    }


# ============================================================================
# CORE BACKEND FIXTURE NAMES FOR PARAMETERIZATION
# ============================================================================

# Core backends for consistency testing (excluding lazy variants)
CORE_BACKEND_FIXTURES = [
    "pandas",
    "polars",
    "pyarrow",
    "ibis",
    "narwhals"
]

# All backends including lazy evaluation
ALL_BACKEND_FIXTURES = [
    "pandas",
    "polars",
    "polars_lazy",
    "pyarrow",
    "ibis",
    "narwhals"
]
