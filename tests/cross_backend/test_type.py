"""
Cross-backend tests for type/cast operations.

Tests type operations:
- cast: Convert expression to different data type

These tests validate that type casting works consistently across
all backends: Polars, Pandas, Narwhals, and Ibis (DuckDB, Polars, SQLite).

Note: Different backends use different dtype specifications:
- Polars: pl.Int64, pl.Float64, pl.Utf8, pl.Boolean
- Narwhals: nw.Int64, nw.Float64, nw.String, nw.Boolean
- Ibis: "int64", "float64", "string", "boolean"
"""

import pytest
import math
import mountainash_expressions as ma
from typing import Any, List


# =============================================================================
# Backend-specific dtype mappings
# =============================================================================

def get_int64_dtype(backend_name: str) -> Any:
    """Get int64 dtype for the given backend."""
    if backend_name == "polars":
        import polars as pl
        return pl.Int64
    elif backend_name in ("pandas", "narwhals"):
        import narwhals as nw
        return nw.Int64
    elif backend_name.startswith("ibis-"):
        return "int64"
    else:
        raise ValueError(f"Unknown backend: {backend_name}")


def get_float64_dtype(backend_name: str) -> Any:
    """Get float64 dtype for the given backend."""
    if backend_name == "polars":
        import polars as pl
        return pl.Float64
    elif backend_name in ("pandas", "narwhals"):
        import narwhals as nw
        return nw.Float64
    elif backend_name.startswith("ibis-"):
        return "float64"
    else:
        raise ValueError(f"Unknown backend: {backend_name}")


def get_string_dtype(backend_name: str) -> Any:
    """Get string dtype for the given backend."""
    if backend_name == "polars":
        import polars as pl
        return pl.Utf8
    elif backend_name in ("pandas", "narwhals"):
        import narwhals as nw
        return nw.String
    elif backend_name.startswith("ibis-"):
        return "string"
    else:
        raise ValueError(f"Unknown backend: {backend_name}")


def get_boolean_dtype(backend_name: str) -> Any:
    """Get boolean dtype for the given backend."""
    if backend_name == "polars":
        import polars as pl
        return pl.Boolean
    elif backend_name in ("pandas", "narwhals"):
        import narwhals as nw
        return nw.Boolean
    elif backend_name.startswith("ibis-"):
        return "boolean"
    else:
        raise ValueError(f"Unknown backend: {backend_name}")


def get_int32_dtype(backend_name: str) -> Any:
    """Get int32 dtype for the given backend."""
    if backend_name == "polars":
        import polars as pl
        return pl.Int32
    elif backend_name in ("pandas", "narwhals"):
        import narwhals as nw
        return nw.Int32
    elif backend_name.startswith("ibis-"):
        return "int32"
    else:
        raise ValueError(f"Unknown backend: {backend_name}")


# =============================================================================
# Helper Functions
# =============================================================================

def select_and_extract(df: Any, backend_expr: Any, column_alias: str, backend_name: str) -> List:
    """Select expression and extract values."""
    if backend_name.startswith("ibis-"):
        result = df.select(backend_expr.name(column_alias))
        return result[column_alias].execute().tolist()
    else:
        result = df.select(backend_expr.alias(column_alias))
        return result[column_alias].to_list()


