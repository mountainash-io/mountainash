"""
Cross-backend tests for name/alias operations.

Tests name operations:
- alias: Rename expression/column
- prefix: Add prefix to column name
- suffix: Add suffix to column name
- to_upper: Convert column name to uppercase
- to_lower: Convert column name to lowercase

These tests validate that name operations work consistently across
all backends: Polars, Pandas, Narwhals, and Ibis (DuckDB, Polars, SQLite).
"""

import pytest
import mountainash_expressions as ma
from typing import Any, List


# =============================================================================
# Helper Functions
# =============================================================================

def get_column_names(df: Any, backend_name: str) -> List[str]:
    """Extract column names from a DataFrame for any backend."""
    if backend_name.startswith("ibis-"):
        return list(df.columns)
    elif backend_name in ("polars", "pandas", "narwhals"):
        return df.columns if hasattr(df, 'columns') else list(df.schema.names())
    else:
        raise ValueError(f"Unknown backend: {backend_name}")


def select_expr(df: Any, backend_expr: Any, backend_name: str) -> Any:
    """Select an expression and return the result DataFrame."""
    result = df.select(backend_expr)
    if backend_name.startswith("ibis-"):
        # For Ibis, we need to execute to materialize
        return result
    return result


def get_values_from_result(result: Any, column: str, backend_name: str) -> List:
    """Extract values from result by column name."""
    if backend_name.startswith("ibis-"):
        return result[column].execute().tolist()
    else:
        return result[column].to_list()


