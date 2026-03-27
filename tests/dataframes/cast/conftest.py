"""Shared fixtures for cast module tests."""

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
def standard_data() -> Dict[str, List[Any]]:
    """Standard test data for cast tests."""
    return {
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "category": ["A", "B", "A", "C", "B"],
        "value": [100.5, 200.7, 300.9, 400.2, 500.8],
        "active": [True, False, True, True, False]
    }


# ============================================================================
# BACKEND-SPECIFIC FIXTURES
# ============================================================================

@pytest.fixture
def pandas_df(standard_data) -> pd.DataFrame:
    """Pandas DataFrame for testing."""
    return pd.DataFrame(standard_data)


@pytest.fixture
def polars_df(standard_data) -> pl.DataFrame:
    """Polars DataFrame for testing."""
    return pl.DataFrame(standard_data)


@pytest.fixture
def polars_lazy(standard_data) -> pl.LazyFrame:
    """Polars LazyFrame for testing."""
    return pl.DataFrame(standard_data).lazy()


@pytest.fixture
def pyarrow_table(standard_data) -> pa.Table:
    """PyArrow Table for testing."""
    return pa.table(standard_data)


@pytest.fixture(scope="module")
def shared_ibis_backend():
    """Shared Ibis backend for testing.

    Using module scope ensures the same backend instance is used across tests.
    """
    # Create a temporary table just to get the backend
    temp_table = DataFrameUtils.create_ibis({"id": [1]})
    return temp_table.get_backend()


@pytest.fixture
def ibis_table(standard_data, shared_ibis_backend) -> ibis.expr.types.Table:
    """Ibis Table for testing using shared backend."""
    # First create as pandas, then convert to ibis with shared backend
    df = pd.DataFrame(standard_data)
    return DataFrameUtils.to_ibis(df, ibis_backend=shared_ibis_backend)


@pytest.fixture
def narwhals_df(standard_data) -> nw.DataFrame:
    """Narwhals DataFrame for testing."""
    pandas_df = pd.DataFrame(standard_data)
    return nw.from_native(pandas_df)


@pytest.fixture
def narwhals_lazy(standard_data) -> nw.LazyFrame:
    """Narwhals LazyFrame for testing."""
    polars_df = pl.DataFrame(standard_data)
    return nw.from_native(polars_df.lazy())


# ============================================================================
# ALL BACKENDS FIXTURE FOR PARAMETERIZATION
# ============================================================================

@pytest.fixture(scope="module")
def all_backend_dataframes(standard_data):
    """All backend DataFrames with identical data for cross-backend testing."""
    ibis_table = DataFrameUtils.create_ibis(standard_data)

    return {
        "pandas": pd.DataFrame(standard_data),
        "polars": pl.DataFrame(standard_data),
        "polars_lazy": pl.DataFrame(standard_data).lazy(),
        "pyarrow": pa.table(standard_data),
        "ibis": ibis_table,
        "narwhals": nw.from_native(pd.DataFrame(standard_data)),
        "narwhals_lazy": nw.from_native(pl.DataFrame(standard_data).lazy())
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
def single_row_data() -> Dict[str, List[Any]]:
    """Single-row data for testing."""
    return {
        "id": [1],
        "name": ["Alice"],
        "value": [100.5],
        "active": [True]
    }


@pytest.fixture
def single_column_data() -> Dict[str, List[Any]]:
    """Single-column data for testing."""
    return {"id": [1, 2, 3, 4, 5]}


@pytest.fixture
def dataframes_with_nulls() -> Dict[str, List[Any]]:
    """Data with null values for testing null handling."""
    return {
        "id": [1, 2, None, 4, 5],
        "name": ["Alice", None, "Charlie", "Diana", None],
        "value": [100.5, None, 300.9, None, 500.8],
        "active": [True, None, True, False, None]
    }


@pytest.fixture
def mixed_types_data() -> Dict[str, List[Any]]:
    """Data with various data types."""
    return {
        "integers": [1, 2, 3],
        "floats": [1.1, 2.2, 3.3],
        "strings": ["a", "b", "c"],
        "bools": [True, False, True],
        "mixed": [1, "two", 3.0]
    }


@pytest.fixture
def large_dataframe_data() -> Dict[str, List[Any]]:
    """Large DataFrame (1000 rows) for performance testing."""
    return {
        "id": list(range(1, 1001)),
        "value": [i * 10.5 for i in range(1, 1001)],
        "category": [f"Cat_{i % 10}" for i in range(1, 1001)]
    }


@pytest.fixture
def special_characters_data() -> Dict[str, List[Any]]:
    """Data with special characters in column names."""
    return {
        "column with spaces": [1, 2, 3],
        "column-with-dashes": ["a", "b", "c"],
        "column_normal": [10.5, 20.5, 30.5],
        "🚀_emoji_col": [True, False, True]
    }


# ============================================================================
# REALISTIC SCENARIO FIXTURES
# ============================================================================

@pytest.fixture
def financial_data() -> Dict[str, List[Any]]:
    """Realistic financial transaction data."""
    return {
        "transaction_id": [1001, 1002, 1003, 1004, 1005],
        "amount": [1250.50, 2500.75, 500.25, 10000.00, 750.80],
        "currency": ["USD", "EUR", "GBP", "USD", "EUR"],
        "timestamp": ["2024-01-15 10:30:00", "2024-01-15 11:45:00",
                     "2024-01-15 14:20:00", "2024-01-15 16:00:00",
                     "2024-01-15 17:30:00"],
        "category": ["expense", "income", "expense", "income", "expense"]
    }


@pytest.fixture
def sensor_data() -> Dict[str, List[Any]]:
    """Realistic sensor/IoT data."""
    return {
        "sensor_id": ["S001", "S002", "S003", "S004", "S005"],
        "temperature": [22.5, 23.1, 21.8, 24.2, 22.9],
        "humidity": [45.0, 50.5, 48.2, 52.1, 46.8],
        "pressure": [1013.25, 1012.80, 1014.10, 1011.95, 1013.50],
        "online": [True, True, False, True, True]
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
    "narwhals",
    "narwhals_lazy"
]
