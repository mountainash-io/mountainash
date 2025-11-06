#!/usr/bin/env python3
"""Test script for the public API."""

import sys
sys.path.insert(0, 'src')

import narwhals as nw
import polars as pl
import ibis

# Import the public API
import mountainash_expressions as ma


def test_basic_api():
    """Test basic public API functionality."""
    print("\n" + "="*60)
    print("Testing Basic Public API")
    print("="*60)

    # Create test dataframe
    df = pl.DataFrame({
        'age': [25, 30, 35, 40],
        'score': [85, 90, 75, 95],
        'name': ['Alice', 'Bob', 'Charlie', 'David']
    })

    print("\n--- Test 1: Simple Comparison ---")
    # Build expression
    expr = ma.col("age").gt(30)
    print(f"✓ Built expression: {expr}")

    # Compile to backend
    backend_expr = expr.compile(df)
    print(f"✓ Compiled to: {type(backend_expr)}")

    # Use with dataframe
    result = df.filter(backend_expr)
    print(f"✓ Filtered result: {result.shape[0]} rows")
    assert result.shape[0] == 2

    print("\n--- Test 2: Chained Operations ---")
    # Build complex expression
    expr = ma.col("age").gt(25).and_(ma.col("score").ge(85))
    backend_expr = expr.compile(df)
    result = df.filter(backend_expr)
    print(f"✓ Complex expression result: {result.shape[0]} rows")
    assert result.shape[0] == 2

    print("\n--- Test 3: Helper Function (filter) ---")
    # Use helper function
    result = ma.filter(df, ma.col("age").eq(30))
    print(f"✓ Helper function result: {result.shape[0]} rows")
    assert result.shape[0] == 1

    print("\n✅ Basic API tests passed!")


def test_comparison_operators():
    """Test all comparison operators."""
    print("\n" + "="*60)
    print("Testing Comparison Operators")
    print("="*60)

    df = pl.DataFrame({'value': [10, 20, 30, 40, 50]})

    tests = [
        ("eq", ma.col("value").eq(30), 1),
        ("ne", ma.col("value").ne(30), 4),
        ("gt", ma.col("value").gt(30), 2),
        ("lt", ma.col("value").lt(30), 2),
        ("ge", ma.col("value").ge(30), 3),
        ("le", ma.col("value").le(30), 3),
    ]

    for name, expr, expected_count in tests:
        result = df.filter(expr.compile(df))
        print(f"✓ {name}: {result.shape[0]} rows (expected {expected_count})")
        assert result.shape[0] == expected_count

    print("\n✅ All comparison operators working!")


def test_logical_operators():
    """Test logical operators."""
    print("\n" + "="*60)
    print("Testing Logical Operators")
    print("="*60)

    df = pl.DataFrame({
        'age': [25, 30, 35, 40],
        'score': [85, 90, 75, 95],
        'active': [True, True, False, True]
    })

    print("\n--- AND Operation ---")
    expr = ma.col("age").gt(25).and_(ma.col("score").ge(85))
    result = df.filter(expr.compile(df))
    print(f"✓ AND result: {result.shape[0]} rows")
    assert result.shape[0] == 2

    print("\n--- OR Operation ---")
    expr = ma.col("age").lt(28).or_(ma.col("age").gt(38))
    result = df.filter(expr.compile(df))
    print(f"✓ OR result: {result.shape[0]} rows")
    assert result.shape[0] == 2

    print("\n--- NOT Operation ---")
    expr = ma.col("active").not_()
    result = df.filter(expr.compile(df))
    print(f"✓ NOT result: {result.shape[0]} rows")
    assert result.shape[0] == 1

    print("\n✅ All logical operators working!")


def test_collection_operators():
    """Test collection operators."""
    print("\n" + "="*60)
    print("Testing Collection Operators")
    print("="*60)

    df = pl.DataFrame({'category': ['A', 'B', 'C', 'D', 'E']})

    print("\n--- IN Operation ---")
    expr = ma.col("category").is_in(['A', 'C', 'E'])
    result = df.filter(expr.compile(df))
    print(f"✓ IN result: {result.shape[0]} rows")
    assert result.shape[0] == 3

    print("\n--- NOT IN Operation ---")
    expr = ma.col("category").is_not_in(['B', 'D'])
    result = df.filter(expr.compile(df))
    print(f"✓ NOT IN result: {result.shape[0]} rows")
    assert result.shape[0] == 3

    print("\n✅ Collection operators working!")