# =============================================================================
# Cross-Backend Tests - Alias Operation
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
class TestAliasOperation:
    """Test .name.alias() operation."""

    def test_alias_simple_column(self, backend_name, backend_factory):
        """Test aliasing a simple column reference."""
        data = {
            "age": [25, 30, 35],
            "name": ["Alice", "Bob", "Charlie"]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("age").name.alias("years")
        backend_expr = expr.compile(df)
        result = select_expr(df, backend_expr, backend_name)

        columns = get_column_names(result, backend_name)
        assert "years" in columns, f"[{backend_name}] Expected 'years' in columns, got {columns}"
        assert "age" not in columns, f"[{backend_name}] Did not expect 'age' in columns, got {columns}"

        values = get_values_from_result(result, "years", backend_name)
        assert values == [25, 30, 35], f"[{backend_name}] Expected [25, 30, 35], got {values}"

    def test_alias_computed_expression(self, backend_name, backend_factory):
        """Test aliasing a computed expression."""
        data = {
            "price": [100, 200, 300],
            "quantity": [2, 3, 4]
        }
        df = backend_factory.create(data, backend_name)

        expr = (ma.col("price") * ma.col("quantity")).name.alias("total")
        backend_expr = expr.compile(df)
        result = select_expr(df, backend_expr, backend_name)

        columns = get_column_names(result, backend_name)
        assert "total" in columns, f"[{backend_name}] Expected 'total' in columns, got {columns}"

        values = get_values_from_result(result, "total", backend_name)
        assert values == [200, 600, 1200], f"[{backend_name}] Expected [200, 600, 1200], got {values}"

    def test_alias_after_string_operation(self, backend_name, backend_factory):
        """Test aliasing after a string operation."""
        data = {
            "text": ["hello", "world", "test"]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("text").str.upper().name.alias("TEXT_UPPER")
        backend_expr = expr.compile(df)
        result = select_expr(df, backend_expr, backend_name)

        columns = get_column_names(result, backend_name)
        assert "TEXT_UPPER" in columns, f"[{backend_name}] Expected 'TEXT_UPPER' in columns, got {columns}"

        values = get_values_from_result(result, "TEXT_UPPER", backend_name)
        assert values == ["HELLO", "WORLD", "TEST"], f"[{backend_name}] Expected uppercase, got {values}"

    def test_alias_preserves_data(self, backend_name, backend_factory):
        """Test that alias preserves all data values."""
        data = {
            "value": [1.5, 2.5, 3.5, None, 5.5]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("value").name.alias("renamed")
        backend_expr = expr.compile(df)
        result = select_expr(df, backend_expr, backend_name)

        values = get_values_from_result(result, "renamed", backend_name)
        # Check non-null values
        assert values[0] == 1.5, f"[{backend_name}] First value mismatch"
        assert values[1] == 2.5, f"[{backend_name}] Second value mismatch"
        assert values[2] == 3.5, f"[{backend_name}] Third value mismatch"
        assert values[4] == 5.5, f"[{backend_name}] Fifth value mismatch"
        # Check null is preserved (None or NaN depending on backend)
        assert values[3] is None or (isinstance(values[3], float) and values[3] != values[3]), \
            f"[{backend_name}] Null not preserved: {values[3]}"


# =============================================================================
# Cross-Backend Tests - Prefix Operation
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
class TestPrefixOperation:
    """Test .name.prefix() operation."""

    def test_prefix_simple(self, backend_name, backend_factory):
        """Test adding a prefix to column name."""
        data = {
            "id": [1, 2, 3],
            "value": [10, 20, 30]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("id").name.prefix("customer_")
        backend_expr = expr.compile(df)
        result = select_expr(df, backend_expr, backend_name)

        columns = get_column_names(result, backend_name)
        assert "customer_id" in columns, f"[{backend_name}] Expected 'customer_id' in columns, got {columns}"

        values = get_values_from_result(result, "customer_id", backend_name)
        assert values == [1, 2, 3], f"[{backend_name}] Expected [1, 2, 3], got {values}"

    def test_prefix_empty_string(self, backend_name, backend_factory):
        """Test prefix with empty string (no change)."""
        data = {
            "col": [1, 2, 3]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("col").name.prefix("")
        backend_expr = expr.compile(df)
        result = select_expr(df, backend_expr, backend_name)

        columns = get_column_names(result, backend_name)
        assert "col" in columns, f"[{backend_name}] Expected 'col' in columns, got {columns}"

    def test_prefix_special_characters(self, backend_name, backend_factory):
        """Test prefix with underscore."""
        data = {
            "value": [1, 2, 3]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("value").name.prefix("pre_")
        backend_expr = expr.compile(df)
        result = select_expr(df, backend_expr, backend_name)

        columns = get_column_names(result, backend_name)
        assert "pre_value" in columns, f"[{backend_name}] Expected 'pre_value' in columns, got {columns}"


# =============================================================================
# Cross-Backend Tests - Suffix Operation
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
class TestSuffixOperation:
    """Test .name.suffix() operation."""

    def test_suffix_simple(self, backend_name, backend_factory):
        """Test adding a suffix to column name."""
        data = {
            "price": [100, 200, 300]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("price").name.suffix("_usd")
        backend_expr = expr.compile(df)
        result = select_expr(df, backend_expr, backend_name)

        columns = get_column_names(result, backend_name)
        assert "price_usd" in columns, f"[{backend_name}] Expected 'price_usd' in columns, got {columns}"

        values = get_values_from_result(result, "price_usd", backend_name)
        assert values == [100, 200, 300], f"[{backend_name}] Expected [100, 200, 300], got {values}"

    def test_suffix_empty_string(self, backend_name, backend_factory):
        """Test suffix with empty string (no change)."""
        data = {
            "col": [1, 2, 3]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("col").name.suffix("")
        backend_expr = expr.compile(df)
        result = select_expr(df, backend_expr, backend_name)

        columns = get_column_names(result, backend_name)
        assert "col" in columns, f"[{backend_name}] Expected 'col' in columns, got {columns}"

    def test_suffix_version_number(self, backend_name, backend_factory):
        """Test suffix with version-like string."""
        data = {
            "config": ["a", "b", "c"]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("config").name.suffix("_v2")
        backend_expr = expr.compile(df)
        result = select_expr(df, backend_expr, backend_name)

        columns = get_column_names(result, backend_name)
        assert "config_v2" in columns, f"[{backend_name}] Expected 'config_v2' in columns, got {columns}"


# =============================================================================
# Cross-Backend Tests - to_upper Operation
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
class TestToUpperOperation:
    """Test .name.name_to_upper() operation."""

    def test_to_upper_lowercase_name(self, backend_name, backend_factory):
        """Test converting lowercase column name to uppercase."""
        data = {
            "age": [25, 30, 35]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("age").name.name_to_upper()
        backend_expr = expr.compile(df)
        result = select_expr(df, backend_expr, backend_name)

        columns = get_column_names(result, backend_name)
        assert "AGE" in columns, f"[{backend_name}] Expected 'AGE' in columns, got {columns}"

        values = get_values_from_result(result, "AGE", backend_name)
        assert values == [25, 30, 35], f"[{backend_name}] Expected [25, 30, 35], got {values}"

    def test_to_upper_mixed_case(self, backend_name, backend_factory):
        """Test to_upper on mixed case column name."""
        data = {
            "firstName": ["Alice", "Bob", "Charlie"]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("firstName").name.name_to_upper()
        backend_expr = expr.compile(df)
        result = select_expr(df, backend_expr, backend_name)

        columns = get_column_names(result, backend_name)
        assert "FIRSTNAME" in columns, f"[{backend_name}] Expected 'FIRSTNAME' in columns, got {columns}"

    def test_to_upper_already_uppercase(self, backend_name, backend_factory):
        """Test to_upper on already uppercase column name."""
        data = {
            "ID": [1, 2, 3]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("ID").name.name_to_upper()
        backend_expr = expr.compile(df)
        result = select_expr(df, backend_expr, backend_name)

        columns = get_column_names(result, backend_name)
        assert "ID" in columns, f"[{backend_name}] Expected 'ID' in columns, got {columns}"


# =============================================================================
# Cross-Backend Tests - to_lower Operation
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
class TestToLowerOperation:
    """Test .name.name_to_lower() operation."""

    def test_to_lower_uppercase_name(self, backend_name, backend_factory):
        """Test converting uppercase column name to lowercase."""
        data = {
            "AGE": [25, 30, 35]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("AGE").name.name_to_lower()
        backend_expr = expr.compile(df)
        result = select_expr(df, backend_expr, backend_name)

        columns = get_column_names(result, backend_name)
        assert "age" in columns, f"[{backend_name}] Expected 'age' in columns, got {columns}"

        values = get_values_from_result(result, "age", backend_name)
        assert values == [25, 30, 35], f"[{backend_name}] Expected [25, 30, 35], got {values}"

    def test_to_lower_mixed_case(self, backend_name, backend_factory):
        """Test to_lower on mixed case column name."""
        data = {
            "FirstName": ["Alice", "Bob", "Charlie"]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("FirstName").name.name_to_lower()
        backend_expr = expr.compile(df)
        result = select_expr(df, backend_expr, backend_name)

        columns = get_column_names(result, backend_name)
        assert "firstname" in columns, f"[{backend_name}] Expected 'firstname' in columns, got {columns}"

    def test_to_lower_already_lowercase(self, backend_name, backend_factory):
        """Test to_lower on already lowercase column name."""
        data = {
            "id": [1, 2, 3]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("id").name.name_to_lower()
        backend_expr = expr.compile(df)
        result = select_expr(df, backend_expr, backend_name)

        columns = get_column_names(result, backend_name)
        assert "id" in columns, f"[{backend_name}] Expected 'id' in columns, got {columns}"


# =============================================================================
# Cross-Backend Tests - Chained Name Operations
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
class TestChainedNameOperations:
    """Test chaining name operations with other operations."""

    def test_arithmetic_then_alias(self, backend_name, backend_factory):
        """Test arithmetic operation followed by alias."""
        data = {
            "a": [10, 20, 30],
            "b": [1, 2, 3]
        }
        df = backend_factory.create(data, backend_name)

        expr = (ma.col("a") + ma.col("b")).name.alias("sum")
        backend_expr = expr.compile(df)
        result = select_expr(df, backend_expr, backend_name)

        columns = get_column_names(result, backend_name)
        assert "sum" in columns, f"[{backend_name}] Expected 'sum' in columns, got {columns}"

        values = get_values_from_result(result, "sum", backend_name)
        assert values == [11, 22, 33], f"[{backend_name}] Expected [11, 22, 33], got {values}"

    def test_comparison_then_alias(self, backend_name, backend_factory):
        """Test comparison operation followed by alias."""
        data = {
            "value": [10, 20, 30]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("value").gt(15).name.alias("is_large")
        backend_expr = expr.compile(df)
        result = select_expr(df, backend_expr, backend_name)

        columns = get_column_names(result, backend_name)
        assert "is_large" in columns, f"[{backend_name}] Expected 'is_large' in columns, got {columns}"

        values = get_values_from_result(result, "is_large", backend_name)
        assert values == [False, True, True], f"[{backend_name}] Expected [False, True, True], got {values}"

    def test_null_check_then_alias(self, backend_name, backend_factory):
        """Test null check followed by alias."""
        data = {
            "value": [1, None, 3]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("value").is_null().name.alias("missing")
        backend_expr = expr.compile(df)
        result = select_expr(df, backend_expr, backend_name)

        columns = get_column_names(result, backend_name)
        assert "missing" in columns, f"[{backend_name}] Expected 'missing' in columns, got {columns}"

        values = get_values_from_result(result, "missing", backend_name)
        assert values == [False, True, False], f"[{backend_name}] Expected [False, True, False], got {values}"


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
class TestNameEdgeCases:
    """Test edge cases for name operations."""

    def test_alias_with_spaces(self, backend_name, backend_factory):
        """Test alias with spaces in name."""
        data = {
            "col": [1, 2, 3]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("col").name.alias("my column")
        backend_expr = expr.compile(df)
        result = select_expr(df, backend_expr, backend_name)

        columns = get_column_names(result, backend_name)
        assert "my column" in columns, f"[{backend_name}] Expected 'my column' in columns, got {columns}"

    def test_alias_with_numbers(self, backend_name, backend_factory):
        """Test alias starting with numbers."""
        data = {
            "col": [1, 2, 3]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("col").name.alias("123_column")
        backend_expr = expr.compile(df)
        result = select_expr(df, backend_expr, backend_name)

        columns = get_column_names(result, backend_name)
        assert "123_column" in columns, f"[{backend_name}] Expected '123_column' in columns, got {columns}"

    def test_long_column_name(self, backend_name, backend_factory):
        """Test alias with very long name."""
        data = {
            "x": [1, 2, 3]
        }
        df = backend_factory.create(data, backend_name)

        long_name = "this_is_a_very_long_column_name_that_might_cause_issues_in_some_backends"
        expr = ma.col("x").name.alias(long_name)
        backend_expr = expr.compile(df)
        result = select_expr(df, backend_expr, backend_name)

        columns = get_column_names(result, backend_name)
        assert long_name in columns, f"[{backend_name}] Expected long name in columns, got {columns}"

    def test_unicode_column_name(self, backend_name, backend_factory):
        """Test alias with unicode characters."""
        data = {
            "col": [1, 2, 3]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("col").name.alias("temperature_\u00b0C")
        backend_expr = expr.compile(df)
        result = select_expr(df, backend_expr, backend_name)

        columns = get_column_names(result, backend_name)
        assert "temperature_\u00b0C" in columns, f"[{backend_name}] Expected unicode name in columns, got {columns}"
