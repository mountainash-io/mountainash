"""
Cross-backend tests for boolean operators and comparisons.

Tests boolean operations:
- Comparison operators (==, !=, <, <=, >, >=)
- Logical operators (AND, OR, NOT)
- Collection operators (IN, NOT IN)
- Null checks (IS NULL, IS NOT NULL)
- Complex boolean expressions
- Boolean with other operations

These tests validate that boolean operations work consistently across
all backends: Polars, Pandas, Narwhals, and Ibis (DuckDB, Polars, SQLite).
"""

import pytest
import mountainash_expressions as ma


# =============================================================================
# Cross-Backend Tests - Comparison Operators
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
class TestComparisonOperators:
    """Test comparison operators: ==, !=, <, <=, >, >="""

    def test_equality(self, backend_name, backend_factory, get_result_count):
        """Test == operator."""
        data = {
            "age": [25, 30, 35, 30, 40],
            "name": ["Alice", "Bob", "Charlie", "David", "Eve"]
        }
        df = backend_factory.create(data, backend_name)

        # age == 30
        expr = ma.col("age") == 30
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        assert count == 2, f"[{backend_name}] Expected 2 rows where age == 30, got {count}"

    def test_not_equal(self, backend_name, backend_factory, get_result_count):
        """Test != operator."""
        data = {
            "age": [25, 30, 35, 30, 40]
        }
        df = backend_factory.create(data, backend_name)

        # age != 30
        expr = ma.col("age") != 30
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        assert count == 3, f"[{backend_name}] Expected 3 rows where age != 30, got {count}"

    def test_less_than(self, backend_name, backend_factory, get_result_count):
        """Test < operator."""
        data = {
            "age": [25, 30, 35, 40, 45]
        }
        df = backend_factory.create(data, backend_name)

        # age < 35
        expr = ma.col("age") < 35
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        assert count == 2, f"[{backend_name}] Expected 2 rows where age < 35, got {count}"

    def test_less_than_or_equal(self, backend_name, backend_factory, get_result_count):
        """Test <= operator."""
        data = {
            "age": [25, 30, 35, 40, 45]
        }
        df = backend_factory.create(data, backend_name)

        # age <= 35
        expr = ma.col("age") <= 35
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        assert count == 3, f"[{backend_name}] Expected 3 rows where age <= 35, got {count}"

    def test_greater_than(self, backend_name, backend_factory, get_result_count):
        """Test > operator."""
        data = {
            "age": [25, 30, 35, 40, 45]
        }
        df = backend_factory.create(data, backend_name)

        # age > 35
        expr = ma.col("age") > 35
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        assert count == 2, f"[{backend_name}] Expected 2 rows where age > 35, got {count}"

    def test_greater_than_or_equal(self, backend_name, backend_factory, get_result_count):
        """Test >= operator."""
        data = {
            "age": [25, 30, 35, 40, 45]
        }
        df = backend_factory.create(data, backend_name)

        # age >= 35
        expr = ma.col("age") >= 35
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        assert count == 3, f"[{backend_name}] Expected 3 rows where age >= 35, got {count}"


# =============================================================================
# Cross-Backend Tests - Logical Operators
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
class TestLogicalOperators:
    """Test logical operators: AND, OR, NOT"""

    def test_and_operator(self, backend_name, backend_factory, get_result_count):
        """Test AND (&) operator."""
        data = {
            "age": [25, 30, 35, 40, 45],
            "score": [85, 90, 75, 95, 80]
        }
        df = backend_factory.create(data, backend_name)

        # (age > 30) AND (score >= 80)
        expr = (ma.col("age") > 30) & (ma.col("score") >= 80)
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        # age=35,score=75: False; age=40,score=95: True; age=45,score=80: True
        assert count == 2, f"[{backend_name}] Expected 2 rows, got {count}"

    def test_or_operator(self, backend_name, backend_factory, get_result_count):
        """Test OR (|) operator."""
        data = {
            "age": [25, 30, 35, 40, 45]
        }
        df = backend_factory.create(data, backend_name)

        # (age < 28) OR (age > 38)
        expr = (ma.col("age") < 28) | (ma.col("age") > 38)
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        # age=25: True; age=40: True; age=45: True
        assert count == 3, f"[{backend_name}] Expected 3 rows, got {count}"

    def test_not_operator(self, backend_name, backend_factory, get_result_count):
        """Test NOT (~) operator."""
        data = {
            "active": [True, True, False, True, False]
        }
        df = backend_factory.create(data, backend_name)

        # NOT active
        expr = ~ma.col("active")
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        assert count == 2, f"[{backend_name}] Expected 2 rows where NOT active, got {count}"

    def test_complex_and_or(self, backend_name, backend_factory, get_result_count):
        """Test complex AND/OR combination."""
        data = {
            "age": [25, 30, 35, 40, 45],
            "score": [85, 90, 75, 95, 80],
            "active": [True, True, False, True, False]
        }
        df = backend_factory.create(data, backend_name)

        # (age > 30 AND score >= 80) OR active == False
        expr = ((ma.col("age") > 30) & (ma.col("score") >= 80)) | (ma.col("active") == False)
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        # age=35,score=75,active=False: True (via OR)
        # age=40,score=95,active=True: True (via AND)
        # age=45,score=80,active=False: True (both conditions)
        assert count == 3, f"[{backend_name}] Expected 3 rows, got {count}"


# =============================================================================
# Cross-Backend Tests - Collection Operators
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
class TestCollectionOperators:
    """Test collection operators: IN, NOT IN"""

    def test_in_operator(self, backend_name, backend_factory, get_result_count):
        """Test IN operator."""
        data = {
            "category": ["A", "B", "C", "D", "E"],
            "value": [10, 20, 30, 40, 50]
        }
        df = backend_factory.create(data, backend_name)

        # category IN ['A', 'C', 'E']
        expr = ma.col("category").is_in(["A", "C", "E"])
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        assert count == 3, f"[{backend_name}] Expected 3 rows in ['A', 'C', 'E'], got {count}"

    def test_not_in_operator(self, backend_name, backend_factory, get_result_count):
        """Test NOT IN operator."""
        data = {
            "category": ["A", "B", "C", "D", "E"]
        }
        df = backend_factory.create(data, backend_name)

        # category NOT IN ['B', 'D']
        expr = ~ma.col("category").is_in(["B", "D"])
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        assert count == 3, f"[{backend_name}] Expected 3 rows NOT IN ['B', 'D'], got {count}"

    def test_in_with_numbers(self, backend_name, backend_factory, get_result_count):
        """Test IN operator with numeric values."""
        data = {
            "value": [10, 20, 30, 40, 50]
        }
        df = backend_factory.create(data, backend_name)

        # value IN [20, 40]
        expr = ma.col("value").is_in([20, 40])
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        assert count == 2, f"[{backend_name}] Expected 2 rows in [20, 40], got {count}"


# =============================================================================
# Cross-Backend Tests - Null Checks
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
class TestNullChecks:
    """Test null check operators: IS NULL, IS NOT NULL"""

    def test_is_null(self, backend_name, backend_factory, get_result_count):
        """Test IS NULL check."""
        data = {
            "value": [10, None, 30, None, 50],
            "name": ["Alice", "Bob", "Charlie", "David", "Eve"]
        }
        df = backend_factory.create(data, backend_name)

        # value IS NULL
        expr = ma.col("value").is_null()
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        assert count == 2, f"[{backend_name}] Expected 2 null values, got {count}"

    def test_is_not_null(self, backend_name, backend_factory, get_result_count):
        """Test IS NOT NULL check."""
        data = {
            "value": [10, None, 30, None, 50]
        }
        df = backend_factory.create(data, backend_name)

        # value IS NOT NULL
        expr = ~ma.col("value").is_null()
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        assert count == 3, f"[{backend_name}] Expected 3 non-null values, got {count}"

    def test_null_with_comparison(self, backend_name, backend_factory, get_result_count):
        """Test null check combined with comparison."""
        data = {
            "value": [10, None, 30, None, 50]
        }
        df = backend_factory.create(data, backend_name)

        # (value IS NOT NULL) AND (value > 20)
        expr = (~ma.col("value").is_null()) & (ma.col("value") > 20)
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        # value=30: True; value=50: True
        assert count == 2, f"[{backend_name}] Expected 2 rows, got {count}"


