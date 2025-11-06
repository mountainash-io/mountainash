#!/usr/bin/env python3
"""
Test suite for arithmetic operations in Mountain Ash Expressions.

Tests arithmetic operations across all backends (Polars, Narwhals, Ibis).
"""

import sys
sys.path.insert(0, 'src')

import polars as pl
import pandas as pd
import narwhals as nw
import ibis

import mountainash_expressions as ma

def test_basic_arithmetic():
    """Test basic arithmetic operations."""
    print("\n" + "=" * 60)
    print("Testing Basic Arithmetic Operations")
    print("=" * 60)

    # Create test DataFrame
    df = pl.DataFrame({
        "a": [10, 20, 30, 40, 50],
        "b": [2, 3, 4, 5, 6],
        "c": [1, 2, 3, 4, 5]
    })

    # Test addition
    expr = ma.col("a").add(ma.col("b"))
    result = df.select(expr.compile(df).alias("result"))
    print(f"\n✓ Addition (a + b):")
    print(result)
    assert result["result"].to_list() == [12, 23, 34, 45, 56]

    # Test subtraction
    expr = ma.col("a").subtract(ma.col("b"))
    result = df.select(expr.compile(df).alias("result"))
    print(f"\n✓ Subtraction (a - b):")
    print(result)
    assert result["result"].to_list() == [8, 17, 26, 35, 44]

    # Test multiplication
    expr = ma.col("a").multiply(ma.col("c"))
    result = df.select(expr.compile(df).alias("result"))
    print(f"\n✓ Multiplication (a * c):")
    print(result)
    assert result["result"].to_list() == [10, 40, 90, 160, 250]

    # Test division
    expr = ma.col("a").divide(ma.col("b"))
    result = df.select(expr.compile(df).alias("result"))
    print(f"\n✓ Division (a / b):")
    print(result)
    expected = [10/2, 20/3, 30/4, 40/5, 50/6]
    actual = result["result"].to_list()
    for i in range(len(expected)):
        assert abs(actual[i] - expected[i]) < 0.0001

    # Test modulo
    expr = ma.col("a").modulo(ma.col("b"))
    result = df.select(expr.compile(df).alias("result"))
    print(f"\n✓ Modulo (a % b):")
    print(result)
    assert result["result"].to_list() == [0, 2, 2, 0, 2]

    # Test power
    expr = ma.col("c").power(2)
    result = df.select(expr.compile(df).alias("result"))
    print(f"\n✓ Power (c ** 2):")
    print(result)
    assert result["result"].to_list() == [1, 4, 9, 16, 25]

    # Test floor division
    expr = ma.col("a").floor_divide(ma.col("b"))
    result = df.select(expr.compile(df).alias("result"))
    print(f"\n✓ Floor Division (a // b):")
    print(result)
    assert result["result"].to_list() == [5, 6, 7, 8, 8]

    print(f"\n✅ All basic arithmetic operations passed!")


def test_python_operators():
    """Test Python magic operators for arithmetic."""
    print("\n" + "=" * 60)
    print("Testing Python Magic Operators")
    print("=" * 60)

    df = pl.DataFrame({
        "x": [10, 20, 30],
        "y": [2, 4, 5]
    })

    # Test + operator
    expr = ma.col("x") + ma.col("y")
    result = df.select(expr.compile(df).alias("result"))
    print(f"\n✓ Using + operator (x + y):")
    print(result)
    assert result["result"].to_list() == [12, 24, 35]

    # Test - operator
    expr = ma.col("x") - ma.col("y")
    result = df.select(expr.compile(df).alias("result"))
    print(f"\n✓ Using - operator (x - y):")
    print(result)
    assert result["result"].to_list() == [8, 16, 25]

    # Test * operator
    expr = ma.col("x") * ma.col("y")
    result = df.select(expr.compile(df).alias("result"))
    print(f"\n✓ Using * operator (x * y):")
    print(result)
    assert result["result"].to_list() == [20, 80, 150]

    # Test / operator
    expr = ma.col("x") / ma.col("y")
    result = df.select(expr.compile(df).alias("result"))
    print(f"\n✓ Using / operator (x / y):")
    print(result)
    expected = [10/2, 20/4, 30/5]
    actual = result["result"].to_list()
    for i in range(len(expected)):
        assert abs(actual[i] - expected[i]) < 0.0001

    # Test % operator
    expr = ma.col("x") % ma.col("y")
    result = df.select(expr.compile(df).alias("result"))
    print(f"\n✓ Using % operator (x % y):")
    print(result)
    assert result["result"].to_list() == [0, 0, 0]

    # Test ** operator
    expr = ma.col("y") ** 2
    result = df.select(expr.compile(df).alias("result"))
    print(f"\n✓ Using ** operator (y ** 2):")
    print(result)
    assert result["result"].to_list() == [4, 16, 25]

    # Test // operator
    expr = ma.col("x") // ma.col("y")
    result = df.select(expr.compile(df).alias("result"))
    print(f"\n✓ Using // operator (x // y):")
    print(result)
    assert result["result"].to_list() == [5, 5, 6]

    print(f"\n✅ All Python magic operators passed!")


def test_reverse_operators():
    """Test reverse operators (literal on left side)."""
    print("\n" + "=" * 60)
    print("Testing Reverse Operators")
    print("=" * 60)

    df = pl.DataFrame({
        "x": [1, 2, 3, 4, 5]
    })

    # Test 10 + col("x")
    expr = 10 + ma.col("x")
    result = df.select(expr.compile(df).alias("result"))
    print(f"\n✓ Reverse add (10 + x):")
    print(result)
    assert result["result"].to_list() == [11, 12, 13, 14, 15]

    # Test 10 - col("x")
    expr = 10 - ma.col("x")
    result = df.select(expr.compile(df).alias("result"))
    print(f"\n✓ Reverse subtract (10 - x):")
    print(result)
    assert result["result"].to_list() == [9, 8, 7, 6, 5]

    # Test 2 * col("x")
    expr = 2 * ma.col("x")
    result = df.select(expr.compile(df).alias("result"))
    print(f"\n✓ Reverse multiply (2 * x):")
    print(result)
    assert result["result"].to_list() == [2, 4, 6, 8, 10]

    # Test 100 / col("x")
    expr = 100 / ma.col("x")
    result = df.select(expr.compile(df).alias("result"))
    print(f"\n✓ Reverse divide (100 / x):")
    print(result)
    expected = [100/1, 100/2, 100/3, 100/4, 100/5]
    actual = result["result"].to_list()
    for i in range(len(expected)):
        assert abs(actual[i] - expected[i]) < 0.0001

    print(f"\n✅ All reverse operators passed!")


def test_chained_arithmetic():
    """Test chained arithmetic operations."""
    print("\n" + "=" * 60)
    print("Testing Chained Arithmetic")
    print("=" * 60)

    df = pl.DataFrame({
        "price": [100, 200, 300],
        "quantity": [2, 3, 4],
        "discount": [10, 20, 30],
        "tax_rate": [0.1, 0.15, 0.2]
    })

    # Test: (price * quantity - discount) * (1 + tax_rate)
    expr = (ma.col("price") * ma.col("quantity") - ma.col("discount")) * (1 + ma.col("tax_rate"))
    result = df.select(expr.compile(df).alias("total"))
    print(f"\n✓ Complex calculation: (price * quantity - discount) * (1 + tax_rate)")
    print(result)

    # Verify calculations
    expected = [
        (100 * 2 - 10) * (1 + 0.1),   # 209
        (200 * 3 - 20) * (1 + 0.15),  # 667
        (300 * 4 - 30) * (1 + 0.2)    # 1404
    ]
    actual = result["total"].to_list()
    for i in range(len(expected)):
        assert abs(actual[i] - expected[i]) < 0.0001

    print(f"\n✅ Chained arithmetic passed!")


def test_arithmetic_with_filtering():
    """Test combining arithmetic with boolean filtering."""
    print("\n" + "=" * 60)
    print("Testing Arithmetic with Filtering")
    print("=" * 60)

    df = pl.DataFrame({
        "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
        "base_salary": [50000, 60000, 70000, 80000, 90000],
        "bonus_pct": [0.1, 0.15, 0.2, 0.25, 0.3]
    })

    # Calculate total compensation and filter
    total_comp = ma.col("base_salary") * (1 + ma.col("bonus_pct"))

    # Filter for total compensation > 75000
    filter_expr = total_comp.gt(75000)

    result = df.filter(filter_expr.compile(df)).select([
        pl.col("name"),
        total_comp.compile(df).alias("total_comp")
    ])

    print(f"\n✓ Employees with total compensation > 75000:")
    print(result)

    assert len(result) == 3  # Charlie, David, Eve
    assert result["name"].to_list() == ["Charlie", "David", "Eve"]

    print(f"\n✅ Arithmetic with filtering passed!")


def test_cross_backend_arithmetic():
    """Test arithmetic operations across different backends."""
    print("\n" + "=" * 60)
    print("Testing Cross-Backend Arithmetic")
    print("=" * 60)

    # Same expression: (a * b) + c
    expr = (ma.col("a") * ma.col("b")) + ma.col("c")

    # Test with Polars
    df_polars = pl.DataFrame({
        "a": [10, 20, 30],
        "b": [2, 3, 4],
        "c": [5, 10, 15]
    })
    result_polars = df_polars.select(expr.compile(df_polars).alias("result"))
    print(f"\n✓ Polars result:")
    print(result_polars)
    polars_values = result_polars["result"].to_list()

    # Test with Narwhals/Pandas
    df_pandas = pd.DataFrame({
        "a": [10, 20, 30],
        "b": [2, 3, 4],
        "c": [5, 10, 15]
    })
    df_nw = nw.from_native(df_pandas)
    result_nw = df_nw.select(expr.compile(df_nw).alias("result"))
    print(f"\n✓ Narwhals/Pandas result:")
    print(result_nw.to_native())
    nw_values = result_nw.to_native()["result"].to_list()

    # Test with Ibis
    ibis.set_backend("duckdb")
    df_ibis = ibis.memtable({
        "a": [10, 20, 30],
        "b": [2, 3, 4],
        "c": [5, 10, 15]
    })
    ibis_expr = expr.compile(df_ibis).name("result")
    result_ibis = df_ibis.select(ibis_expr)
    print(f"\n✓ Ibis result:")
    print(result_ibis.execute())
    ibis_values = result_ibis.execute()["result"].to_list()

    # Verify all backends produce same results
    expected = [25, 70, 135]  # (10*2)+5, (20*3)+10, (30*4)+15
    assert polars_values == expected
    assert nw_values == expected
    assert ibis_values == expected

    print(f"\n✅ Same arithmetic expression works across all three backends!")


def test_arithmetic_with_literals():
    """Test arithmetic operations with literal values."""
    print("\n" + "=" * 60)
    print("Testing Arithmetic with Literals")
    print("=" * 60)

    df = pl.DataFrame({
        "base": [100, 200, 300]
    })

    # Test with ma.lit()
    expr = ma.col("base") * ma.lit(1.1)
    result = df.select(expr.compile(df).alias("result"))
    print(f"\n✓ Using ma.lit(): base * ma.lit(1.1)")
    print(result)
    expected = [110.0, 220.0, 330.0]
    actual = result["result"].to_list()
    for i in range(len(expected)):
        assert abs(actual[i] - expected[i]) < 0.0001

    # Test with direct literal
    expr = ma.col("base") * 1.1
    result = df.select(expr.compile(df).alias("result"))
    print(f"\n✓ Using direct literal: base * 1.1")
    print(result)
    actual = result["result"].to_list()
    for i in range(len(expected)):
        assert abs(actual[i] - expected[i]) < 0.0001

    print(f"\n✅ Arithmetic with literals passed!")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Mountain Ash Expressions - Arithmetic Operations Tests")
    print("=" * 60)

    try:
        test_basic_arithmetic()
        test_python_operators()
        test_reverse_operators()
        test_chained_arithmetic()
        test_arithmetic_with_filtering()
        test_cross_backend_arithmetic()
        test_arithmetic_with_literals()

        print("\n" + "=" * 60)
        print("✅ ALL ARITHMETIC TESTS PASSED!")
        print("=" * 60)
        print("""
🎉 Arithmetic operations are fully functional!

Supported operations:
  - Addition: col("a") + col("b") or col("a").add(col("b"))
  - Subtraction: col("a") - col("b") or col("a").subtract(col("b"))
  - Multiplication: col("a") * col("b") or col("a").multiply(col("b"))
  - Division: col("a") / col("b") or col("a").divide(col("b"))
  - Modulo: col("a") % col("b") or col("a").modulo(col("b"))
  - Power: col("a") ** 2 or col("a").power(2)
  - Floor Division: col("a") // col("b") or col("a").floor_divide(col("b"))

Works across all backends: Polars, Narwhals (Pandas), and Ibis!
        """)
        return 0

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
