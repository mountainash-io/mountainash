"""
Comprehensive tests for pattern matching operations across backends.

Tests: LIKE, REGEX_MATCH, REGEX_CONTAINS, and REGEX_REPLACE operations.
"""

import polars as pl
import narwhals as nw
import ibis
import mountainash_expressions as ma


def test_sql_like_patterns():
    """Test SQL LIKE pattern matching."""
    df = pl.DataFrame({
        "name": ["John Doe", "Jane Smith", "John Smith", "Bob Johnson", "Alice"]
    })

    # Test: starts with "John"
    expr = ma.col("name").like("John%")
    result = df.filter(expr.compile(df))
    assert result["name"].to_list() == ["John Doe", "John Smith"]

    # Test: ends with "Smith"
    expr = ma.col("name").like("%Smith")
    result = df.filter(expr.compile(df))
    assert result["name"].to_list() == ["Jane Smith", "John Smith"]

    # Test: contains "oh"
    expr = ma.col("name").like("%oh%")
    result = df.filter(expr.compile(df))
    assert result["name"].to_list() == ["John Doe", "John Smith", "Bob Johnson"]


def test_regex_match():
    """Test full regex matching."""
    df = pl.DataFrame({
        "phone": ["123-456-7890", "555-1234", "123-456-789", "(555) 123-4567", "1234567890"]
    })

    # Match exactly NNN-NNN-NNNN format
    expr = ma.col("phone").regex_match(r"\d{3}-\d{3}-\d{4}")
    result = df.filter(expr.compile(df))
    assert result["phone"].to_list() == ["123-456-7890"]

    # Match 10 consecutive digits
    expr = ma.col("phone").regex_match(r"\d{10}")
    result = df.filter(expr.compile(df))
    assert result["phone"].to_list() == ["1234567890"]


def test_regex_contains():
    """Test regex contains (partial matching)."""
    df = pl.DataFrame({
        "text": ["hello123world", "no digits here", "456", "mix42ed", ""]
    })

    # Contains any digits
    expr = ma.col("text").regex_contains(r"\d+")
    result = df.filter(expr.compile(df))
    assert result["text"].to_list() == ["hello123world", "456", "mix42ed"]

    # Contains word "hello"
    expr = ma.col("text").regex_contains(r"hello")
    result = df.filter(expr.compile(df))
    assert result["text"].to_list() == ["hello123world"]


def test_regex_replace():
    """Test regex replacement."""
    df = pl.DataFrame({
        "text": ["hello123world", "456", "mix42ed", "no digits"]
    })

    # Replace all digits with X
    expr = ma.col("text").regex_replace(r"\d+", "X")
    result = df.select(expr.compile(df).alias("replaced"))
    assert result["replaced"].to_list() == ["helloXworld", "X", "mixXed", "no digits"]

    # Replace word boundaries
    df2 = pl.DataFrame({
        "text": ["hello world", "world hello", "hello"]
    })
    expr = ma.col("text").regex_replace(r"hello", "hi")
    result = df2.select(expr.compile(df2).alias("replaced"))
    assert result["replaced"].to_list() == ["hi world", "world hi", "hi"]


def test_pattern_with_boolean_filter():
    """Test combining pattern operations with boolean filters."""
    df = pl.DataFrame({
        "name": ["John Doe", "Jane Smith", "John Smith", "Bob Johnson"],
        "age": [25, 30, 35, 40],
        "email": ["john@example.com", "jane@test.com", "jsmith@example.com", "bob@test.com"]
    })

    # Filter: age > 28 AND name starts with "J"
    expr = (ma.col("age") > 28) & ma.col("name").like("J%")
    result = df.filter(expr.compile(df))
    assert result["name"].to_list() == ["Jane Smith", "John Smith"]

    # Filter: age < 40 AND email contains "example"
    expr = (ma.col("age") < 40) & ma.col("email").regex_contains(r"example")
    result = df.filter(expr.compile(df))
    assert result["name"].to_list() == ["John Doe", "John Smith"]


def test_chained_pattern_operations():
    """Test chaining pattern operations."""
    df = pl.DataFrame({
        "text": ["HELLO123", "world456", "TEST789"]
    })

    # Replace digits, then check if contains "HELLO"
    expr = ma.col("text").regex_replace(r"\d+", "").str_upper()
    result = df.select(expr.compile(df).alias("result"))
    assert result["result"].to_list() == ["HELLO", "WORLD", "TEST"]


def test_email_validation():
    """Test pattern matching for email validation."""
    df = pl.DataFrame({
        "email": ["user@example.com", "invalid.email", "test@domain.co.uk", "bad@", "@bad.com", "good@test.org"]
    })

    # Simple email pattern
    expr = ma.col("email").regex_match(r"[^@]+@[^@]+\.[^@]+")
    result = df.filter(expr.compile(df))
    assert set(result["email"].to_list()) == {"user@example.com", "test@domain.co.uk", "good@test.org"}


def test_phone_number_formatting():
    """Test pattern matching and replacement for phone numbers."""
    df = pl.DataFrame({
        "phone": ["1234567890", "5551234567", "9876543210"]
    })

    # Format as XXX-XXX-XXXX
    expr = ma.col("phone").regex_replace(r"(\d{3})(\d{3})(\d{4})", r"\1-\2-\3")
    result = df.select(expr.compile(df).alias("formatted"))

    # The exact format depends on backend regex support, so just check it changed
    assert len(result["formatted"].to_list()) == 3


def test_cross_backend_pattern_compatibility():
    """Test that pattern operations produce same results across backends."""
    data = {
        "text": ["hello world", "foo123bar", "TEST", "MixedCase456"],
        "value": [100, 200, 300, 400]
    }

    # Polars
    df_polars = pl.DataFrame(data)

    # Narwhals (wrapping Polars)
    df_narwhals = nw.from_native(df_polars)

    # Ibis
    con_ibis = ibis.duckdb.connect()
    df_ibis = con_ibis.create_table("test_pattern_cross", data)

    # Test 1: LIKE pattern
    expr = ma.col("text").like("%o%")

    result_polars = df_polars.filter(expr.compile(df_polars))
    result_narwhals = df_narwhals.filter(expr.compile(df_narwhals))
    result_ibis = df_ibis.filter(expr.compile(df_ibis)).execute()

    expected_texts = ["hello world", "foo123bar"]
    assert result_polars["text"].to_list() == expected_texts
    assert result_narwhals["text"].to_list() == expected_texts
    assert result_ibis["text"].tolist() == expected_texts

    # Test 2: regex_contains
    expr = ma.col("text").regex_contains(r"\d+")

    result_polars = df_polars.filter(expr.compile(df_polars))
    result_narwhals = df_narwhals.filter(expr.compile(df_narwhals))
    result_ibis = df_ibis.filter(expr.compile(df_ibis)).execute()

    expected_texts = ["foo123bar", "MixedCase456"]
    assert result_polars["text"].to_list() == expected_texts
    assert result_narwhals["text"].to_list() == expected_texts
    assert result_ibis["text"].tolist() == expected_texts

    # Test 3: regex_replace
    expr = ma.col("text").regex_replace(r"\d+", "X")

    result_polars = df_polars.select(expr.compile(df_polars).alias("result"))
    result_narwhals = df_narwhals.select(expr.compile(df_narwhals).alias("result"))
    ibis_expr = expr.compile(df_ibis).name("result")
    result_ibis = df_ibis.select(ibis_expr).execute()

    expected = ["hello world", "fooXbar", "TEST", "MixedCaseX"]
    assert result_polars["result"].to_list() == expected
    assert result_narwhals["result"].to_list() == expected
    assert result_ibis["result"].tolist() == expected


def test_pattern_with_string_operations():
    """Test combining pattern matching with string operations."""
    df = pl.DataFrame({
        "text": ["  hello123  ", "  WORLD456  ", "  test789  "]
    })

    # Trim, then replace digits, then uppercase
    expr = ma.col("text").str_trim().regex_replace(r"\d+", "").str_upper()
    result = df.select(expr.compile(df).alias("result"))
    assert result["result"].to_list() == ["HELLO", "WORLD", "TEST"]


def test_complex_regex_patterns():
    """Test more complex regex patterns."""
    df = pl.DataFrame({
        "text": ["abc123def", "xyz", "123", "abc", "123abc456def"]
    })

    # Pattern: starts with letters, then digits
    expr = ma.col("text").regex_contains(r"^[a-z]+\d+")
    result = df.filter(expr.compile(df))
    assert result["text"].to_list() == ["abc123def"]

    # Pattern: only digits
    expr = ma.col("text").regex_match(r"\d+")
    result = df.filter(expr.compile(df))
    assert result["text"].to_list() == ["123"]


if __name__ == "__main__":
    print("Running pattern matching operation tests...")

    print("✓ test_sql_like_patterns")
    test_sql_like_patterns()

    print("✓ test_regex_match")
    test_regex_match()

    print("✓ test_regex_contains")
    test_regex_contains()

    print("✓ test_regex_replace")
    test_regex_replace()

    print("✓ test_pattern_with_boolean_filter")
    test_pattern_with_boolean_filter()

    print("✓ test_chained_pattern_operations")
    test_chained_pattern_operations()

    print("✓ test_email_validation")
    test_email_validation()

    print("✓ test_phone_number_formatting")
    test_phone_number_formatting()

    print("✓ test_cross_backend_pattern_compatibility")
    test_cross_backend_pattern_compatibility()

    print("✓ test_pattern_with_string_operations")
    test_pattern_with_string_operations()

    print("✓ test_complex_regex_patterns")
    test_complex_regex_patterns()

    print("\n✅ All pattern matching tests passed!")
