#!/usr/bin/env python3
"""
Verification script for Ibis _binop contract violation fix.

This script demonstrates that the one-line fix to _binop restores
the documented behavior and enables reverse operators with ibis.literal().

Usage:
    python ibis_fix_verification.py

Expected output: All tests pass ✅
"""

import sys


def verify_fix():
    """Verify the _binop fix works for all numeric and boolean types."""
    try:
        import ibis
        import polars as pl
    except ImportError as e:
        print(f"ERROR: Required packages not installed: {e}")
        print("Install with: pip install 'ibis-framework[polars]'")
        sys.exit(1)

    print("=" * 70)
    print("IBIS _binop FIX VERIFICATION")
    print("=" * 70)
    print(f"\nIbis version: {ibis.__version__}")
    print()

    # Create test data
    conn = ibis.polars.connect()
    df = pl.DataFrame({
        'x_int': [10],
        'x_float': [10.5],
        'x_bool': [True],
    })
    table = conn.create_table('test', df, overwrite=True)

    failures = 0
    tests_run = 0

    # Test 1: IntegerScalar arithmetic
    print("Testing IntegerScalar reverse operators:")
    int_tests = [
        ('+', lambda: ibis.literal(5) + ibis._['x_int'], 15),
        ('-', lambda: ibis.literal(100) - ibis._['x_int'], 90),
        ('*', lambda: ibis.literal(5) * ibis._['x_int'], 50),
        ('/', lambda: ibis.literal(100) / ibis._['x_int'], 10.0),
        ('%', lambda: ibis.literal(100) % ibis._['x_int'], 0),
        ('//', lambda: ibis.literal(100) // ibis._['x_int'], 10),
    ]

    for op, expr_fn, expected in int_tests:
        tests_run += 1
        try:
            expr = expr_fn()
            result = table.select(expr.name('r'))['r'].execute().tolist()[0]
            if result == expected:
                print(f"  ✅ literal(n) {op} col → {result}")
            else:
                print(f"  ❌ literal(n) {op} col → {result} (expected {expected})")
                failures += 1
        except Exception as e:
            print(f"  ❌ literal(n) {op} col → {type(e).__name__}")
            failures += 1

    print()

    # Test 2: FloatingScalar arithmetic
    print("Testing FloatingScalar reverse operators:")
    float_tests = [
        ('+', lambda: ibis.literal(2.5) + ibis._['x_float'], 13.0),
        ('-', lambda: ibis.literal(20.0) - ibis._['x_float'], 9.5),
        ('*', lambda: ibis.literal(2.5) * ibis._['x_float'], 26.25),
    ]

    for op, expr_fn, expected in float_tests:
        tests_run += 1
        try:
            expr = expr_fn()
            result = table.select(expr.name('r'))['r'].execute().tolist()[0]
            if result == expected:
                print(f"  ✅ literal(n) {op} col → {result}")
            else:
                print(f"  ❌ literal(n) {op} col → {result} (expected {expected})")
                failures += 1
        except Exception as e:
            print(f"  ❌ literal(n) {op} col → {type(e).__name__}")
            failures += 1

    print()

    # Test 3: BooleanScalar logical
    print("Testing BooleanScalar reverse operators:")
    bool_tests = [
        ('&', lambda: ibis.literal(True) & ibis._['x_bool'], True),
        ('|', lambda: ibis.literal(False) | ibis._['x_bool'], True),
    ]

    for op, expr_fn, expected in bool_tests:
        tests_run += 1
        try:
            expr = expr_fn()
            result = table.select(expr.name('r'))['r'].execute().tolist()[0]
            if result == expected:
                print(f"  ✅ literal(n) {op} col → {result}")
            else:
                print(f"  ❌ literal(n) {op} col → {result} (expected {expected})")
                failures += 1
        except Exception as e:
            print(f"  ❌ literal(n) {op} col → {type(e).__name__}")
            failures += 1

    print()

    # Test 4: Verify order preservation for non-commutative operations
    print("Verifying order preservation (non-commutative operations):")

    tests_run += 1
    try:
        # Subtraction: 100 - 10 = 90 (not 10 - 100 = -90)
        expr = ibis.literal(100) - ibis._['x_int']
        result = table.select(expr.name('r'))['r'].execute().tolist()[0]
        if result == 90:
            print(f"  ✅ 100 - col(10) → {result} (correct order)")
        else:
            print(f"  ❌ 100 - col(10) → {result} (expected 90)")
            failures += 1
    except Exception as e:
        print(f"  ❌ Subtraction order → {type(e).__name__}")
        failures += 1

    tests_run += 1
    try:
        # Division: 100 / 10 = 10.0 (not 10 / 100 = 0.1)
        expr = ibis.literal(100) / ibis._['x_int']
        result = table.select(expr.name('r'))['r'].execute().tolist()[0]
        if result == 10.0:
            print(f"  ✅ 100 / col(10) → {result} (correct order)")
        else:
            print(f"  ❌ 100 / col(10) → {result} (expected 10.0)")
            failures += 1
    except Exception as e:
        print(f"  ❌ Division order → {type(e).__name__}")
        failures += 1

    # Summary
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    passed = tests_run - failures
    print(f"\nTests run: {tests_run}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failures} {'❌' if failures > 0 else ''}")
    print()

    if failures == 0:
        print("✅ All tests passed! The fix works correctly.")
        print()
        print("The _binop fix successfully:")
        print("  • Enables reverse operators for ibis.literal()")
        print("  • Preserves order for non-commutative operations")
        print("  • Maintains consistency with documented behavior")
        print("  • Works across IntegerScalar, FloatingScalar, and BooleanScalar")
        return 0
    else:
        print(f"❌ {failures} test(s) failed.")
        print()
        print("The fix may not be applied correctly or there are other issues.")
        return 1


def main():
    """Run verification."""
    print()
    exit_code = verify_fix()
    print()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
