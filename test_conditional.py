"""
Comprehensive tests for conditional operations across backends.

Tests: WHEN-THEN-OTHERWISE, COALESCE, and FILL_NULL operations.
"""

import polars as pl
import narwhals as nw
import ibis
import mountainash_expressions as ma


def test_when_then_otherwise():
    """Test when-then-otherwise conditional expressions."""
    df = pl.DataFrame({
        "age": [15, 25, 35, 45, 55, 65, 75],
        "name": ["Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace"]
    })

    # Test: age category
    expr = ma.when(ma.col("age") >= 65).then("senior").otherwise("non-senior")
    result = df.select(expr.compile(df).alias("category"))
    expected = ["non-senior", "non-senior", "non-senior", "non-senior", "non-senior", "senior", "senior"]
    assert result["category"].to_list() == expected

    # Test: numeric values
    expr = ma.when(ma.col("age") > 50).then(1).otherwise(0)
    result = df.select(expr.compile(df).alias("flag"))
    assert result["flag"].to_list() == [0, 0, 0, 0, 1, 1, 1]


def test_nested_when():
    """Test nested when-then-otherwise conditions."""
    df = pl.DataFrame({
        "score": [95, 85, 75, 65, 55]
    })

    # Test: letter grades using nested when
    expr = ma.when(ma.col("score") >= 90).then("A").otherwise(
        ma.when(ma.col("score") >= 80).then("B").otherwise(
            ma.when(ma.col("score") >= 70).then("C").otherwise("D")
        )
    )
    result = df.select(expr.compile(df).alias("grade"))
    assert result["grade"].to_list() == ["A", "B", "C", "D", "D"]


def test_coalesce():
    """Test coalesce - return first non-null value."""
    df = pl.DataFrame({
        "phone_mobile": ["555-1234", None, "555-5678", None],
        "phone_home": [None, "555-2345", None, "555-6789"],
        "phone_work": ["555-9999", "555-8888", "555-7777", None]
    })

    # Test: get first available phone number
    expr = ma.coalesce(ma.col("phone_mobile"), ma.col("phone_home"), ma.col("phone_work"))
    result = df.select(expr.compile(df).alias("phone"))
    assert result["phone"].to_list() == ["555-1234", "555-2345", "555-5678", "555-6789"]


def test_fill_null():
    """Test fill_null - replace nulls with a value."""
    df = pl.DataFrame({
        "score": [100, None, 85, None, 90],
        "name": ["Alice", "Bob", "Charlie", "David", "Eve"]
    })

    # Test: fill null scores with 0
    expr = ma.col("score").fill_null(0)
    result = df.select(expr.compile(df).alias("score_filled"))
    assert result["score_filled"].to_list() == [100, 0, 85, 0, 90]


def test_conditional_with_boolean_logic():
    """Test conditional combined with boolean operations."""
    df = pl.DataFrame({
        "age": [15, 25, 35, 45],
        "active": [True, True, False, True],
        "score": [70, 85, 90, 95]
    })

    # Test: when with AND condition
    expr = ma.when((ma.col("age") >= 18) & ma.col("active")).then("eligible").otherwise("not eligible")
    result = df.select(expr.compile(df).alias("status"))
    assert result["status"].to_list() == ["not eligible", "eligible", "not eligible", "eligible"]

    # Test: conditional based on score range
    expr = ma.when((ma.col("score") >= 80) & (ma.col("score") < 90)).then("B").otherwise("other")
    result = df.select(expr.compile(df).alias("grade"))
    assert result["grade"].to_list() == ["other", "B", "other", "other"]


def test_conditional_with_arithmetic():
    """Test conditional combined with arithmetic operations."""
    df = pl.DataFrame({
        "value": [10, 20, 30, 40, 50]
    })

    # Test: double if above threshold, keep if below
    expr = ma.when(ma.col("value") > 25).then(ma.col("value") * 2).otherwise(ma.col("value"))
    result = df.select(expr.compile(df).alias("result"))
    assert result["result"].to_list() == [10, 20, 60, 80, 100]


def test_cross_backend_conditional_compatibility():
    """Test that conditional operations produce same results across backends."""
    data = {
        "age": [20, 30, 40, 50, 60, 70],
        "score": [100, None, 85, None, 90, 95]
    }

    # Polars
    df_polars = pl.DataFrame(data)

    # Narwhals (wrapping Polars)
    df_narwhals = nw.from_native(df_polars)

    # Ibis
    con_ibis = ibis.duckdb.connect()
    df_ibis = con_ibis.create_table("test_conditional_cross", data)

    # Test 1: when-then-otherwise
    expr = ma.when(ma.col("age") >= 60).then("senior").otherwise("non-senior")

    result_polars = df_polars.select(expr.compile(df_polars).alias("result"))
    result_narwhals = df_narwhals.select(expr.compile(df_narwhals).alias("result"))
    ibis_expr = expr.compile(df_ibis).name("result")
    result_ibis = df_ibis.select(ibis_expr).execute()

    expected = ["non-senior", "non-senior", "non-senior", "non-senior", "senior", "senior"]
    assert result_polars["result"].to_list() == expected
    assert result_narwhals["result"].to_list() == expected
    assert result_ibis["result"].tolist() == expected

    # Test 2: fill_null
    expr = ma.col("score").fill_null(0)

    result_polars = df_polars.select(expr.compile(df_polars).alias("result"))
    result_narwhals = df_narwhals.select(expr.compile(df_narwhals).alias("result"))
    ibis_expr = expr.compile(df_ibis).name("result")
    result_ibis = df_ibis.select(ibis_expr).execute()

    expected = [100, 0, 85, 0, 90, 95]
    assert result_polars["result"].to_list() == expected
    assert result_narwhals["result"].to_list() == expected
    assert result_ibis["result"].tolist() == expected


def test_conditional_with_string_operations():
    """Test conditional combined with string operations."""
    df = pl.DataFrame({
        "name": ["alice", "BOB", "Charlie", None],
        "age": [25, 30, 35, 40]
    })

    # Test: uppercase name if age > 28, otherwise lowercase
    expr = ma.when(ma.col("age") > 28).then(
        ma.col("name").str_upper()
    ).otherwise(
        ma.col("name").str_lower()
    )
    result = df.select(expr.compile(df).alias("formatted_name"))
    expected_values = result["formatted_name"].to_list()
    # alice (age 25, <=28) -> lowercase -> alice
    # BOB (age 30, >28) -> uppercase -> BOB
    # Charlie (age 35, >28) -> uppercase -> CHARLIE
    # None (age 40, >28) -> None stays None
    assert expected_values[0] == "alice"
    assert expected_values[1] == "BOB"
    assert expected_values[2] == "CHARLIE"
    assert expected_values[3] is None


if __name__ == "__main__":
    print("Running conditional operation tests...")

    print("✓ test_when_then_otherwise")
    test_when_then_otherwise()

    print("✓ test_nested_when")
    test_nested_when()

    print("✓ test_coalesce")
    test_coalesce()

    print("✓ test_fill_null")
    test_fill_null()

    print("✓ test_conditional_with_boolean_logic")
    test_conditional_with_boolean_logic()

    print("✓ test_conditional_with_arithmetic")
    test_conditional_with_arithmetic()

    print("✓ test_cross_backend_conditional_compatibility")
    test_cross_backend_conditional_compatibility()

    print("✓ test_conditional_with_string_operations")
    test_conditional_with_string_operations()

    print("\n✅ All conditional tests passed!")
