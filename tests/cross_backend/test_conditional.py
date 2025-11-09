"""
Cross-backend tests for conditional operations.

Tests conditional expressions:
- WHEN-THEN-OTHERWISE
- Nested conditionals
- COALESCE (first non-null value)
- FILL_NULL (replace nulls)
- Conditionals with boolean logic
- Conditionals with arithmetic
- Conditionals with string operations

These tests validate that conditional operations work consistently across
all backends: Polars, Pandas, Narwhals, and Ibis (DuckDB, Polars, SQLite).
"""

import pytest
import mountainash_expressions as ma


# =============================================================================
# Cross-Backend Tests - Basic Conditionals
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
class TestBasicConditionals:
    """Test basic when-then-otherwise conditionals."""

    def test_when_then_otherwise_string(self, backend_name, backend_factory, select_and_extract):
        """Test when-then-otherwise with string values."""
        data = {
            "age": [15, 25, 35, 45, 55, 65, 75],
            "name": ["Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace"]
        }
        df = backend_factory.create(data, backend_name)

        # Age category: senior if >= 65
        expr = ma.when(ma.col("age") >= 65).then("senior").otherwise("non-senior")
        backend_expr = expr.compile(df)

        actual = select_and_extract(df, backend_expr, "category", backend_name)

        expected = ["non-senior", "non-senior", "non-senior", "non-senior", "non-senior", "senior", "senior"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_when_then_otherwise_numeric(self, backend_name, backend_factory, select_and_extract):
        """Test when-then-otherwise with numeric values."""
        data = {
            "age": [15, 25, 35, 45, 55, 65, 75]
        }
        df = backend_factory.create(data, backend_name)

        # Binary flag: 1 if > 50, else 0
        expr = ma.when(ma.col("age") > 50).then(1).otherwise(0)
        backend_expr = expr.compile(df)

        actual = select_and_extract(df, backend_expr, "flag", backend_name)

        expected = [0, 0, 0, 0, 1, 1, 1]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )


# =============================================================================
# Cross-Backend Tests - Nested Conditionals
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
class TestNestedConditionals:
    """Test nested when-then-otherwise conditions."""

    def test_nested_when_letter_grades(self, backend_name, backend_factory, select_and_extract):
        """Test nested conditionals for letter grades."""
        data = {
            "score": [95, 85, 75, 65, 55]
        }
        df = backend_factory.create(data, backend_name)

        # Letter grades: A (>=90), B (>=80), C (>=70), D (<70)
        expr = ma.when(ma.col("score") >= 90).then("A").otherwise(
            ma.when(ma.col("score") >= 80).then("B").otherwise(
                ma.when(ma.col("score") >= 70).then("C").otherwise("D")
            )
        )
        backend_expr = expr.compile(df)

        actual = select_and_extract(df, backend_expr, "grade", backend_name)

        expected = ["A", "B", "C", "D", "D"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )


# =============================================================================
# Cross-Backend Tests - Coalesce
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
class TestCoalesce:
    """Test coalesce - return first non-null value."""

    def test_coalesce_multiple_columns(self, backend_name, backend_factory, select_and_extract):
        """Test coalesce across multiple columns."""
        data = {
            "phone_mobile": ["555-1234", None, "555-5678", None],
            "phone_home": [None, "555-2345", None, "555-6789"],
            "phone_work": ["555-9999", "555-8888", "555-7777", None]
        }
        df = backend_factory.create(data, backend_name)

        # Get first available phone number
        expr = ma.coalesce(ma.col("phone_mobile"), ma.col("phone_home"), ma.col("phone_work"))
        backend_expr = expr.compile(df)

        actual = select_and_extract(df, backend_expr, "phone", backend_name)

        expected = ["555-1234", "555-2345", "555-5678", "555-6789"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )


# =============================================================================
# Cross-Backend Tests - Fill Null
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
class TestFillNull:
    """Test fill_null - replace nulls with a value."""

    def test_fill_null_with_zero(self, backend_name, backend_factory, select_and_extract):
        """Test filling null values with zero."""
        data = {
            "score": [100, None, 85, None, 90],
            "name": ["Alice", "Bob", "Charlie", "David", "Eve"]
        }
        df = backend_factory.create(data, backend_name)

        # Fill null scores with 0
        expr = ma.col("score").fill_null(0)
        backend_expr = expr.compile(df)

        actual = select_and_extract(df, backend_expr, "score_filled", backend_name)

        expected = [100, 0, 85, 0, 90]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )


# =============================================================================
# Integration Tests - Conditionals with Boolean Logic
# =============================================================================