# =============================================================================
# Cross-Backend Tests - Cast to Integer
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
])
class TestCastToInteger:
    """Test casting to integer types."""

    def test_cast_float_to_int(self, backend_name, backend_factory):
        """Test casting float values to int (truncates toward zero)."""
        data = {
            "value": [1.1, 2.9, 3.5, -1.7, -2.3]
        }
        df = backend_factory.create(data, backend_name)

        dtype = get_int64_dtype(backend_name)
        expr = ma.col("value").cast(dtype)
        backend_expr = expr.compile(df)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        # Float to int truncates toward zero
        expected = [1, 2, 3, -1, -2]
        assert values == expected, f"[{backend_name}] Expected {expected}, got {values}"

    def test_cast_string_to_int(self, backend_name, backend_factory):
        """Test casting string numeric values to int."""
        data = {
            "value": ["10", "20", "30", "40", "50"]
        }
        df = backend_factory.create(data, backend_name)

        dtype = get_int64_dtype(backend_name)
        expr = ma.col("value").cast(dtype)
        backend_expr = expr.compile(df)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        expected = [10, 20, 30, 40, 50]
        assert values == expected, f"[{backend_name}] Expected {expected}, got {values}"

    def test_cast_bool_to_int(self, backend_name, backend_factory):
        """Test casting boolean to int (True=1, False=0)."""
        data = {
            "flag": [True, False, True, False, True]
        }
        df = backend_factory.create(data, backend_name)

        dtype = get_int64_dtype(backend_name)
        expr = ma.col("flag").cast(dtype)
        backend_expr = expr.compile(df)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        expected = [1, 0, 1, 0, 1]
        assert values == expected, f"[{backend_name}] Expected {expected}, got {values}"

    def test_cast_int64_to_int32(self, backend_name, backend_factory):
        """Test casting between integer types."""
        data = {
            "value": [100, 200, 300]
        }
        df = backend_factory.create(data, backend_name)

        dtype = get_int32_dtype(backend_name)
        expr = ma.col("value").cast(dtype)
        backend_expr = expr.compile(df)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        expected = [100, 200, 300]
        assert values == expected, f"[{backend_name}] Expected {expected}, got {values}"


# =============================================================================
# Cross-Backend Tests - Cast to Float
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
])
class TestCastToFloat:
    """Test casting to float types."""

    def test_cast_int_to_float(self, backend_name, backend_factory):
        """Test casting integer values to float."""
        data = {
            "value": [1, 2, 3, 4, 5]
        }
        df = backend_factory.create(data, backend_name)

        dtype = get_float64_dtype(backend_name)
        expr = ma.col("value").cast(dtype)
        backend_expr = expr.compile(df)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        expected = [1.0, 2.0, 3.0, 4.0, 5.0]
        assert values == expected, f"[{backend_name}] Expected {expected}, got {values}"

    def test_cast_string_to_float(self, backend_name, backend_factory):
        """Test casting string numeric values to float."""
        data = {
            "value": ["1.5", "2.5", "3.5"]
        }
        df = backend_factory.create(data, backend_name)

        dtype = get_float64_dtype(backend_name)
        expr = ma.col("value").cast(dtype)
        backend_expr = expr.compile(df)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        expected = [1.5, 2.5, 3.5]
        assert values == expected, f"[{backend_name}] Expected {expected}, got {values}"

    def test_cast_bool_to_float(self, backend_name, backend_factory):
        """Test casting boolean to float (True=1.0, False=0.0)."""
        data = {
            "flag": [True, False, True]
        }
        df = backend_factory.create(data, backend_name)

        dtype = get_float64_dtype(backend_name)
        expr = ma.col("flag").cast(dtype)
        backend_expr = expr.compile(df)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        expected = [1.0, 0.0, 1.0]
        assert values == expected, f"[{backend_name}] Expected {expected}, got {values}"


# =============================================================================
# Cross-Backend Tests - Cast to String
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
])
class TestCastToString:
    """Test casting to string type."""

    def test_cast_int_to_string(self, backend_name, backend_factory):
        """Test casting integer to string."""
        data = {
            "value": [1, 2, 3, 100, 999]
        }
        df = backend_factory.create(data, backend_name)

        dtype = get_string_dtype(backend_name)
        expr = ma.col("value").cast(dtype)
        backend_expr = expr.compile(df)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        expected = ["1", "2", "3", "100", "999"]
        assert values == expected, f"[{backend_name}] Expected {expected}, got {values}"

    def test_cast_float_to_string(self, backend_name, backend_factory):
        """Test casting float to string."""
        data = {
            "value": [1.5, 2.0, 3.75]
        }
        df = backend_factory.create(data, backend_name)

        dtype = get_string_dtype(backend_name)
        expr = ma.col("value").cast(dtype)
        backend_expr = expr.compile(df)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        # Check that conversion happened (format may vary by backend)
        assert len(values) == 3, f"[{backend_name}] Expected 3 values"
        # First value should contain "1" and "5" (for 1.5)
        assert "1" in values[0] and "5" in values[0], f"[{backend_name}] Expected '1.5', got {values[0]}"

    def test_cast_bool_to_string(self, backend_name, backend_factory):
        """Test casting boolean to string."""
        data = {
            "flag": [True, False, True]
        }
        df = backend_factory.create(data, backend_name)

        dtype = get_string_dtype(backend_name)
        expr = ma.col("flag").cast(dtype)
        backend_expr = expr.compile(df)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        # Boolean string representation varies by backend
        # Could be "true"/"false", "True"/"False", "1"/"0"
        assert len(values) == 3, f"[{backend_name}] Expected 3 values"
        # Check that True and False produce different strings
        assert values[0] != values[1], f"[{backend_name}] True and False should differ: {values}"


# =============================================================================
# Cross-Backend Tests - Cast to Boolean
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
])
class TestCastToBoolean:
    """Test casting to boolean type."""

    def test_cast_int_to_bool(self, backend_name, backend_factory):
        """Test casting integer to boolean (0=False, nonzero=True)."""
        data = {
            "value": [0, 1, 2, -1, 0]
        }
        df = backend_factory.create(data, backend_name)

        dtype = get_boolean_dtype(backend_name)
        expr = ma.col("value").cast(dtype)
        backend_expr = expr.compile(df)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        expected = [False, True, True, True, False]
        assert values == expected, f"[{backend_name}] Expected {expected}, got {values}"

    def test_cast_float_to_bool(self, backend_name, backend_factory):
        """Test casting float to boolean (0.0=False, nonzero=True)."""
        data = {
            "value": [0.0, 1.0, 0.5, -0.5, 0.0]
        }
        df = backend_factory.create(data, backend_name)

        dtype = get_boolean_dtype(backend_name)
        expr = ma.col("value").cast(dtype)
        backend_expr = expr.compile(df)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        expected = [False, True, True, True, False]
        assert values == expected, f"[{backend_name}] Expected {expected}, got {values}"


# =============================================================================
# Cross-Backend Tests - Cast with Nulls
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
])
class TestCastWithNulls:
    """Test casting with null values."""

    def test_cast_with_null_int_to_float(self, backend_name, backend_factory):
        """Test that nulls are preserved when casting int to float."""
        data = {
            "value": [1, None, 3, None, 5]
        }
        df = backend_factory.create(data, backend_name)

        dtype = get_float64_dtype(backend_name)
        expr = ma.col("value").cast(dtype)
        backend_expr = expr.compile(df)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        # Check non-null values
        assert values[0] == 1.0, f"[{backend_name}] First value: {values[0]}"
        assert values[2] == 3.0, f"[{backend_name}] Third value: {values[2]}"
        assert values[4] == 5.0, f"[{backend_name}] Fifth value: {values[4]}"

        # Check nulls are preserved (None or NaN)
        assert values[1] is None or (isinstance(values[1], float) and math.isnan(values[1])), \
            f"[{backend_name}] Second value should be null: {values[1]}"
        assert values[3] is None or (isinstance(values[3], float) and math.isnan(values[3])), \
            f"[{backend_name}] Fourth value should be null: {values[3]}"

    def test_cast_with_null_float_to_string(self, backend_name, backend_factory):
        """Test that nulls are preserved when casting float to string."""
        data = {
            "value": [1.5, None, 3.5]
        }
        df = backend_factory.create(data, backend_name)

        dtype = get_string_dtype(backend_name)
        expr = ma.col("value").cast(dtype)
        backend_expr = expr.compile(df)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        # Check that first and third are strings
        assert isinstance(values[0], str), f"[{backend_name}] First should be string: {values[0]}"
        assert isinstance(values[2], str), f"[{backend_name}] Third should be string: {values[2]}"

        # Check null is preserved
        assert values[1] is None, f"[{backend_name}] Second value should be null: {values[1]}"


# =============================================================================
# Cross-Backend Tests - Cast in Expressions
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
])
class TestCastInExpressions:
    """Test using cast within larger expressions."""

    def test_cast_then_arithmetic(self, backend_name, backend_factory):
        """Test casting then performing arithmetic."""
        data = {
            "value": ["10", "20", "30"]
        }
        df = backend_factory.create(data, backend_name)

        dtype = get_int64_dtype(backend_name)
        expr = ma.col("value").cast(dtype) * 2
        backend_expr = expr.compile(df)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        expected = [20, 40, 60]
        assert values == expected, f"[{backend_name}] Expected {expected}, got {values}"

    def test_cast_then_comparison(self, backend_name, backend_factory):
        """Test casting then performing comparison."""
        data = {
            "value": ["5", "15", "25"]
        }
        df = backend_factory.create(data, backend_name)

        dtype = get_int64_dtype(backend_name)
        expr = ma.col("value").cast(dtype).gt(10)
        backend_expr = expr.compile(df)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        expected = [False, True, True]
        assert values == expected, f"[{backend_name}] Expected {expected}, got {values}"

    def test_arithmetic_then_cast(self, backend_name, backend_factory):
        """Test arithmetic then casting result."""
        data = {
            "a": [10, 20, 30],
            "b": [3, 3, 3]
        }
        df = backend_factory.create(data, backend_name)

        dtype = get_string_dtype(backend_name)
        expr = (ma.col("a") + ma.col("b")).cast(dtype)
        backend_expr = expr.compile(df)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        expected = ["13", "23", "33"]
        assert values == expected, f"[{backend_name}] Expected {expected}, got {values}"

    def test_cast_with_alias(self, backend_name, backend_factory):
        """Test casting combined with alias."""
        data = {
            "price": [100, 200, 300]
        }
        df = backend_factory.create(data, backend_name)

        dtype = get_float64_dtype(backend_name)
        expr = ma.col("price").cast(dtype).name.alias("price_float")
        backend_expr = expr.compile(df)

        # Select directly without additional aliasing
        if backend_name.startswith("ibis-"):
            result = df.select(backend_expr)
            values = result["price_float"].execute().tolist()
        else:
            result = df.select(backend_expr)
            values = result["price_float"].to_list()

        expected = [100.0, 200.0, 300.0]
        assert values == expected, f"[{backend_name}] Expected {expected}, got {values}"


# =============================================================================
# Edge Cases
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
])
class TestCastEdgeCases:
    """Test edge cases for cast operations."""

    def test_cast_same_type(self, backend_name, backend_factory):
        """Test casting to the same type (should be no-op)."""
        data = {
            "value": [1, 2, 3]
        }
        df = backend_factory.create(data, backend_name)

        dtype = get_int64_dtype(backend_name)
        expr = ma.col("value").cast(dtype)
        backend_expr = expr.compile(df)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        expected = [1, 2, 3]
        assert values == expected, f"[{backend_name}] Expected {expected}, got {values}"

    def test_cast_negative_float_to_int(self, backend_name, backend_factory):
        """Test casting negative floats to int (truncation behavior)."""
        data = {
            "value": [-1.9, -2.1, -3.5]
        }
        df = backend_factory.create(data, backend_name)

        dtype = get_int64_dtype(backend_name)
        expr = ma.col("value").cast(dtype)
        backend_expr = expr.compile(df)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        # Truncation toward zero: -1.9 -> -1, -2.1 -> -2, -3.5 -> -3
        expected = [-1, -2, -3]
        assert values == expected, f"[{backend_name}] Expected {expected}, got {values}"

    def test_cast_zero_values(self, backend_name, backend_factory):
        """Test casting zero values."""
        data = {
            "value": [0, 0, 0]  # All same type to avoid mixed-type errors
        }
        df = backend_factory.create(data, backend_name)

        dtype = get_string_dtype(backend_name)
        expr = ma.col("value").cast(dtype)
        backend_expr = expr.compile(df)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        # All should be string representations of zero
        assert len(values) == 3, f"[{backend_name}] Expected 3 values"
        for v in values:
            assert "0" in v, f"[{backend_name}] Expected '0' in {v}"

    def test_cast_large_int_to_float(self, backend_name, backend_factory):
        """Test casting large integers to float (precision check)."""
        data = {
            "value": [1000000, 2000000, 3000000]
        }
        df = backend_factory.create(data, backend_name)

        dtype = get_float64_dtype(backend_name)
        expr = ma.col("value").cast(dtype)
        backend_expr = expr.compile(df)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        expected = [1000000.0, 2000000.0, 3000000.0]
        assert values == expected, f"[{backend_name}] Expected {expected}, got {values}"