# =============================================================================
# Integration Tests - Boolean with Arithmetic
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
class TestBooleanWithArithmetic:
    """Test boolean operators combined with arithmetic operations."""

    def test_comparison_with_arithmetic(self, backend_name, backend_factory, get_result_count):
        """Test comparison with arithmetic expression."""
        data = {
            "a": [10, 20, 30, 40, 50],
            "b": [5, 10, 15, 20, 25]
        }
        df = backend_factory.create(data, backend_name)

        # (a + b) > 50
        expr = (ma.col("a") + ma.col("b")) > 50
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        # a+b: 15, 30, 45, 60, 75 -> 60, 75 > 50
        assert count == 2, f"[{backend_name}] Expected 2 rows, got {count}"

    def test_complex_arithmetic_boolean(self, backend_name, backend_factory, get_result_count):
        """Test complex arithmetic in boolean expression."""
        data = {
            "x": [10, 20, 30, 40, 50],
            "y": [2, 3, 4, 5, 6]
        }
        df = backend_factory.create(data, backend_name)

        # (x * y) >= 100
        expr = (ma.col("x") * ma.col("y")) >= 100
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        # x*y: 20, 60, 120, 200, 300 -> 120, 200, 300 >= 100
        assert count == 3, f"[{backend_name}] Expected 3 rows, got {count}"


# =============================================================================
# Integration Tests - Boolean with String Operations
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
class TestBooleanWithStringOperations:
    """Test boolean operators combined with string operations."""

    def test_string_comparison_and_numeric(self, backend_name, backend_factory, get_result_count):
        """Test string contains AND numeric comparison."""
        data = {
            "name": ["Alice Smith", "Bob Jones", "Charlie Smith", "David Brown"],
            "age": [25, 30, 35, 40]
        }
        df = backend_factory.create(data, backend_name)

        # (name contains "Smith") AND (age > 28)
        expr = ma.col("name").str_contains("Smith") & (ma.col("age") > 28)
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        # Alice Smith (age 25): False; Charlie Smith (age 35): True
        assert count == 1, f"[{backend_name}] Expected 1 row, got {count}"

    def test_string_starts_with_or_ends_with(self, backend_name, backend_factory, get_result_count):
        """Test string starts_with OR ends_with."""
        data = {
            "filename": ["test.txt", "data.csv", "test.csv", "report.txt", "output.json"]
        }
        df = backend_factory.create(data, backend_name)

        # (filename starts with "test") OR (filename ends with ".json")
        expr = ma.col("filename").str_starts_with("test") | ma.col("filename").str_ends_with(".json")
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        # test.txt, test.csv, output.json
        assert count == 3, f"[{backend_name}] Expected 3 rows, got {count}"


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
class TestBooleanEdgeCases:
    """Test edge cases for boolean operations."""

    def test_all_true_condition(self, backend_name, backend_factory, get_result_count):
        """Test condition that's always true."""
        data = {
            "value": [1, 2, 3, 4, 5]
        }
        df = backend_factory.create(data, backend_name)

        # value > 0 (always true)
        expr = ma.col("value") > 0
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        assert count == 5, f"[{backend_name}] Expected all 5 rows, got {count}"

    def test_all_false_condition(self, backend_name, backend_factory, get_result_count):
        """Test condition that's always false."""
        data = {
            "value": [1, 2, 3, 4, 5]
        }
        df = backend_factory.create(data, backend_name)

        # value > 100 (always false)
        expr = ma.col("value") > 100
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        assert count == 0, f"[{backend_name}] Expected 0 rows, got {count}"

    def test_in_empty_list(self, backend_name, backend_factory, get_result_count):
        """Test IN operator with empty list."""
        data = {
            "value": [1, 2, 3, 4, 5]
        }
        df = backend_factory.create(data, backend_name)

        # value IN [] (should match nothing)
        expr = ma.col("value").is_in([])
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        assert count == 0, f"[{backend_name}] Expected 0 rows for empty IN list, got {count}"

    def test_nested_logical_operations(self, backend_name, backend_factory, get_result_count):
        """Test deeply nested logical operations."""
        data = {
            "a": [1, 2, 3, 4, 5],
            "b": [5, 4, 3, 2, 1],
            "c": [2, 3, 4, 5, 6]
        }
        df = backend_factory.create(data, backend_name)

        # ((a > 2) AND (b < 4)) OR (c == 3)
        expr = ((ma.col("a") > 2) & (ma.col("b") < 4)) | (ma.col("c") == 3)
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        # Row 0: (1>2 & 5<4) | 2==3 = False | False = False
        # Row 1: (2>2 & 4<4) | 3==3 = False | True = True
        # Row 2: (3>2 & 3<4) | 4==3 = True | False = True
        # Row 3: (4>2 & 2<4) | 5==3 = True | False = True
        # Row 4: (5>2 & 1<4) | 6==3 = True | False = True
        assert count == 4, f"[{backend_name}] Expected 4 rows, got {count}"


# =============================================================================
# Complex Real-World Tests
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
class TestComplexBooleanExpressions:
    """Test complex real-world boolean expressions."""

    def test_age_range_and_category(self, backend_name, backend_factory, get_column_values):
        """Test age range filtering with category check."""
        data = {
            "name": ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"],
            "age": [25, 30, 35, 40, 45, 50],
            "category": ["A", "B", "A", "C", "B", "A"],
            "score": [85, 90, 75, 95, 80, 88]
        }
        df = backend_factory.create(data, backend_name)

        # (age >= 30 AND age <= 45) AND (category IN ['A', 'B']) AND (score >= 80)
        expr = (
            (ma.col("age") >= 30) &
            (ma.col("age") <= 45) &
            ma.col("category").is_in(["A", "B"]) &
            (ma.col("score") >= 80)
        )
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        actual = get_column_values(result, "name", backend_name)
        # Bob: age=30, cat=B, score=90: True
        # Charlie: age=35, cat=A, score=75: False (score < 80)
        # Eve: age=45, cat=B, score=80: True
        expected = ["Bob", "Eve"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_complex_eligibility_check(self, backend_name, backend_factory, get_column_values):
        """Test complex eligibility criteria."""
        data = {
            "applicant": ["Alice", "Bob", "Charlie", "David", "Eve"],
            "age": [17, 25, 35, 30, 22],
            "score": [95, 70, 85, 90, 88],
            "premium": [True, False, True, False, True]
        }
        df = backend_factory.create(data, backend_name)

        # Eligible if: (age >= 18 AND score >= 80) OR (premium == True AND score >= 85)
        expr = (
            ((ma.col("age") >= 18) & (ma.col("score") >= 80)) |
            ((ma.col("premium") == True) & (ma.col("score") >= 85))
        )
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        actual = get_column_values(result, "applicant", backend_name)
        # Alice: (17>=18 & 95>=80) | (True & 95>=85) = False | True = True
        # Bob: (25>=18 & 70>=80) | (False & 70>=85) = False | False = False
        # Charlie: (35>=18 & 85>=80) | (True & 85>=85) = True | True = True
        # David: (30>=18 & 90>=80) | (False & 90>=85) = True | False = True
        # Eve: (22>=18 & 88>=80) | (True & 88>=85) = True | True = True
        expected = ["Alice", "Charlie", "David", "Eve"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )
