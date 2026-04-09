"""
Cross-backend tests for string operations.

Tests all string operations: upper, lower, trim, length, contains,
starts_with, ends_with, replace, substring.

These tests validate that string operations work consistently across
all backends: Polars, Pandas, Narwhals, and Ibis (DuckDB, Polars, SQLite).
"""

import pytest
import mountainash.expressions as ma
import mountainash as ma_top


# =============================================================================
# Cross-Backend Tests - Case Conversion
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.string
@pytest.mark.parametrize("backend_name", [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",  # Not implemented yet
    "ibis-duckdb",  # External dependency issue
    "ibis-sqlite",  # Limited temporal support

])
class TestCaseConversion:
    """Test upper and lower case conversion."""

    def test_str_upper(self, backend_name, backend_factory, collect_expr):
        """Test converting strings to uppercase."""
        data = {
            "name": ["Alice", "BOB", "Charlie", "DAVID", "eve"]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("name").str.upper()
        actual = collect_expr(df, expr)

        expected = ["ALICE", "BOB", "CHARLIE", "DAVID", "EVE"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_str_lower(self, backend_name, backend_factory, collect_expr):
        """Test converting strings to lowercase."""
        data = {
            "name": ["Alice", "BOB", "Charlie", "DAVID", "eve"]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("name").str.lower()
        actual = collect_expr(df, expr)

        expected = ["alice", "bob", "charlie", "david", "eve"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )


# =============================================================================
# Cross-Backend Tests - Trim Operations
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.string
@pytest.mark.parametrize("backend_name", [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",  # Not implemented yet
    "ibis-duckdb",  # External dependency issue
    "ibis-sqlite",  # Limited temporal support

])
class TestTrimOperations:
    """Test trim, ltrim, and rtrim operations."""

    def test_str_trim(self, backend_name, backend_factory, collect_expr):
        """Test trimming whitespace from both sides."""
        data = {
            "text": ["  hello  ", "world  ", "  foo", "bar", "  baz  "]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("text").str.trim()
        actual = collect_expr(df, expr)

        expected = ["hello", "world", "foo", "bar", "baz"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )


# =============================================================================
# Cross-Backend Tests - String Length
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.string
@pytest.mark.parametrize("backend_name", [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",  # Not implemented yet
    "ibis-duckdb",  # External dependency issue
    "ibis-sqlite",  # Limited temporal support

])
class TestStringLength:
    """Test string length operation."""

    def test_str_length(self, backend_name, backend_factory, collect_expr):
        """Test getting string length."""
        data = {
            "word": ["cat", "hello", "a", "testing", ""]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("word").str.length()
        actual = collect_expr(df, expr)

        expected = [3, 5, 1, 7, 0]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )


# =============================================================================
# Cross-Backend Tests - String Contains
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.string
@pytest.mark.parametrize("backend_name", [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",  # Not implemented yet
    "ibis-duckdb",  # External dependency issue
    "ibis-sqlite",  # Limited temporal support

])
class TestStringContains:
    """Test string contains check (returns boolean)."""

    def test_str_contains_hello(self, backend_name, backend_factory):
        """Test filtering rows containing 'hello'."""
        data = {
            "text": ["hello world", "foo bar", "test", "hello", "world"]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("text").str.contains("hello")
        actual = ma_top.relation(df).filter(expr).to_dict()["text"]
        expected = ["hello world", "hello"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_str_contains_world(self, backend_name, backend_factory):
        """Test filtering rows containing 'world'."""
        data = {
            "text": ["hello world", "foo bar", "test", "hello", "world"]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("text").str.contains("world")
        actual = ma_top.relation(df).filter(expr).to_dict()["text"]
        expected = ["hello world", "world"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )


# =============================================================================
# Cross-Backend Tests - Starts With / Ends With
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.string
@pytest.mark.parametrize("backend_name", [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",  # Not implemented yet
    "ibis-duckdb",  # External dependency issue
    "ibis-sqlite",  # Limited temporal support

])
class TestStringStartsEndsWith:
    """Test starts_with and ends_with checks."""

    def test_str_starts_with(self, backend_name, backend_factory):
        """Test filtering files starting with 'test'."""
        data = {
            "filename": ["test.txt", "data.csv", "test.csv", "report.txt", "test.json"]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("filename").str.starts_with("test")
        actual = ma_top.relation(df).filter(expr).to_dict()["filename"]
        expected = ["test.txt", "test.csv", "test.json"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_str_ends_with(self, backend_name, backend_factory):
        """Test filtering files ending with '.csv'."""
        data = {
            "filename": ["test.txt", "data.csv", "test.csv", "report.txt", "test.json"]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("filename").str.ends_with(".csv")
        actual = ma_top.relation(df).filter(expr).to_dict()["filename"]
        expected = ["data.csv", "test.csv"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )


# =============================================================================
# Cross-Backend Tests - String Replace
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.string
@pytest.mark.parametrize("backend_name", [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",  # Not implemented yet
    "ibis-duckdb",  # External dependency issue
    "ibis-sqlite",  # Limited temporal support

])
class TestStringReplace:
    """Test string replace operation."""

    def test_str_replace_hello(self, backend_name, backend_factory, collect_expr):
        """Test replacing 'hello' with 'hi'."""
        data = {
            "text": ["hello world", "foo bar", "hello foo", "world bar"]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("text").str.replace("hello", "hi")
        actual = collect_expr(df, expr)

        expected = ["hi world", "foo bar", "hi foo", "world bar"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_str_replace_bar(self, backend_name, backend_factory, collect_expr):
        """Test replacing 'bar' with 'baz'."""
        data = {
            "text": ["hello world", "foo bar", "hello foo", "world bar"]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("text").str.replace("bar", "baz")
        actual = collect_expr(df, expr)

        expected = ["hello world", "foo baz", "hello foo", "world baz"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )


# =============================================================================
# Cross-Backend Tests - String Substring
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.string
@pytest.mark.parametrize("backend_name", [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",  # Not implemented yet
    "ibis-duckdb",  # External dependency issue
    "ibis-sqlite",  # Limited temporal support

])
class TestStringSubstring:
    """Test substring extraction."""

    def test_str_substring_first_3(self, backend_name, backend_factory, collect_expr):
        """Test extracting first 3 characters."""
        data = {
            "text": ["hello", "world", "testing", "foo", "bar"]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("text").str.substring(0, 3)
        actual = collect_expr(df, expr)

        expected = ["hel", "wor", "tes", "foo", "bar"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_str_substring_from_pos_2(self, backend_name, backend_factory, collect_expr):
        """Test extracting from position 2 to end."""
        data = {
            "text": ["hello", "world", "testing", "foo", "bar"]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("text").str.substring(2)
        actual = collect_expr(df, expr)

        expected = ["llo", "rld", "sting", "o", "r"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )


# =============================================================================
# Integration Tests - Chaining String Operations
# =============================================================================

@pytest.mark.integration
@pytest.mark.string
@pytest.mark.parametrize("backend_name", [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",  # Not implemented yet
    "ibis-duckdb",  # External dependency issue
    "ibis-sqlite",  # Limited temporal support

])
class TestChainingStringOperations:
    """Test chaining multiple string operations."""

    def test_chain_trim_and_lowercase(self, backend_name, backend_factory, collect_expr):
        """Test chaining trim -> lowercase."""
        data = {
            "name": ["  Alice  ", "  BOB  ", "  Charlie  "]
        }
        df = backend_factory.create(data, backend_name)

        # Chain: trim -> lowercase
        expr = ma.col("name").str.trim().str.lower()
        actual = collect_expr(df, expr)

        expected = ["alice", "bob", "charlie"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_chain_trim_upper_starts_with(self, backend_name, backend_factory):
        """Test chaining trim -> upper -> starts_with filter."""
        data = {
            "text": ["  hello world  ", "  foo bar  ", "  hello  ", "  goodbye  "]
        }
        df = backend_factory.create(data, backend_name)

        # Chain: trim -> upper -> check starts with "HELLO"
        expr = ma.col("text").str.trim().str.upper().str.starts_with("HELLO")
        actual = ma_top.relation(df).filter(expr).to_dict()["text"]
        expected = ["  hello world  ", "  hello  "]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )


# =============================================================================
# Integration Tests - String with Boolean Filters
# =============================================================================

@pytest.mark.integration
@pytest.mark.string
@pytest.mark.parametrize("backend_name", [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",  # Not implemented yet
    "ibis-duckdb",  # External dependency issue
    "ibis-sqlite",  # Limited temporal support

])
class TestStringWithBooleanFilter:
    """Test combining string operations with boolean filtering."""

    def test_age_and_city_contains(self, backend_name, backend_factory):
        """Test filtering: age > 30 AND city contains 'New'."""
        data = {
            "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
            "age": [25, 30, 35, 40, 45],
            "city": ["New York", "Boston", "New York", "Chicago", "Boston"]
        }
        df = backend_factory.create(data, backend_name)

        # Filter: age > 30 AND city contains "New"
        # Charlie: age 35 > 30, city "New York" contains "New" ✓
        # David: age 40 > 30, city "Chicago" does NOT contain "New" ✗
        expr = (ma.col("age") > 30) & ma.col("city").str.contains("New")
        actual = ma_top.relation(df).filter(expr).to_dict()["name"]
        expected = ["Charlie"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_age_and_name_starts_with(self, backend_name, backend_factory):
        """Test filtering: age < 40 AND name starts with 'A' or 'B'."""
        data = {
            "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
            "age": [25, 30, 35, 40, 45]
        }
        df = backend_factory.create(data, backend_name)

        # Filter: age < 40 AND (name starts with "A" or "B")
        expr_a = ma.col("name").str.starts_with("A")
        expr_b = ma.col("name").str.starts_with("B")
        expr = (ma.col("age") < 40) & (expr_a | expr_b)
        actual = ma_top.relation(df).filter(expr).to_dict()["name"]
        expected = ["Alice", "Bob"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )


# =============================================================================
# Integration Tests - String with Arithmetic
# =============================================================================

@pytest.mark.integration
@pytest.mark.string
@pytest.mark.parametrize("backend_name", [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",  # Not implemented yet
    "ibis-duckdb",  # External dependency issue
    "ibis-sqlite",  # Limited temporal support

])
class TestStringWithArithmetic:
    """Test combining string operations with arithmetic."""

    def test_string_length_plus_score(self, backend_name, backend_factory, collect_expr):
        """Test getting length of name and adding to score."""
        data = {
            "name": ["Alice", "Bob", "Charlie", "David"],
            "score": [85, 92, 78, 95]
        }
        df = backend_factory.create(data, backend_name)

        # Get length of name and add to score
        expr_len = ma.col("name").str.length()
        expr_result = expr_len + ma.col("score")
        actual = collect_expr(df, expr_result)

        expected = [85 + 5, 92 + 3, 78 + 7, 95 + 5]  # [90, 95, 85, 100]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )


# =============================================================================
# Edge Case Tests
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.string
@pytest.mark.parametrize("backend_name", [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",  # Not implemented yet
    "ibis-duckdb",  # External dependency issue
    "ibis-sqlite",  # Limited temporal support

])
class TestStringEdgeCases:
    """Test edge cases for string operations."""

    def test_empty_string_operations(self, backend_name, backend_factory, collect_expr):
        """Test operations on empty strings."""
        data = {
            "text": ["", "a", "", "test", ""]
        }
        df = backend_factory.create(data, backend_name)

        # Length of empty strings
        expr = ma.col("text").str.length()
        actual = collect_expr(df, expr)

        expected = [0, 1, 0, 4, 0]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_case_conversion_on_mixed(self, backend_name, backend_factory, collect_expr):
        """Test case conversion on mixed case strings."""
        data = {
            "text": ["HeLLo", "WoRLD", "TeSt123", "MiXeD"]
        }
        df = backend_factory.create(data, backend_name)

        # Uppercase
        expr = ma.col("text").str.upper()
        actual = collect_expr(df, expr)

        expected = ["HELLO", "WORLD", "TEST123", "MIXED"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_trim_no_whitespace(self, backend_name, backend_factory, collect_expr):
        """Test trimming strings with no whitespace."""
        data = {
            "text": ["hello", "world", "test"]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("text").str.trim()
        actual = collect_expr(df, expr)

        # Should return unchanged
        expected = ["hello", "world", "test"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_substring_full_length(self, backend_name, backend_factory, collect_expr):
        """Test substring that extracts entire string."""
        data = {
            "text": ["hello", "world", "test"]
        }
        df = backend_factory.create(data, backend_name)

        # Extract from position 0 with no length limit (entire string)
        expr = ma.col("text").str.substring(0)
        actual = collect_expr(df, expr)

        expected = ["hello", "world", "test"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_replace_no_match(self, backend_name, backend_factory, collect_expr):
        """Test replace when pattern doesn't exist."""
        data = {
            "text": ["hello", "world", "test"]
        }
        df = backend_factory.create(data, backend_name)

        # Try to replace "xyz" which doesn't exist
        expr = ma.col("text").str.replace("xyz", "abc")
        actual = collect_expr(df, expr)

        # Should return unchanged
        expected = ["hello", "world", "test"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_contains_empty_string(self, backend_name, backend_factory):
        """Test contains with empty substring."""
        data = {
            "text": ["hello", "world", "test"]
        }
        df = backend_factory.create(data, backend_name)

        # Empty string is contained in all strings
        expr = ma.col("text").str.contains("")
        actual = ma_top.relation(df).filter(expr).to_dict()["text"]
        # All strings contain empty string
        expected = ["hello", "world", "test"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_starts_with_empty_string(self, backend_name, backend_factory):
        """Test starts_with empty string."""
        data = {
            "text": ["hello", "world", "test"]
        }
        df = backend_factory.create(data, backend_name)

        # All strings start with empty string
        expr = ma.col("text").str.starts_with("")
        actual = ma_top.relation(df).filter(expr).to_dict()["text"]
        expected = ["hello", "world", "test"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_ends_with_empty_string(self, backend_name, backend_factory):
        """Test ends_with empty string."""
        data = {
            "text": ["hello", "world", "test"]
        }
        df = backend_factory.create(data, backend_name)

        # All strings end with empty string
        expr = ma.col("text").str.ends_with("")
        actual = ma_top.relation(df).filter(expr).to_dict()["text"]
        expected = ["hello", "world", "test"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_replace_multiple_occurrences(self, backend_name, backend_factory, collect_expr):
        """Test replacing multiple occurrences in same string."""
        data = {
            "text": ["hello hello", "test test test", "world"]
        }
        df = backend_factory.create(data, backend_name)

        # Replace all occurrences of a word
        expr = ma.col("text").str.replace("test", "exam")
        actual = collect_expr(df, expr)

        # str.replace should replace ALL occurrences (consistent with Python str.replace)
        expected = ["hello hello", "exam exam exam", "world"]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_case_sensitivity_contains(self, backend_name, backend_factory):
        """Test case sensitivity in contains operation."""
        data = {
            "text": ["Hello World", "HELLO WORLD", "hello world", "goodbye"]
        }
        df = backend_factory.create(data, backend_name)

        # Search for lowercase "hello"
        expr = ma.col("text").str.contains("hello")
        actual = ma_top.relation(df).filter(expr).to_dict()["text"]
        # Should only match lowercase "hello"
        expected = ["hello world"]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_substring_beyond_length(self, backend_name, backend_factory, collect_expr):
        """Test substring starting beyond string length."""
        data = {
            "text": ["hi", "hello", "x"]
        }
        df = backend_factory.create(data, backend_name)

        # Start at position 10 (beyond all strings)
        expr = ma.col("text").str.substring(10, 5)
        actual = collect_expr(df, expr)

        # Should return empty strings
        expected = ["", "", ""]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_length_with_special_characters(self, backend_name, backend_factory, collect_expr):
        """Test length with special characters and numbers."""
        data = {
            "text": ["hello!", "123", "test@example.com", "a-b-c"]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("text").str.length()
        actual = collect_expr(df, expr)

        expected = [6, 3, 16, 5]  # "hello!" = 6, "123" = 3, "test@example.com" = 16, "a-b-c" = 5
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )
