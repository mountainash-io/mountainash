"""Shared fixtures for join module tests."""

import pytest
import pandas as pd
import polars as pl
import pyarrow as pa
import ibis
import narwhals as nw
from typing import Dict, List, Any, Tuple

from mountainash.dataframes import DataFrameUtils


# ============================================================================
# STANDARD TEST DATA
# ============================================================================

@pytest.fixture(scope="module")
def left_data_standard() -> Dict[str, List[Any]]:
    """Standard left table data for join tests."""
    return {
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "department": ["Engineering", "Sales", "Engineering", "HR", "Sales"]
    }


@pytest.fixture(scope="module")
def right_data_standard() -> Dict[str, List[Any]]:
    """Standard right table data for join tests."""
    return {
        "id": [2, 3, 4, 6, 7],
        "salary": [75000.0, 85000.0, 95000.0, 65000.0, 70000.0],
        "bonus": [5000.0, 7500.0, 10000.0, 3000.0, 4000.0]
    }


# ============================================================================
# BACKEND-SPECIFIC FIXTURES
# ============================================================================

@pytest.fixture
def left_pandas_df(left_data_standard) -> pd.DataFrame:
    """Pandas DataFrame for left table."""
    return pd.DataFrame(left_data_standard)


@pytest.fixture
def right_pandas_df(right_data_standard) -> pd.DataFrame:
    """Pandas DataFrame for right table."""
    return pd.DataFrame(right_data_standard)


@pytest.fixture
def left_polars_df(left_data_standard) -> pl.DataFrame:
    """Polars DataFrame for left table."""
    return pl.DataFrame(left_data_standard)


@pytest.fixture
def right_polars_df(right_data_standard) -> pl.DataFrame:
    """Polars DataFrame for right table."""
    return pl.DataFrame(right_data_standard)


@pytest.fixture
def left_polars_lazy(left_data_standard) -> pl.LazyFrame:
    """Polars LazyFrame for left table."""
    return pl.DataFrame(left_data_standard).lazy()


@pytest.fixture
def right_polars_lazy(right_data_standard) -> pl.LazyFrame:
    """Polars LazyFrame for right table."""
    return pl.DataFrame(right_data_standard).lazy()


@pytest.fixture
def left_pyarrow_table(left_data_standard) -> pa.Table:
    """PyArrow Table for left table."""
    return pa.table(left_data_standard)


@pytest.fixture
def right_pyarrow_table(right_data_standard) -> pa.Table:
    """PyArrow Table for right table."""
    return pa.table(right_data_standard)


@pytest.fixture(scope="module")
def shared_ibis_backend():
    """Shared Ibis backend for testing backend comparisons.

    Using module scope ensures the same backend instance is used across tests.
    """
    # Create a temporary table just to get the backend
    temp_table = DataFrameUtils.create_ibis({"id": [1]})
    return temp_table.get_backend()


@pytest.fixture
def left_ibis_table(left_data_standard, shared_ibis_backend) -> ibis.expr.types.Table:
    """Ibis Table for left table using shared backend."""
    # First create as pandas, then convert to ibis with shared backend
    left_df = pd.DataFrame(left_data_standard)
    return DataFrameUtils.to_ibis(left_df, ibis_backend=shared_ibis_backend)


@pytest.fixture
def right_ibis_table(right_data_standard, shared_ibis_backend) -> ibis.expr.types.Table:
    """Ibis Table for right table using shared backend."""
    # First create as pandas, then convert to ibis with shared backend
    right_df = pd.DataFrame(right_data_standard)
    return DataFrameUtils.to_ibis(right_df, ibis_backend=shared_ibis_backend)


@pytest.fixture
def left_narwhals_df(left_data_standard) -> nw.DataFrame:
    """Narwhals DataFrame for left table."""
    pandas_df = pd.DataFrame(left_data_standard)
    return nw.from_native(pandas_df)


@pytest.fixture
def right_narwhals_df(right_data_standard) -> nw.DataFrame:
    """Narwhals DataFrame for right table."""
    pandas_df = pd.DataFrame(right_data_standard)
    return nw.from_native(pandas_df)


# ============================================================================
# CROSS-BACKEND TEST DATA
# ============================================================================

@pytest.fixture(scope="module")
def all_backend_join_pairs(left_data_standard, right_data_standard):
    """All backend DataFrame pairs with identical data for cross-backend testing."""
    left_ibis = DataFrameUtils.create_ibis(left_data_standard)
    right_ibis = DataFrameUtils.create_ibis(right_data_standard)

    return {
        "pandas": {
            "left": pd.DataFrame(left_data_standard),
            "right": pd.DataFrame(right_data_standard)
        },
        "polars": {
            "left": pl.DataFrame(left_data_standard),
            "right": pl.DataFrame(right_data_standard)
        },
        "polars_lazy": {
            "left": pl.DataFrame(left_data_standard).lazy(),
            "right": pl.DataFrame(right_data_standard).lazy()
        },
        "pyarrow": {
            "left": pa.table(left_data_standard),
            "right": pa.table(right_data_standard)
        },
        "ibis": {
            "left": left_ibis,
            "right": right_ibis
        },
        "narwhals": {
            "left": nw.from_native(pd.DataFrame(left_data_standard)),
            "right": nw.from_native(pd.DataFrame(right_data_standard))
        }
    }


# ============================================================================
# EDGE CASE FIXTURES
# ============================================================================

@pytest.fixture
def empty_dataframes() -> Dict[str, Tuple[Any, Any]]:
    """Empty DataFrames for all backends."""
    empty_data = {}
    return {
        "pandas": (pd.DataFrame(empty_data), pd.DataFrame(empty_data)),
        "polars": (pl.DataFrame(empty_data), pl.DataFrame(empty_data)),
        "pyarrow": (pa.table({}), pa.table({})),
        "ibis": (
            DataFrameUtils.create_ibis({}),
            DataFrameUtils.create_ibis({})
        ),
        "narwhals": (
            nw.from_native(pd.DataFrame(empty_data)),
            nw.from_native(pd.DataFrame(empty_data))
        )
    }


@pytest.fixture
def single_row_join_data() -> Tuple[Dict, Dict]:
    """Single-row DataFrames for join testing."""
    left = {"id": [1], "name": ["Alice"], "dept": ["Engineering"]}
    right = {"id": [1], "salary": [95000.0], "bonus": [10000.0]}
    return left, right


@pytest.fixture
def dataframes_with_nulls() -> Tuple[Dict, Dict]:
    """DataFrames with null values for testing null handling in joins."""
    left = {
        "id": [1, 2, None, 4, 5],
        "name": ["Alice", "Bob", "Charlie", None, "Eve"],
        "dept": ["Engineering", None, "Engineering", "HR", None]
    }
    right = {
        "id": [2, None, 4, 6, 7],
        "salary": [75000.0, 85000.0, None, 65000.0, 70000.0],
        "bonus": [5000.0, None, 10000.0, 3000.0, 4000.0]
    }
    return left, right


@pytest.fixture
def no_overlap_join_data() -> Tuple[Dict, Dict]:
    """DataFrames with no overlapping keys for join testing."""
    left = {"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"]}
    right = {"id": [4, 5, 6], "salary": [95000.0, 85000.0, 75000.0]}
    return left, right


@pytest.fixture
def complete_overlap_join_data() -> Tuple[Dict, Dict]:
    """DataFrames with complete key overlap for join testing."""
    left = {"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"]}
    right = {"id": [1, 2, 3], "salary": [95000.0, 85000.0, 75000.0]}
    return left, right


@pytest.fixture
def duplicate_keys_join_data() -> Tuple[Dict, Dict]:
    """DataFrames with duplicate join keys."""
    left = {
        "id": [1, 1, 2, 2, 3],
        "name": ["Alice", "Alice", "Bob", "Bob", "Charlie"],
        "dept": ["Eng", "Sales", "Eng", "HR", "Sales"]
    }
    right = {
        "id": [1, 1, 2, 3, 3],
        "salary": [95000.0, 98000.0, 85000.0, 75000.0, 78000.0]
    }
    return left, right


@pytest.fixture
def multiple_key_join_data() -> Tuple[Dict, Dict]:
    """DataFrames for testing multi-column joins."""
    left = {
        "id": [1, 1, 2, 2, 3],
        "dept": ["Eng", "Sales", "Eng", "Sales", "HR"],
        "name": ["Alice", "Alice Jr", "Bob", "Bob Jr", "Charlie"]
    }
    right = {
        "id": [1, 1, 2, 2, 3],
        "dept": ["Eng", "Sales", "Eng", "Sales", "HR"],
        "salary": [95000.0, 85000.0, 88000.0, 78000.0, 92000.0]
    }
    return left, right


# ============================================================================
# REALISTIC SCENARIO FIXTURES
# ============================================================================

@pytest.fixture
def employees_data() -> Dict[str, List[Any]]:
    """Realistic employee master data."""
    return {
        "employee_id": [1001, 1002, 1003, 1004, 1005],
        "first_name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "last_name": ["Johnson", "Smith", "Brown", "Wilson", "Davis"],
        "department_id": [10, 20, 10, 30, 20],
        "hire_date": ["2020-01-15", "2019-06-01", "2021-03-10", "2020-09-20", "2022-01-05"]
    }


@pytest.fixture
def departments_data() -> Dict[str, List[Any]]:
    """Realistic department reference data."""
    return {
        "department_id": [10, 20, 30, 40],
        "department_name": ["Engineering", "Sales", "HR", "Marketing"],
        "location": ["San Francisco", "New York", "Chicago", "Boston"]
    }


@pytest.fixture
def salaries_data() -> Dict[str, List[Any]]:
    """Realistic salary data."""
    return {
        "employee_id": [1001, 1002, 1003, 1005, 1006],
        "base_salary": [95000.0, 75000.0, 88000.0, 82000.0, 70000.0],
        "bonus": [10000.0, 5000.0, 7500.0, 6000.0, 4000.0],
        "currency": ["USD", "USD", "USD", "USD", "USD"]
    }


@pytest.fixture
def join_predicates() -> Dict[str, Any]:
    """Common join predicates for testing."""
    return {
        "single_column": "id",
        "multiple_columns": ["id", "dept"],
        "list_single": ["id"],
        "employee_dept": "department_id",
        "employee_salary": "employee_id"
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
