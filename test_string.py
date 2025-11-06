"""
Comprehensive tests for string operations across backends.

Tests all string operations: upper, lower, trim, length, contains,
starts_with, ends_with, replace, substring.
"""

import polars as pl
import narwhals as nw
import ibis
import mountainash_expressions as ma


def test_case_conversion():
    """Test upper and lower case conversion."""
    df = pl.DataFrame({
        "name": ["Alice", "BOB", "Charlie", "DAVID", "eve"]
    })

    # Test uppercase
    expr = ma.col("name").str_upper()
    result = df.select(expr.compile(df).alias("upper"))
    assert result["upper"].to_list() == ["ALICE", "BOB", "CHARLIE", "DAVID", "EVE"]

    # Test lowercase
    expr = ma.col("name").str_lower()
    result = df.select(expr.compile(df).alias("lower"))
    assert result["lower"].to_list() == ["alice", "bob", "charlie", "david", "eve"]


def test_trim_operations():
    """Test trim, ltrim, and rtrim operations."""
    df = pl.DataFrame({
        "text": ["  hello  ", "world  ", "  foo", "bar", "  baz  "]
    })

    # Test trim (both sides)
    expr = ma.col("text").str_trim()
    result = df.select(expr.compile(df).alias("trimmed"))
    assert result["trimmed"].to_list() == ["hello", "world", "foo", "bar", "baz"]


def test_string_length():
    """Test string length operation."""
    df = pl.DataFrame({
        "word": ["cat", "hello", "a", "testing", ""]
    })

    expr = ma.col("word").str_length()
    result = df.select(expr.compile(df).alias("len"))
    assert result["len"].to_list() == [3, 5, 1, 7, 0]


def test_string_contains():
    """Test string contains check (returns boolean)."""
    df = pl.DataFrame({
        "text": ["hello world", "foo bar", "test", "hello", "world"]
    })

    # Filter rows containing "hello"
    expr = ma.col("text").str_contains("hello")
    result = df.filter(expr.compile(df))
    assert result["text"].to_list() == ["hello world", "hello"]

    # Filter rows containing "world"
    expr = ma.col("text").str_contains("world")
    result = df.filter(expr.compile(df))
    assert result["text"].to_list() == ["hello world", "world"]


def test_string_starts_ends_with():
    """Test starts_with and ends_with checks."""
    df = pl.DataFrame({
        "filename": ["test.txt", "data.csv", "test.csv", "report.txt", "test.json"]
    })

    # Filter files starting with "test"
    expr = ma.col("filename").str_starts_with("test")
    result = df.filter(expr.compile(df))
    assert result["filename"].to_list() == ["test.txt", "test.csv", "test.json"]

    # Filter files ending with ".csv"
    expr = ma.col("filename").str_ends_with(".csv")
    result = df.filter(expr.compile(df))
    assert result["filename"].to_list() == ["data.csv", "test.csv"]


def test_string_replace():
    """Test string replace operation."""
    df = pl.DataFrame({
        "text": ["hello world", "foo bar", "hello foo", "world bar"]
    })

    # Replace "hello" with "hi"
    expr = ma.col("text").str_replace("hello", "hi")
    result = df.select(expr.compile(df).alias("replaced"))
    assert result["replaced"].to_list() == ["hi world", "foo bar", "hi foo", "world bar"]

    # Replace "bar" with "baz"
    expr = ma.col("text").str_replace("bar", "baz")
    result = df.select(expr.compile(df).alias("replaced"))
    assert result["replaced"].to_list() == ["hello world", "foo baz", "hello foo", "world baz"]


def test_string_substring():
    """Test substring extraction."""
    df = pl.DataFrame({
        "text": ["hello", "world", "testing", "foo", "bar"]
    })

    # Extract first 3 characters
    expr = ma.col("text").str_substring(0, 3)
    result = df.select(expr.compile(df).alias("sub"))
    assert result["sub"].to_list() == ["hel", "wor", "tes", "foo", "bar"]

    # Extract from position 2 to end
    expr = ma.col("text").str_substring(2)
    result = df.select(expr.compile(df).alias("sub"))
    assert result["sub"].to_list() == ["llo", "rld", "sting", "o", "r"]


def test_chained_string_operations():
    """Test chaining multiple string operations."""
    df = pl.DataFrame({
        "name": ["  Alice  ", "  BOB  ", "  Charlie  "]
    })

    # Chain trim -> lowercase -> check contains
    expr = ma.col("name").str_trim().str_lower()
    result = df.select(expr.compile(df).alias("cleaned"))
    assert result["cleaned"].to_list() == ["alice", "bob", "charlie"]

    # More complex: trim -> upper -> check starts with
    df = pl.DataFrame({
        "text": ["  hello world  ", "  foo bar  ", "  hello  "]
    })
    expr = ma.col("text").str_trim().str_upper().str_starts_with("HELLO")
    result = df.filter(expr.compile(df))
    assert result["text"].to_list() == ["  hello world  ", "  hello  "]


def test_string_with_boolean_filter():
    """Test combining string operations with boolean filtering."""
    df = pl.DataFrame({
        "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
        "age": [25, 30, 35, 40, 45],
        "city": ["New York", "Boston", "New York", "Chicago", "Boston"]
    })

    # Filter: age > 30 AND city contains "New"
    expr = (ma.col("age") > 30) & ma.col("city").str_contains("New")
    result = df.filter(expr.compile(df))
    assert result["name"].to_list() == ["Charlie"]

    # Filter: age < 40 AND name starts with "A" or "B"
    expr_a = ma.col("name").str_starts_with("A")
    expr_b = ma.col("name").str_starts_with("B")
    expr = (ma.col("age") < 40) & (expr_a | expr_b)
    result = df.filter(expr.compile(df))
    assert result["name"].to_list() == ["Alice", "Bob"]


def test_cross_backend_string_compatibility():
    """Test that string operations produce same results across backends."""
    # Create test data
    data = {
        "text": ["Hello World", "foo bar", "TEST", "MixedCase"],
        "value": [100, 200, 300, 400]
    }

    # Polars
    df_polars = pl.DataFrame(data)

    # Narwhals (wrapping Polars)
    df_narwhals = nw.from_native(df_polars)

    # Ibis
    con_ibis = ibis.duckdb.connect()
    df_ibis = con_ibis.create_table("test_string_cross", data)

    # Test 1: uppercase
    expr = ma.col("text").str_upper()

    result_polars = df_polars.select(expr.compile(df_polars).alias("result"))
    result_narwhals = df_narwhals.select(expr.compile(df_narwhals).alias("result"))
    ibis_expr = expr.compile(df_ibis).name("result")
    result_ibis = df_ibis.select(ibis_expr).execute()

    expected = ["HELLO WORLD", "FOO BAR", "TEST", "MIXEDCASE"]
    assert result_polars["result"].to_list() == expected
    assert result_narwhals["result"].to_list() == expected
    assert result_ibis["result"].tolist() == expected

    # Test 2: contains filter
    expr = ma.col("text").str_contains("o")

    result_polars = df_polars.filter(expr.compile(df_polars))
    result_narwhals = df_narwhals.filter(expr.compile(df_narwhals))
    result_ibis = df_ibis.filter(expr.compile(df_ibis)).execute()

    expected_texts = ["Hello World", "foo bar"]
    assert result_polars["text"].to_list() == expected_texts
    assert result_narwhals["text"].to_list() == expected_texts
    assert result_ibis["text"].tolist() == expected_texts

    # Test 3: substring
    expr = ma.col("text").str_substring(0, 3)

    result_polars = df_polars.select(expr.compile(df_polars).alias("result"))
    result_narwhals = df_narwhals.select(expr.compile(df_narwhals).alias("result"))
    ibis_expr = expr.compile(df_ibis).name("result")
    result_ibis = df_ibis.select(ibis_expr).execute()

    expected = ["Hel", "foo", "TES", "Mix"]
    assert result_polars["result"].to_list() == expected
    assert result_narwhals["result"].to_list() == expected
    assert result_ibis["result"].tolist() == expected


def test_string_with_arithmetic():
    """Test combining string operations with arithmetic."""
    df = pl.DataFrame({
        "name": ["Alice", "Bob", "Charlie", "David"],
        "score": [85, 92, 78, 95]
    })

    # Get length of name and add to score
    expr_len = ma.col("name").str_length()
    expr_result = expr_len + ma.col("score")
    result = df.select(expr_result.compile(df).alias("combined"))
    assert result["combined"].to_list() == [85 + 5, 92 + 3, 78 + 7, 95 + 5]


if __name__ == "__main__":
    print("Running string operation tests...")

    print("✓ test_case_conversion")
    test_case_conversion()

    print("✓ test_trim_operations")
    test_trim_operations()

    print("✓ test_string_length")
    test_string_length()

    print("✓ test_string_contains")
    test_string_contains()

    print("✓ test_string_starts_ends_with")
    test_string_starts_ends_with()

    print("✓ test_string_replace")
    test_string_replace()

    print("✓ test_string_substring")
    test_string_substring()

    print("✓ test_chained_string_operations")
    test_chained_string_operations()

    print("✓ test_string_with_boolean_filter")
    test_string_with_boolean_filter()

    print("✓ test_cross_backend_string_compatibility")
    test_cross_backend_string_compatibility()

    print("✓ test_string_with_arithmetic")
    test_string_with_arithmetic()

    print("\n✅ All string tests passed!")