@pytest.mark.integration
@pytest.mark.parametrize("backend_name", [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",

])
class TestConditionalsWithBooleanLogic:
    """Test conditionals combined with boolean operations."""

    def test_when_with_and_condition(self, backend_name, backend_factory, select_and_extract):
        """Test when with AND condition."""
        data = {
            "age": [15, 25, 35, 45],
            "active": [True, True, False, True],
            "score": [70, 85, 90, 95]
        }
        df = backend_factory.create(data, backend_name)

        # Eligible if age >= 18 AND active
        expr = ma.when((ma.col("age") >= 18) & ma.col("active")).then("eligible").otherwise("not eligible")
        backend_expr = expr.compile(df)

        actual = select_and_extract(df, backend_expr, "status", backend_name)

        expected = ["not eligible", "eligible", "not eligible", "eligible"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_when_with_range_condition(self, backend_name, backend_factory, select_and_extract):
        """Test when with range condition (score between 80 and 90)."""
        data = {
            "age": [15, 25, 35, 45],
            "active": [True, True, False, True],
            "score": [70, 85, 90, 95]
        }
        df = backend_factory.create(data, backend_name)

        # Grade B if 80 <= score < 90
        expr = ma.when((ma.col("score") >= 80) & (ma.col("score") < 90)).then("B").otherwise("other")
        backend_expr = expr.compile(df)

        actual = select_and_extract(df, backend_expr, "grade", backend_name)

        expected = ["other", "B", "other", "other"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )


# =============================================================================
# Integration Tests - Conditionals with Arithmetic
# =============================================================================

@pytest.mark.integration
@pytest.mark.parametrize("backend_name", [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",

])
class TestConditionalsWithArithmetic:
    """Test conditionals combined with arithmetic operations."""

    def test_conditional_arithmetic_transformation(self, backend_name, backend_factory, select_and_extract):
        """Test conditional that applies arithmetic transformation."""
        data = {
            "value": [10, 20, 30, 40, 50]
        }
        df = backend_factory.create(data, backend_name)

        # Double if > 25, otherwise keep as is
        expr = ma.when(ma.col("value") > 25).then(ma.col("value") * 2).otherwise(ma.col("value"))
        backend_expr = expr.compile(df)

        actual = select_and_extract(df, backend_expr, "result", backend_name)

        expected = [10, 20, 60, 80, 100]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )


# =============================================================================
# Integration Tests - Conditionals with String Operations
# =============================================================================

@pytest.mark.integration
@pytest.mark.parametrize("backend_name", [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",

])
class TestConditionalsWithStringOperations:
    """Test conditionals combined with string operations."""

    def test_conditional_string_case(self, backend_name, backend_factory, select_and_extract):
        """Test conditional with string case transformations."""
        data = {
            "name": ["alice", "BOB", "Charlie", None],
            "age": [25, 30, 35, 40]
        }
        df = backend_factory.create(data, backend_name)

        # Uppercase if age > 28, otherwise lowercase
        expr = ma.when(ma.col("age") > 28).then(
            ma.col("name").str_upper()
        ).otherwise(
            ma.col("name").str_lower()
        )
        backend_expr = expr.compile(df)

        actual = select_and_extract(df, backend_expr, "formatted_name", backend_name)

        # alice (age 25, <=28) -> lowercase -> alice
        # BOB (age 30, >28) -> uppercase -> BOB
        # Charlie (age 35, >28) -> uppercase -> CHARLIE
        # None (age 40, >28) -> None stays None
        assert actual[0] == "alice", f"[{backend_name}] Expected 'alice', got {actual[0]}"
        assert actual[1] == "BOB", f"[{backend_name}] Expected 'BOB', got {actual[1]}"
        assert actual[2] == "CHARLIE", f"[{backend_name}] Expected 'CHARLIE', got {actual[2]}"
        assert actual[3] is None, f"[{backend_name}] Expected None, got {actual[3]}"


# =============================================================================
# Edge Case Tests
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
class TestConditionalEdgeCases:
    """Test edge cases for conditional operations."""

    def test_all_nulls_coalesce(self, backend_name, backend_factory, select_and_extract):
        """Test coalesce when all values are null."""
        # DuckDB doesn't support creating tables with all NULL columns
        if backend_name == "ibis-duckdb":
            pytest.xfail(
                "DuckDB does not support creating tables with all NULL columns. "
                "This is a genuine backend limitation, not a bug."
            )

        data = {
            "a": [None, None, None],
            "b": [None, None, None],
            "c": [None, None, None]
        }
        df = backend_factory.create(data, backend_name)

        # Coalesce with all nulls should return null
        expr = ma.coalesce(ma.col("a"), ma.col("b"), ma.col("c"))
        backend_expr = expr.compile(df)

        actual = select_and_extract(df, backend_expr, "result", backend_name)

        expected = [None, None, None]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_when_all_false(self, backend_name, backend_factory, select_and_extract):
        """Test when condition that's always false."""
        data = {
            "value": [1, 2, 3, 4, 5]
        }
        df = backend_factory.create(data, backend_name)

        # Condition never true, should always go to otherwise
        expr = ma.when(ma.col("value") > 100).then("big").otherwise("small")
        backend_expr = expr.compile(df)

        actual = select_and_extract(df, backend_expr, "result", backend_name)

        expected = ["small", "small", "small", "small", "small"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_when_all_true(self, backend_name, backend_factory, select_and_extract):
        """Test when condition that's always true."""
        data = {
            "value": [1, 2, 3, 4, 5]
        }
        df = backend_factory.create(data, backend_name)

        # Condition always true, should never go to otherwise
        expr = ma.when(ma.col("value") > 0).then("positive").otherwise("non-positive")
        backend_expr = expr.compile(df)

        actual = select_and_extract(df, backend_expr, "result", backend_name)

        expected = ["positive", "positive", "positive", "positive", "positive"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )
