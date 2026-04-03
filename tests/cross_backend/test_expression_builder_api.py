"""
Cross-backend tests for ExpressionBuilder public API.

Tests the public API interface:
- All dunder methods (magic methods)
- Comparison operators (==, !=, <, <=, >, >=)
- Logical operators (&, |, ~)
- Arithmetic operators (+, -, *, /, %, **, //)
- Reverse arithmetic operators (__radd__, __rsub__, etc.)
- String operations
- Pattern operations
- Conditional operations
- Temporal operations
- Compile method
- Properties and helpers

These tests validate that the ExpressionBuilder API works consistently
across all backends: Polars, Pandas, Narwhals, and Ibis (DuckDB, Polars, SQLite).
"""

import pytest
import mountainash.expressions as ma
from ibis.common.exceptions import InputTypeError


# =============================================================================
# Cross-Backend Tests - Dunder Methods (Comparison)
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
class TestDunderComparisonOperators:
    """Test magic methods for comparison operators."""

    def test_dunder_eq_with_value(self, backend_name, backend_factory, get_result_count):
        """Test __eq__ (==) with literal value."""
        data = {"age": [25, 30, 35, 30, 40]}
        df = backend_factory.create(data, backend_name)

        # Using == operator (calls __eq__)
        expr = ma.col("age") == 30
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)


        count = get_result_count(result, backend_name)
        assert count == 2, f"[{backend_name}] Expected 2 rows where age == 30"

    def test_dunder_eq_with_expression(self, backend_name, backend_factory, get_result_count):
        """Test __eq__ (==) with another expression."""
        data = {"a": [10, 20, 30], "b": [10, 15, 30]}
        df = backend_factory.create(data, backend_name)

        # Using == with two column expressions
        expr = ma.col("a") == ma.col("b")
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        assert count == 2, f"[{backend_name}] Expected 2 rows where a == b"

    def test_dunder_ne(self, backend_name, backend_factory, get_result_count):
        """Test __ne__ (!=) operator."""
        data = {"age": [25, 30, 35, 30, 40]}
        df = backend_factory.create(data, backend_name)

        # Using != operator (calls __ne__)
        expr = ma.col("age") != 30
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        assert count == 3, f"[{backend_name}] Expected 3 rows where age != 30"

    def test_dunder_gt(self, backend_name, backend_factory, get_result_count):
        """Test __gt__ (>) operator."""
        data = {"age": [25, 30, 35, 40, 45]}
        df = backend_factory.create(data, backend_name)

        # Using > operator (calls __gt__)
        expr = ma.col("age") > 35
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        assert count == 2, f"[{backend_name}] Expected 2 rows where age > 35"

    def test_dunder_lt(self, backend_name, backend_factory, get_result_count):
        """Test __lt__ (<) operator."""
        data = {"age": [25, 30, 35, 40, 45]}
        df = backend_factory.create(data, backend_name)

        # Using < operator (calls __lt__)
        expr = ma.col("age") < 35
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        assert count == 2, f"[{backend_name}] Expected 2 rows where age < 35"

    def test_dunder_ge(self, backend_name, backend_factory, get_result_count):
        """Test __ge__ (>=) operator."""
        data = {"age": [25, 30, 35, 40, 45]}
        df = backend_factory.create(data, backend_name)

        # Using >= operator (calls __ge__)
        expr = ma.col("age") >= 35
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        assert count == 3, f"[{backend_name}] Expected 3 rows where age >= 35"

    def test_dunder_le(self, backend_name, backend_factory, get_result_count):
        """Test __le__ (<=) operator."""
        data = {"age": [25, 30, 35, 40, 45]}
        df = backend_factory.create(data, backend_name)

        # Using <= operator (calls __le__)
        expr = ma.col("age") <= 35
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        assert count == 3, f"[{backend_name}] Expected 3 rows where age <= 35"


# =============================================================================
# Cross-Backend Tests - Dunder Methods (Logical)
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
class TestDunderLogicalOperators:
    """Test magic methods for logical operators."""

    def test_dunder_and(self, backend_name, backend_factory, get_result_count):
        """Test __and__ (&) operator."""
        data = {"age": [25, 30, 35, 40, 45], "active": [True, True, False, True, False]}
        df = backend_factory.create(data, backend_name)

        # Using & operator (calls __and__)
        expr = (ma.col("age") > 28) & ma.col("active")
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        assert count == 2, f"[{backend_name}] Expected 2 rows where age > 28 AND active"

    def test_dunder_or(self, backend_name, backend_factory, get_result_count):
        """Test __or__ (|) operator."""
        data = {"age": [25, 30, 35, 40, 45]}
        df = backend_factory.create(data, backend_name)

        # Using | operator (calls __or__)
        expr = (ma.col("age") < 28) | (ma.col("age") > 42)
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        assert count == 2, f"[{backend_name}] Expected 2 rows where age < 28 OR age > 42"

    def test_dunder_invert(self, backend_name, backend_factory, get_result_count):
        """Test __invert__ (~) operator."""
        data = {"age": [25, 30, 35, 40, 45]}
        df = backend_factory.create(data, backend_name)

        # Using ~ operator (calls __invert__)
        expr = ~(ma.col("age") > 35)
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        assert count == 3, f"[{backend_name}] Expected 3 rows where NOT (age > 35)"

    def test_complex_logical_expression(self, backend_name, backend_factory, get_result_count):
        """Test complex combination of logical operators."""
        data = {"age": [25, 30, 35, 40, 45], "score": [70, 85, 90, 95, 65]}
        df = backend_factory.create(data, backend_name)

        # Complex: (age >= 30 AND score >= 85) OR age >= 40
        expr = ((ma.col("age") >= 30) & (ma.col("score") >= 85)) | (ma.col("age") >= 40)
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        assert count == 4, f"[{backend_name}] Expected 4 rows"


# =============================================================================
# Cross-Backend Tests - Dunder Methods (Arithmetic)
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
class TestDunderArithmeticOperators:
    """Test magic methods for arithmetic operators."""

    def test_dunder_add(self, backend_name, backend_factory, collect_expr):
        """Test __add__ (+) operator."""
        data = {"a": [10, 20, 30], "b": [5, 10, 15]}
        df = backend_factory.create(data, backend_name)

        # Using + operator (calls __add__)
        expr = ma.col("a") + ma.col("b")
        actual = collect_expr(df, expr)

        expected = [15, 30, 45]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_dunder_sub(self, backend_name, backend_factory, collect_expr):
        """Test __sub__ (-) operator."""
        data = {"a": [10, 20, 30], "b": [5, 10, 15]}
        df = backend_factory.create(data, backend_name)

        # Using - operator (calls __sub__)
        expr = ma.col("a") - ma.col("b")
        actual = collect_expr(df, expr)

        expected = [5, 10, 15]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_dunder_mul(self, backend_name, backend_factory, collect_expr):
        """Test __mul__ (*) operator."""
        data = {"a": [10, 20, 30], "b": [2, 3, 4]}
        df = backend_factory.create(data, backend_name)

        # Using * operator (calls __mul__)
        expr = ma.col("a") * ma.col("b")
        actual = collect_expr(df, expr)

        expected = [20, 60, 120]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_dunder_truediv(self, backend_name, backend_factory, collect_expr):
        """Test __truediv__ (/) operator."""
        data = {"a": [10, 20, 30], "b": [2, 4, 5]}
        df = backend_factory.create(data, backend_name)

        # Using / operator (calls __truediv__)
        expr = ma.col("a") / ma.col("b")
        actual = collect_expr(df, expr)

        expected = [5.0, 5.0, 6.0]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_dunder_mod(self, backend_name, backend_factory, collect_expr):
        """Test __mod__ (%) operator."""
        data = {"a": [10, 21, 35], "b": [3, 5, 7]}
        df = backend_factory.create(data, backend_name)

        # Using % operator (calls __mod__)
        expr = ma.col("a") % ma.col("b")
        actual = collect_expr(df, expr)

        expected = [1, 1, 0]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_dunder_pow(self, backend_name, backend_factory, collect_expr):
        """Test __pow__ (**) operator."""
        data = {"a": [2, 3, 4], "b": [2, 2, 2]}
        df = backend_factory.create(data, backend_name)

        # Using ** operator (calls __pow__)
        expr = ma.col("a") ** ma.col("b")
        actual = collect_expr(df, expr)

        expected = [4, 9, 16]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_dunder_floordiv(self, backend_name, backend_factory, collect_expr):
        """Test __floordiv__ (//) operator."""
        data = {"a": [10, 21, 35], "b": [3, 5, 7]}
        df = backend_factory.create(data, backend_name)

        # Using // operator (calls __floordiv__)
        expr = ma.col("a") // ma.col("b")
        actual = collect_expr(df, expr)

        expected = [3, 4, 5]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"


# =============================================================================
# Cross-Backend Tests - Reverse Arithmetic Operators
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
class TestReverseArithmeticOperators:
    """Test reverse arithmetic operators (when left operand is not ExpressionBuilder)."""

    def test_radd(self, backend_name, backend_factory, collect_expr):
        """Test __radd__ (other + self)."""
        data = {"a": [10, 20, 30]}
        df = backend_factory.create(data, backend_name)

        # 5 + col("a") - calls __radd__
        expr = 5 + ma.col("a")

        # Known Ibis bug: https://github.com/ibis-project/ibis/issues/11742
        # Reverse operators with literals fail with InputTypeError
        if backend_name.startswith("ibis-"):
            pytest.xfail("Ibis issue: https://github.com/ibis-project/ibis/issues/11742. Raises InputTypeError.  Unable to infer datatype.*Deferred")

        actual = collect_expr(df, expr)
        expected = [15, 25, 35]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_rsub(self, backend_name, backend_factory, collect_expr):
        """Test __rsub__ (other - self)."""
        data = {"a": [10, 20, 30]}
        df = backend_factory.create(data, backend_name)

        # 100 - col("a") - calls __rsub__
        expr = 100 - ma.col("a")

        # Known Ibis bug: https://github.com/ibis-project/ibis/issues/11742
        # Reverse operators with literals fail with InputTypeError
        if backend_name.startswith("ibis-"):
            pytest.xfail("Ibis issue: https://github.com/ibis-project/ibis/issues/11742. Raises InputTypeError.  Unable to infer datatype.*Deferred")

        actual = collect_expr(df, expr)

        expected = [90, 80, 70]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_rmul(self, backend_name, backend_factory, collect_expr):
        """Test __rmul__ (other * self)."""
        data = {"a": [10, 20, 30]}
        df = backend_factory.create(data, backend_name)

        # 5 * col("a") - calls __rmul__
        expr = 5 * ma.col("a")

        # Known Ibis bug: https://github.com/ibis-project/ibis/issues/11742
        # Reverse operators with literals fail with InputTypeError
        if backend_name.startswith("ibis-"):
            pytest.xfail("Ibis issue: https://github.com/ibis-project/ibis/issues/11742. Raises InputTypeError.  Unable to infer datatype.*Deferred")

        actual = collect_expr(df, expr)
        expected = [50, 100, 150]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_rtruediv(self, backend_name, backend_factory, collect_expr):
        """Test __rtruediv__ (other / self)."""
        data = {"a": [2, 4, 5]}
        df = backend_factory.create(data, backend_name)

        # 100 / col("a") - calls __rtruediv__
        expr = 100 / ma.col("a")

        # Known Ibis bug: https://github.com/ibis-project/ibis/issues/11742
        # Reverse operators with literals fail with InputTypeError
        if backend_name.startswith("ibis-"):
            pytest.xfail("Ibis issue: https://github.com/ibis-project/ibis/issues/11742. Raises InputTypeError.  Unable to infer datatype.*Deferred")

        actual = collect_expr(df, expr)
        expected = [50.0, 25.0, 20.0]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_rmod(self, backend_name, backend_factory, collect_expr):
        """Test __rmod__ (other % self)."""
        data = {"a": [3, 5, 7]}
        df = backend_factory.create(data, backend_name)

        # 100 % col("a") - calls __rmod__
        expr = 100 % ma.col("a")

        # Known Ibis bug: https://github.com/ibis-project/ibis/issues/11742
        # Reverse operators with literals fail with InputTypeError
        if backend_name.startswith("ibis-"):
            pytest.xfail("Ibis issue: https://github.com/ibis-project/ibis/issues/11742. Raises InputTypeError.  Unable to infer datatype.*Deferred")


        actual = collect_expr(df, expr)
        expected = [1, 0, 2]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_rpow(self, backend_name, backend_factory, collect_expr):
        """Test __rpow__ (other ** self)."""
        data = {"a": [2, 3, 4]}
        df = backend_factory.create(data, backend_name)

        # 2 ** col("a") - calls __rpow__
        expr = 2 ** ma.col("a")

        # Known Ibis bug: https://github.com/ibis-project/ibis/issues/11742
        # Reverse operators with literals fail with InputTypeError
        if backend_name.startswith("ibis-"):
            pytest.xfail("Ibis issue: https://github.com/ibis-project/ibis/issues/11742. Raises InputTypeError.  Unable to infer datatype.*Deferred")

        actual = collect_expr(df, expr)
        expected = [4, 8, 16]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_rfloordiv(self, backend_name, backend_factory, collect_expr):
        """Test __rfloordiv__ (other // self)."""
        data = {"a": [3, 5, 7]}
        df = backend_factory.create(data, backend_name)

        # 100 // col("a") - calls __rfloordiv__
        expr = 100 // ma.col("a")

        # Known Ibis bug: https://github.com/ibis-project/ibis/issues/11742
        # Reverse operators with literals fail with InputTypeError
        if backend_name.startswith("ibis-"):
            pytest.xfail("Ibis issue: https://github.com/ibis-project/ibis/issues/11742. Raises InputTypeError.  Unable to infer datatype.*Deferred")

        actual = collect_expr(df, expr)

        expected = [33, 20, 14]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"


# =============================================================================
# Cross-Backend Tests - Method-based Comparison API
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
class TestMethodBasedComparison:
    """Test method-based comparison API (eq, ne, gt, lt, ge, le)."""

    def test_eq_method(self, backend_name, backend_factory, get_result_count):
        """Test eq() method."""
        data = {"age": [25, 30, 35, 30, 40]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("age").eq(30)
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        assert count == 2, f"[{backend_name}] Expected 2 rows where age.eq(30)"

    def test_ne_method(self, backend_name, backend_factory, get_result_count):
        """Test ne() method."""
        data = {"age": [25, 30, 35, 30, 40]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("age").ne(30)
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        assert count == 3, f"[{backend_name}] Expected 3 rows where age.ne(30)"

    def test_gt_method(self, backend_name, backend_factory, get_result_count):
        """Test gt() method."""
        data = {"age": [25, 30, 35, 40, 45]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("age").gt(35)
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        assert count == 2, f"[{backend_name}] Expected 2 rows where age.gt(35)"

    def test_lt_method(self, backend_name, backend_factory, get_result_count):
        """Test lt() method."""
        data = {"age": [25, 30, 35, 40, 45]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("age").lt(35)
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        assert count == 2, f"[{backend_name}] Expected 2 rows where age.lt(35)"

    def test_ge_method(self, backend_name, backend_factory, get_result_count):
        """Test ge() method."""
        data = {"age": [25, 30, 35, 40, 45]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("age").ge(35)
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        assert count == 3, f"[{backend_name}] Expected 3 rows where age.ge(35)"

    def test_le_method(self, backend_name, backend_factory, get_result_count):
        """Test le() method."""
        data = {"age": [25, 30, 35, 40, 45]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("age").le(35)
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        assert count == 3, f"[{backend_name}] Expected 3 rows where age.le(35)"


# =============================================================================
# Cross-Backend Tests - Properties and Helpers
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
class TestPropertiesAndHelpers:
    """Test properties and helper methods of ExpressionBuilder."""

    def test_node_property(self, backend_name, backend_factory, collect_expr):
        """Test node property returns underlying expression node."""
        data = {"age": [25, 30, 35]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("age")

        # node property should return the underlying node
        assert expr.node is not None, f"[{backend_name}] node property should not be None"


    def test_repr_method(self, backend_name, backend_factory, collect_expr):
        """Test __repr__ method returns string representation."""
        data = {"age": [25, 30, 35]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("age")

        # __repr__ should return a string
        repr_str = repr(expr)
        assert isinstance(repr_str, str), f"[{backend_name}] repr() should return string"
        assert "BooleanExpressionAPI" in repr_str, \
            f"[{backend_name}] repr() should contain 'BooleanExpressionAPI'"


# =============================================================================
# Cross-Backend Tests - Operator Chaining and Precedence
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
class TestOperatorChainingAndPrecedence:
    """Test complex operator chaining and precedence."""

    def test_arithmetic_chaining(self, backend_name, backend_factory, collect_expr):
        """Test chaining multiple arithmetic operators."""
        data = {"a": [10, 20, 30]}
        df = backend_factory.create(data, backend_name)

        # (a + 5) * 2 - 10
        expr = ((ma.col("a") + 5) * 2) - 10
        actual = collect_expr(df, expr)

        expected = [20, 40, 60]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_comparison_with_arithmetic(self, backend_name, backend_factory, get_result_count):
        """Test comparison operators with arithmetic expressions."""
        data = {"a": [10, 20, 30], "b": [5, 15, 25]}
        df = backend_factory.create(data, backend_name)

        # (a + b) > 30
        expr = (ma.col("a") + ma.col("b")) > 30
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        assert count == 2, f"[{backend_name}] Expected 2 rows where (a + b) > 30"

    def test_logical_with_comparison_and_arithmetic(self, backend_name, backend_factory, get_result_count, get_result):
        """Test logical operators with comparison and arithmetic."""
        data = {"a": [10, 20, 30],
                "b": [5, 10, 15],
                "c": [True, False, True]}
        df = backend_factory.create(data, backend_name)

        # ((a + b) > 25) AND c
        expr = ((ma.col("a") + ma.col("b")) > 25) & ma.col("c")
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        assert count == 1, f"[{backend_name}] Expected 1 rows"

    def test_complex_expression_with_all_operators(self, backend_name, backend_factory, get_result_count, get_result):
        """Test complex expression combining all operator types."""
        data = {
            "price":    [100, 200, 300],
            "discount": [10, 20, 30],
            "quantity": [1, 2, 3],
            "in_stock": [True, True, False]
        }
        df = backend_factory.create(data, backend_name)

        # ((price - discount) * quantity > 200) AND in_stock
        expr = (((ma.col("price") - ma.col("discount")) * ma.col("quantity")) > 200) & ma.col("in_stock")
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        assert count == 1, f"[{backend_name}] Expected 2 rows"


# =============================================================================
# Integration Tests - Real-world API Usage Patterns
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
class TestRealWorldAPIPatterns:
    """Test real-world usage patterns of the API."""

    def test_filtering_with_multiple_conditions(self, backend_name, backend_factory, get_result_count):
        """Test real-world filtering with multiple conditions."""
        data = {
            "age": [25, 30, 35, 40, 45],
            "salary": [50000, 60000, 70000, 80000, 90000],
            "active": [True, True, False, True, True]
        }
        df = backend_factory.create(data, backend_name)

        # Filter: age >= 30 AND salary > 60000 AND active
        expr = (ma.col("age") >= 30) & (ma.col("salary") > 60000) & ma.col("active")
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        assert count == 2, f"[{backend_name}] Expected 2 rows"

    def test_calculated_column_with_operators(self, backend_name, backend_factory, collect_expr):
        """Test creating calculated column using operators."""
        data = {
            "price": [100, 200, 300],
            "tax_rate": [0.1, 0.15, 0.2]
        }
        df = backend_factory.create(data, backend_name)

        # Calculate total: price * (1 + tax_rate)
        # Note: (1 + tax_rate) triggers reverse operator
        # Alias applied BEFORE compile (on ExpressionBuilder)
        expr = (ma.col("price") * (1 + ma.col("tax_rate"))).name.alias("total")

        backend_expr = expr.compile(df)
        result = df.select(backend_expr)

        # Handle lazy evaluation for different backends
        if backend_name == "narwhals-ibis":
            result = result.collect()
            actual = result["total"].to_list()
        elif backend_name.startswith("ibis-"):
            # Ibis returns a Table - need to execute to get result
            actual = result["total"].execute().tolist()
        else:
            actual = result["total"].to_list()

        expected = [110.0, 230.0, 360.0]

        # Use approximate comparison for floating point
        import math
        for i, (a, e) in enumerate(zip(actual, expected)):
            assert math.isclose(a, e, rel_tol=1e-9), \
                f"[{backend_name}] At index {i}: expected {e}, got {a}"

    def test_range_check_pattern(self, backend_name, backend_factory, get_result_count):
        """Test range checking pattern (between values)."""
        data = {"score": [45, 65, 75, 85, 95]}
        df = backend_factory.create(data, backend_name)

        # Check if score is between 60 and 90 (inclusive)
        expr = (ma.col("score") >= 60) & (ma.col("score") <= 90)
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        assert count == 3, f"[{backend_name}] Expected 3 rows where 60 <= score <= 90"

    def test_null_safe_calculation(self, backend_name, backend_factory, collect_expr):
        """Test null-safe calculation pattern."""
        data = {
            "value": [10, None, 30, None, 50]
        }
        df = backend_factory.create(data, backend_name)

        # Calculate with null replacement: value.fill_null(0) * 2
        expr = ma.col("value").fill_null(0) * 2
        actual = collect_expr(df, expr)

        expected = [20, 0, 60, 0, 100]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"
