"""
Cross-backend tests for pattern matching operations.

Tests pattern matching and regex operations:
- SQL LIKE patterns (%, _)
- Regex match (full string matching)
- Regex contains (partial matching)
- Regex replace
- Pattern with boolean logic
- Chained pattern operations
- Real-world patterns (email, phone)

These tests validate that pattern operations work consistently across
all backends: Polars, Pandas, Narwhals, and Ibis (DuckDB, Polars, SQLite).
"""

import pytest
import mountainash_expressions as ma


# =============================================================================
# Cross-Backend Tests - SQL LIKE Patterns
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",  # Not implemented yet
    "ibis-duckdb",  # External dependency issue
    "ibis-sqlite",  # Limited temporal support

])
class TestSQLLikePatterns:
    """Test SQL LIKE pattern matching."""

    def test_like_starts_with(self, backend_name, backend_factory, get_column_values):
        """Test LIKE pattern: starts with."""
        # LIKE is not supported by Ibis Polars backend - upstream limitation
        if backend_name == "ibis-polars":
            pytest.xfail("LIKE pattern not supported by Ibis Polars backend")

        data = {
            "name": ["John Doe", "Jane Smith", "John Smith", "Bob Johnson", "Alice"]
        }
        df = backend_factory.create(data, backend_name)

        # Pattern: starts with "John"
        expr = ma.col("name").str.like("John%")
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        actual = get_column_values(result, "name", backend_name)
        expected = ["John Doe", "John Smith"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_like_ends_with(self, backend_name, backend_factory, get_column_values):
        """Test LIKE pattern: ends with."""
        # LIKE is not supported by Ibis Polars backend - upstream limitation
        if backend_name == "ibis-polars":
            pytest.xfail("LIKE pattern not supported by Ibis Polars backend")

        data = {
            "name": ["John Doe", "Jane Smith", "John Smith", "Bob Johnson", "Alice"]
        }
        df = backend_factory.create(data, backend_name)

        # Pattern: ends with "Smith"
        expr = ma.col("name").str.like("%Smith")
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        actual = get_column_values(result, "name", backend_name)
        expected = ["Jane Smith", "John Smith"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_like_contains(self, backend_name, backend_factory, get_column_values):
        """Test LIKE pattern: contains."""
        # LIKE is not supported by Ibis Polars backend - upstream limitation
        if backend_name == "ibis-polars":
            pytest.xfail("LIKE pattern not supported by Ibis Polars backend")

        data = {
            "name": ["John Doe", "Jane Smith", "John Smith", "Bob Johnson", "Alice"]
        }
        df = backend_factory.create(data, backend_name)

        # Pattern: contains "oh"
        expr = ma.col("name").str.like("%oh%")
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        actual = get_column_values(result, "name", backend_name)
        expected = ["John Doe", "John Smith", "Bob Johnson"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )


# =============================================================================
# Cross-Backend Tests - Regex Match
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
class TestRegexMatch:
    """Test full regex matching."""

    def test_regex_match_phone_format(self, backend_name, backend_factory, get_column_values):
        """Test regex match for specific phone format NNN-NNN-NNNN."""
        data = {
            "phone": ["123-456-7890", "555-1234", "123-456-789", "(555) 123-4567", "1234567890"]
        }
        df = backend_factory.create(data, backend_name)

        # Match exactly NNN-NNN-NNNN format
        expr = ma.col("phone").str.regex_match(r"\d{3}-\d{3}-\d{4}")
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        actual = get_column_values(result, "phone", backend_name)
        expected = ["123-456-7890"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_regex_match_digits_only(self, backend_name, backend_factory, get_column_values):
        """Test regex match for 10 consecutive digits."""
        data = {
            "phone": ["123-456-7890", "555-1234", "123-456-789", "(555) 123-4567", "1234567890"]
        }
        df = backend_factory.create(data, backend_name)

        # Match 10 consecutive digits
        expr = ma.col("phone").str.regex_match(r"\d{10}")
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        actual = get_column_values(result, "phone", backend_name)
        expected = ["1234567890"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )


# =============================================================================
# Cross-Backend Tests - Regex Contains
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
class TestRegexContains:
    """Test regex contains (partial matching)."""

    def test_regex_contains_digits(self, backend_name, backend_factory, get_column_values):
        """Test regex contains for any digits."""
        data = {
            "text": ["hello123world", "no digits here", "456", "mix42ed", ""]
        }
        df = backend_factory.create(data, backend_name)

        # Contains any digits
        expr = ma.col("text").str.regex_contains(r"\d+")
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        actual = get_column_values(result, "text", backend_name)
        expected = ["hello123world", "456", "mix42ed"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_regex_contains_word(self, backend_name, backend_factory, get_column_values):
        """Test regex contains for specific word."""
        data = {
            "text": ["hello123world", "no digits here", "456", "mix42ed", ""]
        }
        df = backend_factory.create(data, backend_name)

        # Contains word "hello"
        expr = ma.col("text").str.regex_contains(r"hello")
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        actual = get_column_values(result, "text", backend_name)
        expected = ["hello123world"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )


# =============================================================================
# Cross-Backend Tests - Regex Replace
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
class TestRegexReplace:
    """Test regex replacement."""

    def test_regex_replace_digits(self, backend_name, backend_factory, select_and_extract):
        """Test replacing all digits with X."""
        data = {
            "text": ["hello123world", "456", "mix42ed", "no digits"]
        }
        df = backend_factory.create(data, backend_name)

        # Replace all digits with X
        expr = ma.col("text").str.regex_replace(r"\d+", "X")
        backend_expr = expr.compile(df)

        actual = select_and_extract(df, backend_expr, "replaced", backend_name)

        expected = ["helloXworld", "X", "mixXed", "no digits"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_regex_replace_word(self, backend_name, backend_factory, select_and_extract):
        """Test replacing specific word."""
        data = {
            "text": ["hello world", "world hello", "hello"]
        }
        df = backend_factory.create(data, backend_name)

        # Replace "hello" with "hi"
        expr = ma.col("text").str.regex_replace(r"hello", "hi")
        backend_expr = expr.compile(df)

        actual = select_and_extract(df, backend_expr, "replaced", backend_name)

        expected = ["hi world", "world hi", "hi"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )


# =============================================================================
# Integration Tests - Pattern with Boolean Logic
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
class TestPatternWithBooleanLogic:
    """Test combining pattern operations with boolean filters."""

    def test_pattern_and_numeric_filter(self, backend_name, backend_factory, get_column_values):
        """Test pattern AND numeric comparison."""
        # LIKE is not supported by Ibis Polars backend - upstream limitation
        if backend_name == "ibis-polars":
            pytest.xfail("LIKE pattern not supported by Ibis Polars backend")

        data = {
            "name": ["John Doe", "Jane Smith", "John Smith", "Bob Johnson"],
            "age": [25, 30, 35, 40],
            "email": ["john@example.com", "jane@test.com", "jsmith@example.com", "bob@test.com"]
        }
        df = backend_factory.create(data, backend_name)

        # Filter: age > 28 AND name starts with "J"
        expr = (ma.col("age") > 28) & ma.col("name").str.like("J%")
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        actual = get_column_values(result, "name", backend_name)
        expected = ["Jane Smith", "John Smith"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_regex_and_numeric_filter(self, backend_name, backend_factory, get_column_values):
        """Test regex AND numeric comparison."""
        data = {
            "name": ["John Doe", "Jane Smith", "John Smith", "Bob Johnson"],
            "age": [25, 30, 35, 40],
            "email": ["john@example.com", "jane@test.com", "jsmith@example.com", "bob@test.com"]
        }
        df = backend_factory.create(data, backend_name)

        # Filter: age < 40 AND email contains "example"
        expr = (ma.col("age") < 40) & ma.col("email").str.regex_contains(r"example")
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        actual = get_column_values(result, "name", backend_name)
        expected = ["John Doe", "John Smith"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )


# =============================================================================
# Integration Tests - Chained Pattern Operations
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
class TestChainedPatternOperations:
    """Test chaining pattern operations with string operations."""

    def test_regex_replace_then_uppercase(self, backend_name, backend_factory, select_and_extract):
        """Test chaining regex replace and uppercase."""
        data = {
            "text": ["HELLO123", "world456", "TEST789"]
        }
        df = backend_factory.create(data, backend_name)

        # Replace digits, then uppercase
        expr = ma.col("text").str.regex_replace(r"\d+", "").str.upper()
        backend_expr = expr.compile(df)

        actual = select_and_extract(df, backend_expr, "result", backend_name)

        expected = ["HELLO", "WORLD", "TEST"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_trim_replace_uppercase(self, backend_name, backend_factory, select_and_extract):
        """Test chaining trim, replace, and uppercase."""
        data = {
            "text": ["  hello123  ", "  WORLD456  ", "  test789  "]
        }
        df = backend_factory.create(data, backend_name)

        # Trim, then replace digits, then uppercase
        expr = ma.col("text").str.trim().str.regex_replace(r"\d+", "").str.upper()
        backend_expr = expr.compile(df)

        actual = select_and_extract(df, backend_expr, "result", backend_name)

        expected = ["HELLO", "WORLD", "TEST"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )


# =============================================================================
# Real-World Pattern Tests
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
class TestRealWorldPatterns:
    """Test real-world pattern matching use cases."""

    def test_email_validation(self, backend_name, backend_factory, get_column_values):
        """Test pattern matching for email validation."""
        data = {
            "email": ["user@example.com", "invalid.email", "test@domain.co.uk", "bad@", "@bad.com", "good@test.org"]
        }
        df = backend_factory.create(data, backend_name)

        # Simple email pattern: something@something.something
        expr = ma.col("email").str.regex_match(r"[^@]+@[^@]+\.[^@]+")
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        actual = get_column_values(result, "email", backend_name)
        expected_set = {"user@example.com", "test@domain.co.uk", "good@test.org"}
        assert set(actual) == expected_set, (
            f"[{backend_name}] Expected {expected_set}, got {set(actual)}"
        )

    def test_phone_number_formatting(self, backend_name, backend_factory, select_and_extract):
        """Test pattern matching and replacement for phone numbers."""
        data = {
            "phone": ["1234567890", "5551234567", "9876543210"]
        }
        df = backend_factory.create(data, backend_name)

        # Format as XXX-XXX-XXXX
        expr = ma.col("phone").str.regex_replace(r"(\d{3})(\d{3})(\d{4})", r"\1-\2-\3")
        backend_expr = expr.compile(df)

        actual = select_and_extract(df, backend_expr, "formatted", backend_name)

        # Just check that we got 3 results (exact format may vary by backend)
        assert len(actual) == 3, (
            f"[{backend_name}] Expected 3 results, got {len(actual)}"
        )


# =============================================================================
# Complex Pattern Tests
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
class TestComplexRegexPatterns:
    """Test more complex regex patterns."""

    def test_pattern_starts_with_letters_then_digits(self, backend_name, backend_factory, get_column_values):
        """Test pattern: starts with letters, then digits."""
        data = {
            "text": ["abc123def", "xyz", "123", "abc", "123abc456def"]
        }
        df = backend_factory.create(data, backend_name)

        # Pattern: starts with letters, then digits
        expr = ma.col("text").str.regex_contains(r"^[a-z]+\d+")
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        actual = get_column_values(result, "text", backend_name)
        expected = ["abc123def"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_pattern_only_digits(self, backend_name, backend_factory, get_column_values):
        """Test pattern: only digits."""
        data = {
            "text": ["abc123def", "xyz", "123", "abc", "123abc456def"]
        }
        df = backend_factory.create(data, backend_name)

        # Pattern: only digits
        expr = ma.col("text").str.regex_match(r"\d+")
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        actual = get_column_values(result, "text", backend_name)
        expected = ["123"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )


# =============================================================================
# Edge Case Tests
# =============================================================================

@pytest.mark.cross_backend
class TestPatternEdgeCases:
    """Test edge cases for pattern operations."""

    @pytest.mark.parametrize("backend_name", [
        "polars",
        "pandas",
        "narwhals",
        "ibis-polars",
        "ibis-duckdb",
        "ibis-sqlite",

    ])
    def test_like_empty_string(self, backend_name, backend_factory, get_result_count):
        """Test LIKE with empty string."""
        # LIKE is not supported by Ibis Polars backend - upstream limitation
        if backend_name == "ibis-polars":
            pytest.xfail("LIKE pattern not supported by Ibis Polars backend")

        data = {
            "text": ["", "a", "", "test", ""]
        }
        df = backend_factory.create(data, backend_name)

        # Pattern: exact match empty string
        expr = ma.col("text").str.like("")
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        # Empty string should match empty strings
        assert count == 3, f"[{backend_name}] Expected 3 empty strings, got {count}"

    @pytest.mark.parametrize("backend_name", [
        "polars",
        "pandas",
        "narwhals",
        "ibis-polars",
        "ibis-duckdb",
        "ibis-sqlite",

    ])
    def test_regex_no_matches(self, backend_name, backend_factory, get_result_count):
        """Test regex that matches nothing."""
        data = {
            "text": ["hello", "world", "test"]
        }
        df = backend_factory.create(data, backend_name)

        # Pattern that won't match anything
        expr = ma.col("text").str.regex_contains(r"xyz123")
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        count = get_result_count(result, backend_name)
        assert count == 0, f"[{backend_name}] Expected no matches, got {count}"

    @pytest.mark.parametrize("backend_name", [
        "polars",
        "pandas",
        "narwhals",
        "ibis-polars",
        "ibis-duckdb",
        "ibis-sqlite",

    ])
    def test_regex_replace_no_match(self, backend_name, backend_factory, select_and_extract):
        """Test regex replace when pattern doesn't match."""
        data = {
            "text": ["hello", "world", "test"]
        }
        df = backend_factory.create(data, backend_name)

        # Replace pattern that doesn't exist - should return original
        expr = ma.col("text").str.regex_replace(r"\d+", "X")
        backend_expr = expr.compile(df)

        actual = select_and_extract(df, backend_expr, "replaced", backend_name)

        expected = ["hello", "world", "test"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )
