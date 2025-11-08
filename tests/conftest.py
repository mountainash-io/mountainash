"""
Pytest configuration and shared fixtures for Mountain Ash Expressions tests.

This module provides:
- Backend fixtures (Polars, Pandas, Narwhals, Ibis, PyArrow)
- Test data fixtures (sample, temporal, arithmetic, string data)
- Helper functions for cross-backend result extraction
- Test markers for organizing test suites
"""

import pytest
import polars as pl
import pandas as pd
import narwhals as nw
import ibis
import pyarrow as pa
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List


# =============================================================================
# Constants
# =============================================================================

ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals",
    "ibis-duckdb",
    "ibis-polars",
    "ibis-sqlite"
]
TEMPORAL_BACKENDS = [
    "polars",
    "narwhals",
    "ibis-duckdb",
    "ibis-polars",
    "ibis-sqlite"
]  # Pandas temporal support varies

# Map backend names to Ibis backend types
IBIS_BACKEND_TYPES = {
    "ibis-duckdb": "duckdb",
    "ibis-polars": "polars",
    "ibis-sqlite": "sqlite"
}


# =============================================================================
# Test Markers Configuration
# =============================================================================

def pytest_configure(config):
    """Register custom markers for test organization."""
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated)")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "backend: Backend-specific tests")
    config.addinivalue_line("markers", "cross_backend: Cross-backend consistency tests")
    config.addinivalue_line("markers", "temporal: Temporal operation tests")
    config.addinivalue_line("markers", "arithmetic: Arithmetic operation tests")
    config.addinivalue_line("markers", "string: String operation tests")
    config.addinivalue_line("markers", "comparison: Comparison operation tests")
    config.addinivalue_line("markers", "logical: Logical operation tests")
    config.addinivalue_line("markers", "slow: Slow-running tests")


# =============================================================================
# Backend Name Fixtures
# =============================================================================

@pytest.fixture(params=ALL_BACKENDS)
def backend_name(request):
    """
    Parametrize tests across all supported backends.

    Usage:
        @pytest.mark.parametrize("backend_name", ["polars", "ibis"])
        def test_something(backend_name, ...):
            ...

    Or use this fixture directly for auto-parametrization:
        def test_something(backend_name, ...):
            # Will run for all backends
    """
    return request.param


@pytest.fixture(params=TEMPORAL_BACKENDS)
def temporal_backend_name(request):
    """Parametrize across backends with good temporal support."""
    return request.param


# =============================================================================
# Test Data Fixtures
# =============================================================================

@pytest.fixture
def sample_data() -> Dict[str, List]:
    """
    Standard test dataset for general operations.

    Schema:
        - age: int (25-45, step 5)
        - score: int (75-95)
        - name: str (Alice, Bob, Charlie, David, Eve)
        - active: bool (True, True, False, True, False)
        - salary: float (50k-90k)
    """
    return {
        'age': [25, 30, 35, 40, 45],
        'score': [85, 90, 75, 95, 80],
        'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
        'active': [True, True, False, True, False],
        'salary': [50000.0, 60000.0, 70000.0, 80000.0, 90000.0]
    }


@pytest.fixture
def temporal_data() -> Dict[str, List]:
    """
    Temporal test dataset with timestamps.

    Schema:
        - timestamp: datetime (5 min ago, 1 hour ago, 1 day ago, 7 days ago, 30 days ago)
        - event: str (A, B, C, D, E)
        - level: str (INFO, ERROR, WARN, etc.)
    """
    now = datetime.now()
    return {
        'timestamp': [
            now - timedelta(minutes=5),
            now - timedelta(hours=1),
            now - timedelta(days=1),
            now - timedelta(days=7),
            now - timedelta(days=30)
        ],
        'event': ['A', 'B', 'C', 'D', 'E'],
        'level': ['INFO', 'ERROR', 'WARN', 'INFO', 'ERROR']
    }


@pytest.fixture
def arithmetic_data() -> Dict[str, List]:
    """
    Arithmetic operations test data.

    Schema:
        - a: int (10-50, step 10)
        - b: int (2-6)
        - c: float (1.5-5.5, step 1.0)
    """
    return {
        'a': [10, 20, 30, 40, 50],
        'b': [2, 3, 4, 5, 6],
        'c': [1.5, 2.5, 3.5, 4.5, 5.5]
    }


@pytest.fixture
def string_data() -> Dict[str, List]:
    """
    String operations test data.

    Schema:
        - text: str (various strings for testing)
        - category: str (A, B, C)
    """
    return {
        'text': ['hello', 'world', 'test', 'data', 'python'],
        'category': ['A', 'B', 'A', 'C', 'B'],
        'description': [
            'Hello World',
            'Test String',
            'Another Test',
            'Final String',
            'Python Code'
        ]
    }


@pytest.fixture
def null_data() -> Dict[str, List]:
    """
    Test data with null/None values for testing null handling.

    Schema:
        - value: Optional[int]
        - text: Optional[str]
    """
    return {
        'value': [1, None, 3, None, 5],
        'text': ['a', 'b', None, 'd', None]
    }


# =============================================================================
# Backend DataFrame Fixtures
# =============================================================================

@pytest.fixture
def polars_df(sample_data) -> pl.DataFrame:
    """Create Polars DataFrame from sample data."""
    return pl.DataFrame(sample_data)


@pytest.fixture
def pandas_df(sample_data) -> pd.DataFrame:
    """Create Pandas DataFrame from sample data."""
    return pd.DataFrame(sample_data)


@pytest.fixture
def narwhals_df(sample_data) -> Any:
    """Create Narwhals DataFrame from sample data."""
    pl_df = pl.DataFrame(sample_data)
    return nw.from_native(pl_df)


@pytest.fixture
def ibis_duckdb_df(sample_data) -> Any:
    """Create Ibis Table with DuckDB backend from sample data."""
    import duckdb
    conn = ibis.duckdb.connect()
    return conn.create_table("sample", sample_data, overwrite=True)


@pytest.fixture
def ibis_polars_df(sample_data) -> Any:
    """Create Ibis Table with Polars backend from sample data."""
    conn = ibis.polars.connect()
    pl_df = pl.DataFrame(sample_data)
    return conn.create_table("sample", pl_df, overwrite=True)


@pytest.fixture
def ibis_sqlite_df(sample_data) -> Any:
    """Create Ibis Table with SQLite backend from sample data."""
    conn = ibis.sqlite.connect(":memory:")
    return conn.create_table("sample", sample_data, overwrite=True)


@pytest.fixture
def backend_df(backend_name: str, sample_data) -> Any:
    """
    Create DataFrame for the specified backend.

    Args:
        backend_name: One of ["polars", "pandas", "narwhals", "ibis-duckdb", "ibis-polars", "ibis-sqlite"]
        sample_data: Test data dictionary

    Returns:
        Backend-specific DataFrame object
    """
    if backend_name == "polars":
        return pl.DataFrame(sample_data)
    elif backend_name == "pandas":
        return pd.DataFrame(sample_data)
    elif backend_name == "narwhals":
        pl_df = pl.DataFrame(sample_data)
        return nw.from_native(pl_df)
    elif backend_name == "ibis-duckdb":
        conn = ibis.duckdb.connect()
        return conn.create_table("sample", sample_data, overwrite=True)
    elif backend_name == "ibis-polars":
        conn = ibis.polars.connect()
        pl_df = pl.DataFrame(sample_data)
        return conn.create_table("sample", pl_df, overwrite=True)
    elif backend_name == "ibis-sqlite":
        conn = ibis.sqlite.connect(":memory:")
        return conn.create_table("sample", sample_data, overwrite=True)
    else:
        raise ValueError(f"Unknown backend: {backend_name}")


@pytest.fixture
def backend_temporal_df(backend_name: str, temporal_data) -> Any:
    """Create temporal DataFrame for the specified backend."""
    if backend_name == "polars":
        return pl.DataFrame(temporal_data)
    elif backend_name == "pandas":
        return pd.DataFrame(temporal_data)
    elif backend_name == "narwhals":
        pl_df = pl.DataFrame(temporal_data)
        return nw.from_native(pl_df)
    elif backend_name == "ibis-duckdb":
        conn = ibis.duckdb.connect()
        return conn.create_table("temporal", temporal_data, overwrite=True)
    elif backend_name == "ibis-polars":
        conn = ibis.polars.connect()
        pl_df = pl.DataFrame(temporal_data)
        return conn.create_table("temporal", pl_df, overwrite=True)
    elif backend_name == "ibis-sqlite":
        conn = ibis.sqlite.connect(":memory:")
        return conn.create_table("temporal", temporal_data, overwrite=True)
    else:
        raise ValueError(f"Unknown backend: {backend_name}")


@pytest.fixture
def backend_arithmetic_df(backend_name: str, arithmetic_data) -> Any:
    """Create arithmetic DataFrame for the specified backend."""
    if backend_name == "polars":
        return pl.DataFrame(arithmetic_data)
    elif backend_name == "pandas":
        return pd.DataFrame(arithmetic_data)
    elif backend_name == "narwhals":
        pl_df = pl.DataFrame(arithmetic_data)
        return nw.from_native(pl_df)
    elif backend_name == "ibis-duckdb":
        conn = ibis.duckdb.connect()
        return conn.create_table("arithmetic", arithmetic_data, overwrite=True)
    elif backend_name == "ibis-polars":
        conn = ibis.polars.connect()
        pl_df = pl.DataFrame(arithmetic_data)
        return conn.create_table("arithmetic", pl_df, overwrite=True)
    elif backend_name == "ibis-sqlite":
        conn = ibis.sqlite.connect(":memory:")
        return conn.create_table("arithmetic", arithmetic_data, overwrite=True)
    else:
        raise ValueError(f"Unknown backend: {backend_name}")


@pytest.fixture
def backend_string_df(backend_name: str, string_data) -> Any:
    """Create string DataFrame for the specified backend."""
    if backend_name == "polars":
        return pl.DataFrame(string_data)
    elif backend_name == "pandas":
        return pd.DataFrame(string_data)
    elif backend_name == "narwhals":
        pl_df = pl.DataFrame(string_data)
        return nw.from_native(pl_df)
    elif backend_name == "ibis-duckdb":
        conn = ibis.duckdb.connect()
        return conn.create_table("strings", string_data, overwrite=True)
    elif backend_name == "ibis-polars":
        conn = ibis.polars.connect()
        pl_df = pl.DataFrame(string_data)
        return conn.create_table("strings", pl_df, overwrite=True)
    elif backend_name == "ibis-sqlite":
        conn = ibis.sqlite.connect(":memory:")
        return conn.create_table("strings", string_data, overwrite=True)
    else:
        raise ValueError(f"Unknown backend: {backend_name}")


# =============================================================================
# Result Helper Fixtures
# =============================================================================

@pytest.fixture
def get_result_count() -> Callable:
    """
    Helper to get row count from any backend DataFrame.

    Returns:
        Callable that takes (df, backend_name) and returns row count

    Usage:
        count = get_result_count(result_df, "polars")
        assert count == 3
    """
    def _get_count(df: Any, backend_name: str) -> int:
        if backend_name.startswith("ibis-"):
            return df.count().execute()
        elif backend_name in ["polars", "pandas", "narwhals"]:
            return df.shape[0]
        else:
            return len(df)
    return _get_count


@pytest.fixture
def get_result() -> Callable:
    """
    Helper to get row count from any backend DataFrame.

    Returns:
        Callable that takes (df, backend_name) and returns row count

    Usage:
        count = get_result_count(result_df, "polars")
        assert count == 3
    """
    def _get_result(df: Any, backend_name: str) -> int:
        if backend_name.startswith("ibis-"):
            return df.execute()
        else: # backend_name in ["polars", "pandas", "narwhals"]:
            return df
    return _get_result



@pytest.fixture
def select_and_extract() -> Callable:
    """
    Helper to select expression and extract values - handles all backends.

    Single function that:
    1. Selects with backend-specific method (.name() or .alias())
    2. Collects/executes if needed (no double-collect)
    3. Extracts column values to list

    Returns:
        Callable that takes (df, backend_expr, column_alias, backend_name) and returns list

    Usage:
        actual = select_and_extract(df, backend_expr, "result", "polars")
        assert actual == [12, 23, 34]
    """
    def _select_and_extract(df: Any, backend_expr: Any, column_alias: str, backend_name: str) -> List:
        # Handle each backend type completely in one place
        if backend_name.startswith("ibis-"):
            # Ibis: use .name(), then execute to get values
            result = df.select(backend_expr.name(column_alias))
            return result[column_alias].execute().tolist()

        elif backend_name in ("polars", "narwhals", "pandas"):
            # Polars/Narwhals/Pandas: use .alias(), then to_list()
            # (pandas is routed through narwhals in factory)
            result = df.select(backend_expr.alias(column_alias))
            return result[column_alias].to_list()

        else:
            raise ValueError(f"Unknown backend: {backend_name}")

    return _select_and_extract


@pytest.fixture
def get_column_values() -> Callable:
    """
    Helper to extract column values as list from any backend.

    Returns:
        Callable that takes (df, column, backend_name) and returns list

    Usage:
        values = get_column_values(df, "age", "polars")
        assert values == [25, 30, 35]
    """
    def _get_values(df: Any, column: str, backend_name: str) -> List:
        if backend_name.startswith("ibis-"):
            return df[column].execute().tolist()
        elif backend_name in ["polars", "pandas", "narwhals"]:
            # Pandas is routed through narwhals, so all use .to_list()
            return df[column].to_list()
        else:
            raise ValueError(f"Unknown backend: {backend_name}")
    return _get_values


@pytest.fixture
def get_scalar_result() -> Callable:
    """
    Helper to extract scalar result from aggregation operations.

    Returns:
        Callable that takes (result, backend_name) and returns scalar value

    Usage:
        max_val = get_scalar_result(max_result, "polars")
        assert max_val == 45
    """
    def _get_scalar(result: Any, backend_name: str) -> Any:
        if backend_name.startswith("ibis-"):
            return result.execute()
        elif backend_name == "polars":
            return result
        elif backend_name == "pandas":
            return result
        elif backend_name == "narwhals":
            return result
        else:
            raise ValueError(f"Unknown backend: {backend_name}")
    return _get_scalar


@pytest.fixture
def assert_backend_equal():
    """
    Helper for asserting equality with backend-specific handling.

    Handles:
    - Float comparisons with tolerance
    - None/NaN equivalence
    - List comparisons

    Usage:
        assert_backend_equal(actual, expected, backend_name, "age comparison")
    """
    def _assert_equal(
        actual: Any,
        expected: Any,
        backend_name: str,
        message: str = ""
    ):
        if isinstance(expected, float):
            # Float comparison with tolerance
            assert abs(actual - expected) < 1e-6, (
                f"{message} [{backend_name}]: expected {expected}, got {actual}"
            )
        elif isinstance(expected, list):
            # List comparison
            assert actual == expected, (
                f"{message} [{backend_name}]: expected {expected}, got {actual}"
            )
        else:
            # Direct comparison
            assert actual == expected, (
                f"{message} [{backend_name}]: expected {expected}, got {actual}"
            )
    return _assert_equal


# =============================================================================
# Factory Fixtures
# =============================================================================

@pytest.fixture
def backend_factory():
    """
    Provide BackendDataFrameFactory for dynamic DataFrame creation in tests.

    Usage:
        def test_something(backend_factory, backend_name):
            df = backend_factory.create(data, backend_name)
    """
    import sys
    import os
    # Add tests directory to path
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    if tests_dir not in sys.path:
        sys.path.insert(0, tests_dir)

    from fixtures.backend_helpers import BackendDataFrameFactory
    return BackendDataFrameFactory


# =============================================================================
# Cleanup Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def reset_between_tests():
    """
    Automatically reset state between tests.

    This fixture runs before and after each test to ensure clean state.
    """
    # Setup (before test)
    yield
    # Teardown (after test)
    # Add any cleanup logic here if needed


# =============================================================================
# Pytest Collection Hooks
# =============================================================================

def pytest_collection_modifyitems(config, items):
    """
    Modify test items during collection.

    Auto-applies markers based on test path:
    - tests/unit/* → @pytest.mark.unit
    - tests/integration/* → @pytest.mark.integration
    - tests/cross_backend/* → @pytest.mark.cross_backend

    Auto-skips tests with known external issues:
    - pandas: Visitor factory doesn't support pandas backend yet
    - ibis-duckdb: External DuckDB dependency incompatibility
    """
    for item in items:
        # Get test file path
        test_path = str(item.fspath)

        # Auto-apply markers based on directory
        if "/unit/" in test_path:
            item.add_marker(pytest.mark.unit)
        elif "/integration/" in test_path:
            item.add_marker(pytest.mark.integration)
        elif "/cross_backend/" in test_path:
            item.add_marker(pytest.mark.cross_backend)
        elif "/backends/" in test_path:
            item.add_marker(pytest.mark.backend)

        # Auto-apply feature markers based on filename
        test_name = item.nodeid.lower()
        if "temporal" in test_name:
            item.add_marker(pytest.mark.temporal)
        if "arithmetic" in test_name:
            item.add_marker(pytest.mark.arithmetic)
        if "string" in test_name:
            item.add_marker(pytest.mark.string)

        # Auto-mark tests with known external issues
        # Check if test is parametrized with backend_name
        if hasattr(item, 'callspec') and 'backend_name' in item.callspec.params:
            backend_name = item.callspec.params['backend_name']

            # DuckDB dependency issue RESOLVED! ✅
            # Issue was fixed by updating dependencies
            # Previous blocker: module 'duckdb' has no attribute 'functional'
            # All 110+ DuckDB tests now pass