def test_null_operators():
    """Test null operators."""
    print("\n" + "="*60)
    print("Testing Null Operators")
    print("="*60)

    df = pl.DataFrame({'value': [10, None, 30, None, 50]})

    print("\n--- IS NULL Operation ---")
    expr = ma.col("value").is_null()
    result = df.filter(expr.compile(df))
    print(f"✓ IS NULL result: {result.shape[0]} rows")
    assert result.shape[0] == 2

    print("\n--- IS NOT NULL Operation ---")
    expr = ma.col("value").is_not_null()
    result = df.filter(expr.compile(df))
    print(f"✓ IS NOT NULL result: {result.shape[0]} rows")
    assert result.shape[0] == 3

    print("\n✅ Null operators working!")


def test_combinators():
    """Test logical combinator helper functions."""
    print("\n" + "="*60)
    print("Testing Logical Combinators")
    print("="*60)

    df = pl.DataFrame({
        'age': [25, 30, 35, 40],
        'score': [85, 90, 75, 95],
        'active': [True, True, False, True]
    })

    print("\n--- and_() Combinator ---")
    expr = ma.and_(
        ma.col("age").gt(25),
        ma.col("score").ge(85),
        ma.col("active").eq(True)
    )
    result = df.filter(expr.compile(df))
    print(f"✓ and_() result: {result.shape[0]} rows")
    assert result.shape[0] == 2

    print("\n--- or_() Combinator ---")
    expr = ma.or_(
        ma.col("age").lt(28),
        ma.col("age").gt(38)
    )
    result = df.filter(expr.compile(df))
    print(f"✓ or_() result: {result.shape[0]} rows")
    assert result.shape[0] == 2

    print("\n--- not_() Combinator ---")
    expr = ma.not_(ma.col("active"))
    result = df.filter(expr.compile(df))
    print(f"✓ not_() result: {result.shape[0]} rows")
    assert result.shape[0] == 1

    print("\n✅ All combinators working!")


def test_cross_backend_api():
    """Test that the same API works across all backends."""
    print("\n" + "="*60)
    print("Testing Cross-Backend API Compatibility")
    print("="*60)

    data = {'age': [25, 30, 35, 40], 'score': [85, 90, 75, 95]}

    # Build expression once
    expr = ma.col("age").gt(30).and_(ma.col("score").ge(85))

    # Test with Polars
    print("\n--- Polars Backend ---")
    pl_df = pl.DataFrame(data)
    pl_result = pl_df.filter(expr.compile(pl_df))
    print(f"✓ Polars result: {pl_result.shape[0]} rows")

    # Test with Narwhals
    print("\n--- Narwhals Backend ---")
    nw_df = nw.from_native(pl.DataFrame(data))
    nw_result = nw_df.filter(expr.compile(nw_df))
    print(f"✓ Narwhals result: {nw_result.shape[0]} rows")

    # Test with Ibis
    print("\n--- Ibis Backend ---")
    ibis_df = ibis.memtable(data)
    ibis_result = ibis_df.filter(expr.compile(ibis_df))
    print(f"✓ Ibis result: {ibis_result.count().execute()} rows")

    # Verify all backends produce same result
    assert pl_result.shape[0] == nw_result.shape[0] == ibis_result.count().execute() == 1

    print("\n✅ Same API works across all three backends!")


def test_python_operators():
    """Test Python magic operators (&, |, ~, ==, etc.)."""
    print("\n" + "="*60)
    print("Testing Python Magic Operators")
    print("="*60)

    df = pl.DataFrame({
        'age': [25, 30, 35, 40],
        'score': [85, 90, 75, 95]
    })

    print("\n--- Using & operator for AND ---")
    expr = (ma.col("age") > 25) & (ma.col("score") >= 85)
    result = df.filter(expr.compile(df))
    print(f"✓ & operator result: {result.shape[0]} rows")
    assert result.shape[0] == 2

    print("\n--- Using | operator for OR ---")
    expr = (ma.col("age") < 28) | (ma.col("age") > 38)
    result = df.filter(expr.compile(df))
    print(f"✓ | operator result: {result.shape[0]} rows")
    assert result.shape[0] == 2

    print("\n--- Using == operator ---")
    expr = ma.col("age") == 30
    result = df.filter(expr.compile(df))
    print(f"✓ == operator result: {result.shape[0]} rows")
    assert result.shape[0] == 1

    print("\n✅ Python magic operators working!")


def main():
    """Run all tests."""
    print("="*60)
    print("Testing Mountain Ash Public API")
    print("="*60)

    try:
        test_basic_api()
        test_comparison_operators()
        test_logical_operators()
        test_collection_operators()
        test_null_operators()
        test_combinators()
        test_cross_backend_api()
        test_python_operators()

        print("\n" + "="*60)
        print("✅ ALL PUBLIC API TESTS PASSED!")
        print("="*60)
        print("\n🎉 The public API is working perfectly!")
        print("\nYou can now use:")
        print("  >>> import mountainash_expressions as ma")
        print("  >>> expr = ma.col('age').gt(30)")
        print("  >>> result = ma.filter(df, expr)")
        print("="*60)
        return 0

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
