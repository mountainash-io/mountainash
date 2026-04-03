"""
Cross-backend tests for arithmetic operations.

Tests basic arithmetic operations:
- Addition, subtraction, multiplication, division
- Modulo, power, floor division
- Python magic operators (+, -, *, /, //, %, **)
- Chaining arithmetic operations
- Edge cases (division by zero, negative numbers)

These tests validate that arithmetic works consistently across
all backends: Polars, Pandas, Narwhals, and Ibis (DuckDB, Polars, SQLite).
"""

import pytest
import mountainash.expressions as ma


# =============================================================================
# Cross-Backend Tests - Basic Arithmetic
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.arithmetic
@pytest.mark.parametrize("backend_name", [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",

])
class TestBasicArithmetic:
    """Test basic arithmetic operations across all backends."""

    def test_addition(self, backend_name, backend_factory, collect_expr):
        """Test addition operation."""
        data = {
            "a": [10, 20, 30, 40, 50],
            "b": [2, 3, 4, 5, 6]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a").add(ma.col("b"))

        # Use helper - replaces 9 lines with 1!
        actual = collect_expr(df, expr)

        expected = [12, 23, 34, 45, 56]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_subtraction(self, backend_name, backend_factory, collect_expr):
        """Test subtraction operation."""
        data = {
            "a": [10, 20, 30, 40, 50],
            "b": [2, 3, 4, 5, 6]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a").subtract(ma.col("b"))

        actual = collect_expr(df, expr)

        expected = [8, 17, 26, 35, 44]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_multiplication(self, backend_name, backend_factory, collect_expr):
        """Test multiplication operation."""
        data = {
            "a": [10, 20, 30, 40, 50],
            "c": [1, 2, 3, 4, 5]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a").multiply(ma.col("c"))

        actual = collect_expr(df, expr)


        expected = [10, 40, 90, 160, 250]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_division(self, backend_name, backend_factory, collect_expr):
        """Test division operation."""
        data = {
            "a": [10, 20, 30, 40, 50],
            "b": [2, 3, 4, 5, 6]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a").divide(ma.col("b"))

        actual = collect_expr(df, expr)

        expected = [10/2, 20/3, 30/4, 40/5, 50/6]

        # Check each value with tolerance for floating point
        for i, (act, exp) in enumerate(zip(actual, expected)):
            assert abs(act - exp) < 0.0001, (
                f"[{backend_name}] At index {i}: expected {exp}, got {act}"
            )

    def test_modulo(self, backend_name, backend_factory, collect_expr):
        """Test modulo operation."""
        data = {
            "a": [10, 20, 30, 40, 50],
            "b": [2, 3, 4, 5, 6]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a").modulo(ma.col("b"))

        actual = collect_expr(df, expr)

        expected = [0, 2, 2, 0, 2]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_power(self, backend_name, backend_factory, collect_expr):
        """Test power operation."""
        data = {
            "c": [1, 2, 3, 4, 5]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("c").power(2)

        actual = collect_expr(df, expr)

        expected = [1, 4, 9, 16, 25]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_floor_division(self, backend_name, backend_factory, collect_expr):
        """Test floor division operation."""
        data = {
            "a": [10, 20, 30, 40, 50],
            "b": [2, 3, 4, 5, 6]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a").floor_divide(ma.col("b"))

        actual = collect_expr(df, expr)

        expected = [5, 6, 7, 8, 8]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )


# =============================================================================
# Cross-Backend Tests - Python Magic Operators
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.arithmetic
@pytest.mark.parametrize("backend_name", [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",

])
class TestPythonMagicOperators:
    """Test Python magic operators (+, -, *, /, etc.)."""

    def test_plus_operator(self, backend_name, backend_factory, collect_expr):
        """Test + operator."""
        data = {
            "x": [10, 20, 30],
            "y": [2, 4, 5]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("x") + ma.col("y")

        actual = collect_expr(df, expr)

        expected = [12, 24, 35]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_minus_operator(self, backend_name, backend_factory, collect_expr):
        """Test - operator."""
        data = {
            "x": [10, 20, 30],
            "y": [2, 4, 5]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("x") - ma.col("y")

        actual = collect_expr(df, expr)

        expected = [8, 16, 25]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_multiply_operator(self, backend_name, backend_factory, collect_expr):
        """Test * operator."""
        data = {
            "x": [10, 20, 30],
            "y": [2, 4, 5]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("x") * ma.col("y")

        actual = collect_expr(df, expr)

        expected = [20, 80, 150]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_divide_operator(self, backend_name, backend_factory, collect_expr):
        """Test / operator."""
        data = {
            "x": [10, 20, 30],
            "y": [2, 4, 5]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("x") / ma.col("y")

        actual = collect_expr(df, expr)

        expected = [5.0, 5.0, 6.0]

        for i, (act, exp) in enumerate(zip(actual, expected)):
            assert abs(act - exp) < 0.0001, (
                f"[{backend_name}] At index {i}: expected {exp}, got {act}"
            )


# =============================================================================
# Integration Tests - Complex Arithmetic
# =============================================================================

@pytest.mark.integration
@pytest.mark.arithmetic
@pytest.mark.parametrize("backend_name", [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",

])
class TestComplexArithmetic:
    """Test chaining and complex arithmetic operations."""

    def test_chained_operations(self, backend_name, backend_factory, collect_expr):
        """Test chaining multiple arithmetic operations."""
        data = {
            "a": [10, 20, 30],
            "b": [2, 3, 4],
            "c": [1, 2, 3]
        }
        df = backend_factory.create(data, backend_name)

        # (a + b) * c
        expr = (ma.col("a") + ma.col("b")) * ma.col("c")

        actual = collect_expr(df, expr)

        expected = [12, 46, 102]  # (10+2)*1=12, (20+3)*2=46, (30+4)*3=102
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_mixed_literals_and_columns(self, backend_name, backend_factory, collect_expr):
        """Test mixing literal values with column references."""
        data = {
            "a": [10, 20, 30]
        }
        df = backend_factory.create(data, backend_name)

        # a * 2 + 5
        expr = ma.col("a") * 2 + 5

        actual = collect_expr(df, expr)

        expected = [25, 45, 65]  # 10*2+5=25, 20*2+5=45, 30*2+5=65
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )


# =============================================================================
# Edge Case Tests
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.arithmetic
@pytest.mark.parametrize("backend_name", [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",

])
class TestArithmeticEdgeCases:
    """Test edge cases for arithmetic operations."""

    def test_negative_numbers(self, backend_name, backend_factory, collect_expr):
        """Test arithmetic with negative numbers."""
        data = {
            "a": [-10, -20, 30],
            "b": [2, -3, 4]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a") + ma.col("b")

        actual = collect_expr(df, expr)

        expected = [-8, -23, 34]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_zero_operations(self, backend_name, backend_factory, collect_expr):
        """Test arithmetic with zero."""
        data = {
            "a": [10, 0, 30],
            "zero": [0, 0, 0]
        }
        df = backend_factory.create(data, backend_name)

        # Add zero (should return same values)
        expr = ma.col("a") + ma.col("zero")

        actual = collect_expr(df, expr)

        expected = [10, 0, 30]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )


    def test_large_numbers(self, backend_name, backend_factory, collect_expr):
        """Test arithmetic with large numbers."""
        data = {
            "a": [1000000, 2000000, 3000000],
            "b": [500000, 1000000, 1500000]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a") + ma.col("b")

        actual = collect_expr(df, expr)

        expected = [1500000, 3000000, 4500000]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_floating_point_operations(self, backend_name, backend_factory, collect_expr):
        """Test arithmetic with floating point numbers."""
        data = {
            "a": [1.5, 2.5, 3.5],
            "b": [0.5, 1.5, 2.5]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a") + ma.col("b")

        actual = collect_expr(df, expr)

        expected = [2.0, 4.0, 6.0]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_power_with_zero(self, backend_name, backend_factory, collect_expr):
        """Test power operation with zero exponent."""
        data = {
            "a": [5, 10, 100]
        }
        df = backend_factory.create(data, backend_name)

        # Any number to the power of 0 should be 1
        expr = ma.col("a") ** 0

        actual = collect_expr(df, expr)

        expected = [1, 1, 1]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_power_with_one(self, backend_name, backend_factory, collect_expr):
        """Test power operation with one as exponent."""
        data = {
            "a": [5, 10, 100]
        }
        df = backend_factory.create(data, backend_name)

        # Any number to the power of 1 should be itself
        expr = ma.col("a") ** 1

        actual = collect_expr(df, expr)

        expected = [5, 10, 100]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_floor_division_with_negatives(self, backend_name, backend_factory, collect_expr):
        """Test floor division with negative numbers."""
        data = {
            "a": [-10, 10, -10],
            "b": [3, -3, -3]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a") // ma.col("b")

        actual = collect_expr(df, expr)

        # Floor division rounds toward negative infinity
        expected = [-4, -4, 3]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_modulo_with_negatives(self, backend_name, backend_factory, collect_expr):
        """Test modulo operation with negative numbers.

        KNOWN ISSUE: SQLite and DuckDB use different modulo semantics than Python.
        - Python: result has same sign as divisor (modulus)
        - SQLite/DuckDB: result has same sign of dividend (remainder)

        This test SHOULD fail for ibis-sqlite and ibis-duckdb until we either:
        1. Normalize the behavior in our library (recommended)
        2. Document this as a known limitation and warn users
        3. File an issue with Ibis to provide normalized modulo

        See: https://en.wikipedia.org/wiki/Modulo_operation
        """
        # Mark SQLite and DuckDB as expected failure due to backend inconsistency
        if backend_name in ("ibis-sqlite", "ibis-duckdb"):
            pytest.xfail(
                f"{backend_name.split('-')[1].title()} modulo semantics differ from Python. "
                f"{backend_name.split('-')[1].title()} returns remainder (sign of dividend), "
                "Python returns modulus (sign of divisor). "
                "This needs normalization or documentation."
            )

        data = {
            "a": [-10, 10, -10],
            "b": [3, -3, -3]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a") % ma.col("b")

        actual = collect_expr(df, expr)

        # Python modulo: result has same sign as divisor
        # This is the EXPECTED behavior for consistency
        expected = [2, -2, -1]

        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_multiply_by_zero(self, backend_name, backend_factory, collect_expr):
        """Test multiplication by zero."""
        data = {
            "a": [10, 20, 30, -5]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a") * 0

        actual = collect_expr(df, expr)

        expected = [0, 0, 0, 0]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_multiply_by_one(self, backend_name, backend_factory, collect_expr):
        """Test multiplication by one (identity)."""
        data = {
            "a": [10, 20, 30, -5]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a") * 1


        actual = collect_expr(df, expr)

        expected = [10, 20, 30, -5]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_subtract_from_zero(self, backend_name, backend_factory, collect_expr):
        """Test subtracting from zero (negation)."""
        from ibis.common.exceptions import InputTypeError

        data = {
            "a": [10, -20, 30, 0]
        }
        df = backend_factory.create(data, backend_name)

        expr = 0 - ma.col("a")

        # Known Ibis bug: https://github.com/ibis-project/ibis/issues/11742
        # Reverse operators with literals fail with InputTypeError
        if backend_name.startswith("ibis-"):
            with pytest.raises(InputTypeError, match="Unable to infer datatype.*Deferred"):
                backend_expr = expr.compile(df)
                result = df.select(backend_expr.name("result"))
                _ = result["result"].execute().tolist()
        else:
            actual = collect_expr(df, expr)
            expected = [-10, 20, -30, 0]
            assert actual == expected, (
                f"[{backend_name}] Expected {expected}, got {actual}"
            )

    def test_complex_chained_operations(self, backend_name, backend_factory, collect_expr):
        """Test complex chained arithmetic operations.

        KNOWN ISSUE: SQLite performs integer division instead of float division.
        - Python/Polars/Pandas: 20/3 = 6.666...
        - SQLite: 20/3 = 6 (truncates to integer)

        This test SHOULD fail for ibis-sqlite until we either:
        1. Normalize division to always return float (recommended)
        2. Add explicit int/float division operators
        3. Document this as a known limitation and warn users
        4. File an issue with Ibis about SQLite division behavior

        See: https://www.sqlite.org/lang_expr.html#operators
        """
        # Mark SQLite as expected failure due to integer division behavior
        if backend_name == "ibis-sqlite":
            pytest.xfail(
                "SQLite performs integer division (20/3 = 6) instead of "
                "float division (20/3 = 6.666...). "
                "This creates cross-backend inconsistency. "
                "Needs normalization or documentation."
            )

        data = {
            "a": [10, 20, 30],
            "b": [2, 3, 4],
            "c": [5, 10, 15]
        }
        df = backend_factory.create(data, backend_name)

        # (a + b) * c - a / b
        expr = (ma.col("a") + ma.col("b")) * ma.col("c") - ma.col("a") / ma.col("b")

        actual = collect_expr(df, expr)

        # (10+2)*5 - 10/2 = 60 - 5.0 = 55.0
        # (20+3)*10 - 20/3 = 230 - 6.666... = 223.333...
        # (30+4)*15 - 30/4 = 510 - 7.5 = 502.5
        import math

        # This is the EXPECTED behavior for consistency (float division)
        expected = [55.0, 230.0 - (20.0/3.0), 502.5]

        # Use approximate comparison for floating point
        for i, (a, e) in enumerate(zip(actual, expected)):
            assert math.isclose(a, e, rel_tol=1e-9), \
                f"[{backend_name}] At index {i}: expected {e}, got {a}"

    def test_mixed_integer_float(self, backend_name, backend_factory, collect_expr):
        """Test operations with mixed integer and float types."""
        data = {
            "int_col": [10, 20, 30],
            "float_col": [2.5, 3.5, 4.5]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("int_col") * ma.col("float_col")

        actual = collect_expr(df, expr)

        expected = [25.0, 70.0, 135.0]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )
