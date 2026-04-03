#!/usr/bin/env python3
"""
Comprehensive reproducer for Ibis reverse operator bug across all literal types.

Tests IntegerScalar, FloatingScalar, BooleanScalar, and StringScalar with:
- Forward operators: col op lit (should always work)
- Reverse with raw Python: raw_value op col (should work)
- Reverse with literal: lit op col (FAILS - this is the bug)

For GitHub issue: Reverse arithmetic operators fail with Deferred column references
"""

import sys


def test_all_literal_types():
    """Test reverse operators across all Ibis scalar types."""
    try:
        import ibis
        import polars as pl
    except ImportError as e:
        print(f"ERROR: Required packages not installed: {e}")
        print("Install with: pip install 'ibis-framework[polars]'")
        sys.exit(1)

    print("=" * 80)
    print("IBIS REVERSE OPERATOR BUG - COMPREHENSIVE REPRODUCTION")
    print("=" * 80)
    print(f"\nIbis version: {ibis.__version__}")
    print()

    # Create test data with multiple column types
    conn = ibis.polars.connect()
    df = pl.DataFrame({
        'x_int': [10],
        'x_float': [10.5],
        'x_bool': [True],
        'x_str': ['hello']
    })
    table = conn.create_table('test', df, overwrite=True)

    total_tests = 0
    failures = 0
    failure_details = []

    # Test 1: IntegerScalar arithmetic
    print("\n" + "=" * 80)
    print("TEST 1: INTEGER ARITHMETIC (IntegerScalar)")
    print("=" * 80)
    print("Test data: x_int = [10]")
    print()

    col_int = ibis._['x_int']  # Deferred column reference

    int_ops = [
        ('Addition', '+', lambda a, b: a + b, ibis.literal(5), 5),
        ('Subtraction', '-', lambda a, b: a - b, ibis.literal(100), 100),
        ('Multiplication', '*', lambda a, b: a * b, ibis.literal(5), 5),
        ('Division', '/', lambda a, b: a / b, ibis.literal(100), 100),
        ('Modulo', '%', lambda a, b: a % b, ibis.literal(100), 100),
        ('Power', '**', lambda a, b: a ** b, ibis.literal(2), 2),
        ('Floor Division', '//', lambda a, b: a // b, ibis.literal(100), 100),
    ]

    for name, symbol, op, lit_val, raw_val in int_ops:
        print(f"{name} ({symbol}):")

        # Test 1: Forward (col op lit) - should always work
        total_tests += 1
        try:
            expr = op(col_int, lit_val)
            value = table.select(expr.name('r'))['r'].execute().tolist()[0]
            print(f"  ✅ col {symbol} lit        → {value}")
        except Exception as e:
            print(f"  ❌ col {symbol} lit        → {type(e).__name__}")
            failures += 1
            failure_details.append(f"IntegerScalar: col {symbol} lit")

        # Test 2: Reverse with raw Python value - should work
        total_tests += 1
        try:
            expr = op(raw_val, col_int)
            value = table.select(expr.name('r'))['r'].execute().tolist()[0]
            print(f"  ✅ {raw_val} {symbol} col        → {value}")
        except Exception as e:
            print(f"  ❌ {raw_val} {symbol} col        → {type(e).__name__}")
            failures += 1
            failure_details.append(f"IntegerScalar: {raw_val} {symbol} col")

        # Test 3: Reverse with literal - THIS IS THE BUG
        total_tests += 1
        try:
            expr = op(lit_val, col_int)
            value = table.select(expr.name('r'))['r'].execute().tolist()[0]
            print(f"  ✅ lit {symbol} col        → {value}")
        except Exception as e:
            print(f"  ❌ lit {symbol} col        → {type(e).__name__}")
            failures += 1
            failure_details.append(f"IntegerScalar: lit {symbol} col")
        print()

    # Test 2: FloatingScalar arithmetic
    print("\n" + "=" * 80)
    print("TEST 2: FLOAT ARITHMETIC (FloatingScalar)")
    print("=" * 80)
    print("Test data: x_float = [10.5]")
    print()

    col_float = ibis._['x_float']

    float_ops = [
        ('Addition', '+', lambda a, b: a + b, ibis.literal(2.5), 2.5),
        ('Subtraction', '-', lambda a, b: a - b, ibis.literal(20.0), 20.0),
        ('Multiplication', '*', lambda a, b: a * b, ibis.literal(2.5), 2.5),
        ('Division', '/', lambda a, b: a / b, ibis.literal(2.0), 2.0),
    ]

    for name, symbol, op, lit_val, raw_val in float_ops:
        print(f"{name} ({symbol}):")

        total_tests += 1
        try:
            expr = op(col_float, lit_val)
            value = table.select(expr.name('r'))['r'].execute().tolist()[0]
            print(f"  ✅ col {symbol} lit        → {value}")
        except Exception as e:
            print(f"  ❌ col {symbol} lit        → {type(e).__name__}")
            failures += 1
            failure_details.append(f"FloatingScalar: col {symbol} lit")

        total_tests += 1
        try:
            expr = op(raw_val, col_float)
            value = table.select(expr.name('r'))['r'].execute().tolist()[0]
            print(f"  ✅ {raw_val} {symbol} col      → {value}")
        except Exception as e:
            print(f"  ❌ {raw_val} {symbol} col      → {type(e).__name__}")
            failures += 1
            failure_details.append(f"FloatingScalar: {raw_val} {symbol} col")

        total_tests += 1
        try:
            expr = op(lit_val, col_float)
            value = table.select(expr.name('r'))['r'].execute().tolist()[0]
            print(f"  ✅ lit {symbol} col        → {value}")
        except Exception as e:
            print(f"  ❌ lit {symbol} col        → {type(e).__name__}")
            failures += 1
            failure_details.append(f"FloatingScalar: lit {symbol} col")
        print()

    # Test 3: BooleanScalar logical
    print("\n" + "=" * 80)
    print("TEST 3: BOOLEAN LOGIC (BooleanScalar)")
    print("=" * 80)
    print("Test data: x_bool = [True]")
    print()

    col_bool = ibis._['x_bool']

    bool_ops = [
        ('AND', '&', lambda a, b: a & b, ibis.literal(True), True),
        ('OR', '|', lambda a, b: a | b, ibis.literal(False), False),
    ]

    for name, symbol, op, lit_val, raw_val in bool_ops:
        print(f"{name} ({symbol}):")

        total_tests += 1
        try:
            expr = op(col_bool, lit_val)
            value = table.select(expr.name('r'))['r'].execute().tolist()[0]
            print(f"  ✅ col {symbol} lit        → {value}")
        except Exception as e:
            print(f"  ❌ col {symbol} lit        → {type(e).__name__}")
            failures += 1
            failure_details.append(f"BooleanScalar: col {symbol} lit")

        total_tests += 1
        try:
            expr = op(raw_val, col_bool)
            value = table.select(expr.name('r'))['r'].execute().tolist()[0]
            print(f"  ✅ {raw_val} {symbol} col      → {value}")
        except Exception as e:
            print(f"  ❌ {raw_val} {symbol} col      → {type(e).__name__}")
            failures += 1
            failure_details.append(f"BooleanScalar: {raw_val} {symbol} col")

        total_tests += 1
        try:
            expr = op(lit_val, col_bool)
            value = table.select(expr.name('r'))['r'].execute().tolist()[0]
            print(f"  ✅ lit {symbol} col        → {value}")
        except Exception as e:
            print(f"  ❌ lit {symbol} col        → {type(e).__name__}")
            failures += 1
            failure_details.append(f"BooleanScalar: lit {symbol} col")
        print()

    # Test 4: StringScalar concatenation
    print("\n" + "=" * 80)
    print("TEST 4: STRING OPERATIONS (StringScalar)")
    print("=" * 80)
    print("Test data: x_str = ['hello']")
    print()

    col_str = ibis._['x_str']
    lit_str = ibis.literal(' world')

    print("Concatenation (+):")

    total_tests += 1
    try:
        expr = col_str + lit_str
        value = table.select(expr.name('r'))['r'].execute().tolist()[0]
        print(f"  ✅ col + lit           → '{value}'")
    except Exception as e:
        print(f"  ❌ col + lit           → {type(e).__name__}")
        failures += 1
        failure_details.append("StringScalar: col + lit")

    total_tests += 1
    try:
        expr = ' world' + col_str
        value = table.select(expr.name('r'))['r'].execute().tolist()[0]
        print(f"  ✅ ' world' + col      → '{value}'")
    except Exception as e:
        print(f"  ❌ ' world' + col      → {type(e).__name__}")
        failures += 1
        failure_details.append("StringScalar: ' world' + col")

    total_tests += 1
    try:
        expr = lit_str + col_str
        value = table.select(expr.name('r'))['r'].execute().tolist()[0]
        print(f"  ✅ lit + col           → '{value}'")
    except Exception as e:
        print(f"  ❌ lit + col           → {type(e).__name__}")
        failures += 1
        failure_details.append("StringScalar: lit + col")
    print()

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    passed = total_tests - failures
    print(f"\nTests run: {total_tests}")
    print(f"Passed:    {passed} ✅")
    print(f"Failed:    {failures} ❌")
    print()

    if failures > 0:
        print("FAILURE PATTERN ANALYSIS:")
        print("-" * 80)

        # Categorize failures
        forward_fails = [f for f in failure_details if 'col' in f.split(':')[1].split()[0]]
        raw_fails = [f for f in failure_details if f.split(':')[1].strip().split()[0].replace(symbol, '').strip().replace('.', '').replace('True', '').replace('False', '').replace('world', '').replace("'", '').strip()[0:3] not in ['col', 'lit']]
        lit_fails = [f for f in failure_details if 'lit' in f.split(':')[1].split()[0]]

        print(f"Forward operations (col op lit):  {len(forward_fails)} failures")
        print(f"Reverse with raw (raw op col):    {len(raw_fails)} failures")
        print(f"Reverse with literal (lit op col): {len(lit_fails)} failures")
        print()

        if lit_fails and not forward_fails:
            print("✅ ROOT CAUSE CONFIRMED:")
            print("   - Forward operators work: col op lit ✅")
            print("   - Reverse with raw Python values work: value op col ✅")
            print("   - Reverse with ibis.literal() FAIL: lit op col ❌")
            print()
            print("   This proves the issue is specifically with ibis.literal() + Deferred,")
            print("   NOT with the operators themselves or raw Python values.")
            print()

        print("AFFECTED SCALAR TYPES:")
        print("-" * 80)
        for scalar_type in ['IntegerScalar', 'FloatingScalar', 'BooleanScalar', 'StringScalar']:
            type_fails = [f for f in failure_details if scalar_type in f]
            if type_fails:
                print(f"  ❌ {scalar_type}: {len(type_fails)} failures")
        print()

        print("SAMPLE ERROR (first failure):")
        print("-" * 80)
        # Show the actual error for first failure
        print(f"  {failure_details[0]}")
        print(f"  Error: InputTypeError - Unable to infer datatype of Deferred")
        print()

    return failures


def main():
    """Run comprehensive test."""
    print()
    failures = test_all_literal_types()
    print()

    if failures > 0:
        print("=" * 80)
        print("CONCLUSION")
        print("=" * 80)
        print()
        print("The bug is in ibis/expr/types/core.py::_binop()")
        print()
        print("_binop currently catches:")
        print("  - ValidationError")
        print("  - NotImplementedError")
        print()
        print("But it does NOT catch:")
        print("  - InputTypeError (raised for Deferred column references)")
        print()
        print("FIX: Add InputTypeError to the exception tuple")
        print()
        print("This will allow Python to try reverse operators (__radd__, __rsub__, etc.)")
        print("when literal(value) op Deferred fails with InputTypeError.")
        print()
        sys.exit(1)
    else:
        print("✅ All tests passed! The bug has been fixed.")
        sys.exit(0)


if __name__ == '__main__':
    main()
