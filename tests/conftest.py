"""
Pytest configuration and shared fixtures for Mountain Ash Expressions tests.

This module provides:
- Backend fixtures (Polars, Pandas, Narwhals, Ibis, PyArrow)
- Test data fixtures (sample, temporal, arithmetic, string data)
- Helper functions for cross-backend result extraction
- Test markers for organizing test suites
"""

# --- must run BEFORE `from fixtures.backend_registry import ...` ---
import os, sys
for _i, _a in enumerate(sys.argv):
    if _a == "--ma-backend-scope" and _i + 1 < len(sys.argv):
        os.environ["MA_BACKEND_SCOPE"] = sys.argv[_i + 1]
    elif _a.startswith("--ma-backend-scope="):
        os.environ["MA_BACKEND_SCOPE"] = _a.split("=", 1)[1]

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

from fixtures.backend_registry import (
    REGISTRY as BACKEND_REGISTRY,
    ALL_BACKENDS,
)
TEMPORAL_BACKENDS = [
    "polars",
    "polars-lazy",
    "narwhals-polars",
    "narwhals-pandas",
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
# CLI Options
# =============================================================================

def pytest_addoption(parser):
    parser.addoption(
        "--ma-backend-scope", action="store", default=None,
        choices=["pr", "full"],
        help="Backend matrix scope: 'pr' (one per family) or 'full' (all). "
             "Mirrors the MA_BACKEND_SCOPE env var; CLI wins.",
    )


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
    """Create DataFrame for the specified backend via the central registry."""
    return BACKEND_REGISTRY[backend_name].build(sample_data, table_name="sample")


@pytest.fixture
def backend_temporal_df(backend_name: str, temporal_data) -> Any:
    """Create temporal DataFrame for the specified backend."""
    return BACKEND_REGISTRY[backend_name].build(temporal_data, table_name="temporal")


@pytest.fixture
def backend_arithmetic_df(backend_name: str, arithmetic_data) -> Any:
    """Create arithmetic DataFrame for the specified backend."""
    return BACKEND_REGISTRY[backend_name].build(arithmetic_data, table_name="arithmetic")


@pytest.fixture
def backend_string_df(backend_name: str, string_data) -> Any:
    """Create string DataFrame for the specified backend."""
    return BACKEND_REGISTRY[backend_name].build(string_data, table_name="strings")


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
        spec = BACKEND_REGISTRY[backend_name]
        if spec.materialization == "deferred":  # ibis
            return df.count().execute()
        if spec.materialization == "lazy":      # polars-lazy
            return df.collect().shape[0]
        if spec.family == "narwhals":
            return df.shape[0]
        return df.shape[0] if hasattr(df, "shape") else len(df)
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
    def _get_result(df: Any, backend_name: str) -> Any:
        spec = BACKEND_REGISTRY[backend_name]
        if spec.materialization == "deferred":  # ibis
            return df.execute()
        if spec.materialization == "lazy":      # polars-lazy
            return df.collect()
        return df
    return _get_result



@pytest.fixture
def select_and_extract() -> Callable:
    """
    Extract compiled expression results — for booleanizer/internal tests only.

    Most tests should use `collect_expr` instead. This fixture exists only for
    tests that need to pass explicit booleanizer parameters to .compile(),
    which the relation API does not support.

    Usage:
        backend_expr = expr.compile(df, booleanizer=None)
        actual = select_and_extract(df, backend_expr, "result", backend_name)
    """
    def _select_and_extract(df: Any, backend_expr: Any, column_alias: str, backend_name: str) -> List:
        spec = BACKEND_REGISTRY[backend_name]
        family = spec.family
        materialization = spec.materialization

        if family == "ibis":
            # Ibis: use .name(), then PyArrow to avoid pandas NaN/null conflation
            result = df.select(backend_expr.name(column_alias))
            return result.to_pyarrow()[column_alias].to_pylist()

        if family == "pandas":
            # Pandas (via narwhals): use PyArrow to avoid NaN/null conflation
            result = df.select(backend_expr.alias(column_alias))
            return result.to_arrow()[column_alias].to_pylist()

        # Family "narwhals" covers narwhals-polars / narwhals-pandas /
        # narwhals-lazy; the materialization check below collects the lazy one.
        if family in ("polars-eager", "polars-lazy", "narwhals"):
            result = df.select(backend_expr.alias(column_alias))
            if materialization == "lazy":
                result = result.collect()
            return result[column_alias].to_list()

        raise ValueError(f"Unknown backend: {backend_name}")

    return _select_and_extract


@pytest.fixture
def collect_expr():
    """Extract expression results via the relation API.

    Mirrors real-world usage: wraps the DataFrame in a relation, projects
    the expression, and extracts via .to_dict() (which routes through
    Polars for null-safe extraction).

    Usage:
        actual = collect_expr(df, expr)
        actual = collect_expr(df, expr, alias="custom_name")
    """
    def _collect(df, expr, alias="result"):
        import mountainash as ma
        return ma.relation(df).select(expr.name.alias(alias)).to_dict()[alias]
    return _collect


@pytest.fixture
def collect_col():
    """Extract column values via the relation API.

    Usage:
        values = collect_col(df, "age")
    """
    def _collect(df, column):
        import mountainash as ma
        return ma.relation(df).select(column).to_dict()[column]
    return _collect


@pytest.fixture
def assert_parameter_sensitivity(collect_expr) -> Callable:
    """
    Assert that different parameter values produce different results.

    Proves an operation's parameter actually reaches the backend by showing
    that two different parameter values produce two different outputs.

    Usage:
        assert_parameter_sensitivity(
            df, lambda d: ma.col("val").round(d), 1, 2, backend_name
        )
    """
    def _assert_parameter_sensitivity(
        df: Any,
        build_expr: Callable,
        param_a: Any,
        param_b: Any,
        backend_name: str,
    ) -> None:
        expr_a = build_expr(param_a)
        expr_b = build_expr(param_b)
        result_a = collect_expr(df, expr_a)
        result_b = collect_expr(df, expr_b)
        assert result_a != result_b, (
            f"[{backend_name}] param_a={param_a} and param_b={param_b} produced "
            f"identical results {result_a} — parameter may be silently ignored"
        )

    return _assert_parameter_sensitivity


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
        spec = BACKEND_REGISTRY[backend_name]
        if spec.materialization == "deferred":  # ibis
            return result.execute()
        if spec.materialization == "lazy":
            return result.collect() if hasattr(result, "collect") else result
        return result
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
    """Assign exactly one tier marker per test; record closed-by-default violations.

    - Explicit tier markers win. >1 tier marker is a violation (spec: exactly one).
    - Unmarked items get resolve_tier(); None means unclassified → violation.
    """
    from selection.tiers import TIERS, resolve_tier

    untagged, multi = [], []
    for item in items:
        existing = [m.name for m in item.iter_markers() if m.name in TIERS]
        if len(existing) > 1:
            multi.append(item.nodeid)
            continue
        if existing:
            continue  # exactly one explicit tier marker
        tier = resolve_tier(item.nodeid)
        if tier is None:
            untagged.append(item.nodeid)
        else:
            item.add_marker(getattr(pytest.mark, tier))
    config._ma_tier_untagged = untagged
    config._ma_tier_multi = multi
