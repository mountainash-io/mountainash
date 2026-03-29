#!/usr/bin/env python3
"""
Minimal reproducer comparing Ibis vs Polars operator behavior.

Shows that Polars handles all cases correctly, while Ibis fails
with ibis.literal() on the left side of operators.
"""

import sys


def test_ibis():
    """Test Ibis operator behavior."""
    try:
        import ibis
        import polars as pl
    except ImportError:
        print("ERROR: ibis or polars not installed")
        return 0

    print("=" * 60)
    print("IBIS EXPRESSIONS")
    print("=" * 60)

    # Create test data with multiple column types
    conn = ibis.polars.connect()
    df = pl.DataFrame({
        'x_int': [10],
        'x_float': [10.5],
        'x_bool': [True],
        'x_str': ['hello']
    })
    table = conn.create_table('test_ibis', df, overwrite=True)

    failures = 0

    # Test 1: IntegerScalar arithmetic
    print(f"\n{'='*60}")
    print("1. INTEGER ARITHMETIC (IntegerScalar)")
    print(f"{'='*60}")
    print(f"Test data: x_int = [10]")
    print()

    col_int = ibis._['x_int']
    lit_int = ibis.literal(5)
    lit_100 = ibis.literal(100)

    print(f"Types: col={type(col_int).__name__}, lit={type(lit_int).__name__}")
    print()

    int_ops = [
        ('Addition', '+', lambda a, b: a + b, lit_int, 5),
        ('Subtraction', '-', lambda a, b: a - b, lit_100, 100),
        ('Multiplication', '*', lambda a, b: a * b, lit_int, 5),
        ('Division', '/', lambda a, b: a / b, lit_100, 100),
        ('Modulo', '%', lambda a, b: a % b, lit_100, 100),
        ('Power', '**', lambda a, b: a ** b, ibis.literal(2), 2),
        ('Floor Division', '//', lambda a, b: a // b, lit_100, 100),
    ]

    for name, symbol, op, lit_val, raw_val in int_ops:
        print(f"{name} ({symbol}):")

        # Forward
        try:
            expr = op(col_int, lit_val)
            value = table.select(expr.name('result'))['result'].execute().tolist()[0]
            print(f"  ✅ col {symbol} lit      → {expr} → {value}")
        except Exception as e:
            print(f"  ❌ col {symbol} lit      → {type(e).__name__}")
            failures += 1

        # Reverse with raw
        try:
            expr = op(raw_val, col_int)
            value = table.select(expr.name('result'))['result'].execute().tolist()[0]
            print(f"  ✅ {raw_val} {symbol} col      → {expr} → {value}")
        except Exception as e:
            print(f"  ❌ {raw_val} {symbol} col      → {type(e).__name__}")
            failures += 1

        # Reverse with literal
        try:
            expr = op(lit_val, col_int)
            value = table.select(expr.name('result'))['result'].execute().tolist()[0]
            print(f"  ✅ lit {symbol} col      → {expr} → {value}")
        except Exception as e:
            print(f"  ❌ lit {symbol} col      → {type(e).__name__}")
            failures += 1
        print()

    # Test 2: FloatingScalar arithmetic
    print(f"\n{'='*60}")
    print("2. FLOAT ARITHMETIC (FloatingScalar)")
    print(f"{'='*60}")
    print(f"Test data: x_float = [10.5]")
    print()

    col_float = ibis._['x_float']
    lit_float = ibis.literal(2.5)

    print(f"Types: col={type(col_float).__name__}, lit={type(lit_float).__name__}")
    print()

    float_ops = [
        ('Addition', '+', lambda a, b: a + b, lit_float, 2.5),
        ('Subtraction', '-', lambda a, b: a - b, ibis.literal(20.0), 20.0),
        ('Multiplication', '*', lambda a, b: a * b, lit_float, 2.5),
    ]

    for name, symbol, op, lit_val, raw_val in float_ops:
        print(f"{name} ({symbol}):")

        try:
            expr = op(col_float, lit_val)
            value = table.select(expr.name('result'))['result'].execute().tolist()[0]
            print(f"  ✅ col {symbol} lit      → {expr} → {value}")
        except Exception as e:
            print(f"  ❌ col {symbol} lit      → {type(e).__name__}")
            failures += 1

        try:
            expr = op(raw_val, col_float)
            value = table.select(expr.name('result'))['result'].execute().tolist()[0]
            print(f"  ✅ {raw_val} {symbol} col      → {expr} → {value}")
        except Exception as e:
            print(f"  ❌ {raw_val} {symbol} col      → {type(e).__name__}")
            failures += 1

        try:
            expr = op(lit_val, col_float)
            value = table.select(expr.name('result'))['result'].execute().tolist()[0]
            print(f"  ✅ lit {symbol} col      → {expr} → {value}")
        except Exception as e:
            print(f"  ❌ lit {symbol} col      → {type(e).__name__}")
            failures += 1
        print()

    # Test 3: BooleanScalar logical
    print(f"\n{'='*60}")
    print("3. BOOLEAN LOGIC (BooleanScalar)")
    print(f"{'='*60}")
    print(f"Test data: x_bool = [True]")
    print()

    col_bool = ibis._['x_bool']
    lit_true = ibis.literal(True)
    lit_false = ibis.literal(False)

    print(f"Types: col={type(col_bool).__name__}, lit={type(lit_true).__name__}")
    print()

    bool_ops = [
        ('AND', '&', lambda a, b: a & b, lit_true, True),
        ('OR', '|', lambda a, b: a | b, lit_false, False),
    ]

    for name, symbol, op, lit_val, raw_val in bool_ops:
        print(f"{name} ({symbol}):")

        try:
            expr = op(col_bool, lit_val)
            value = table.select(expr.name('result'))['result'].execute().tolist()[0]
            print(f"  ✅ col {symbol} lit      → {expr} → {value}")
        except Exception as e:
            print(f"  ❌ col {symbol} lit      → {type(e).__name__}")
            failures += 1

        try:
            expr = op(raw_val, col_bool)
            value = table.select(expr.name('result'))['result'].execute().tolist()[0]
            print(f"  ✅ {raw_val} {symbol} col      → {expr} → {value}")
        except Exception as e:
            print(f"  ❌ {raw_val} {symbol} col      → {type(e).__name__}")
            failures += 1

        try:
            expr = op(lit_val, col_bool)
            value = table.select(expr.name('result'))['result'].execute().tolist()[0]
            print(f"  ✅ lit {symbol} col      → {expr} → {value}")
        except Exception as e:
            print(f"  ❌ lit {symbol} col      → {type(e).__name__}")
            failures += 1
        print()

    # Test 4: StringScalar concatenation
    print(f"\n{'='*60}")
    print("4. STRING OPERATIONS (StringScalar)")
    print(f"{'='*60}")
    print(f"Test data: x_str = ['hello']")
    print()

    col_str = ibis._['x_str']
    lit_str = ibis.literal(' world')

    print(f"Types: col={type(col_str).__name__}, lit={type(lit_str).__name__}")
    print()

    print("Concatenation (+):")

    try:
        expr = col_str + lit_str
        value = table.select(expr.name('result'))['result'].execute().tolist()[0]
        print(f"  ✅ col + lit      → {expr} → '{value}'")
    except Exception as e:
        print(f"  ❌ col + lit      → {type(e).__name__}")
        failures += 1

    try:
        expr = ' world' + col_str
        value = table.select(expr.name('result'))['result'].execute().tolist()[0]
        print(f"  ✅ ' world' + col      → {expr} → '{value}'")
    except Exception as e:
        print(f"  ❌ ' world' + col      → {type(e).__name__}")
        failures += 1

    try:
        expr = lit_str + col_str
        value = table.select(expr.name('result'))['result'].execute().tolist()[0]
        print(f"  ✅ lit + col      → {expr} → '{value}'")
    except Exception as e:
        print(f"  ❌ lit + col      → {type(e).__name__}")
        failures += 1
    print()

    return failures


def test_polars():
    """Test Polars operator behavior."""
    try:
        import polars as pl
    except ImportError:
        print("ERROR: polars not installed")
        return 0

    print("\n" + "=" * 60)
    print("POLARS EXPRESSIONS")
    print("=" * 60)

    # Create test data with multiple column types
    df = pl.DataFrame({
        'x_int': [10],
        'x_float': [10.5],
        'x_bool': [True],
        'x_str': ['hello']
    })

    failures = 0

    # Test 1: Integer arithmetic
    print(f"\n{'='*60}")
    print("1. INTEGER ARITHMETIC (Expr)")
    print(f"{'='*60}")
    print(f"Test data: x_int = [10]")
    print()

    col_int = pl.col('x_int')
    lit_int = pl.lit(5)
    lit_100 = pl.lit(100)

    print(f"Types: col={type(col_int).__name__}, lit={type(lit_int).__name__}")
    print()

    int_ops = [
        ('Addition', '+', lambda a, b: a + b, lit_int, 5),
        ('Subtraction', '-', lambda a, b: a - b, lit_100, 100),
        ('Multiplication', '*', lambda a, b: a * b, lit_int, 5),
        ('Division', '/', lambda a, b: a / b, lit_100, 100),
        ('Modulo', '%', lambda a, b: a % b, lit_100, 100),
        ('Power', '**', lambda a, b: a ** b, pl.lit(2), 2),
        ('Floor Division', '//', lambda a, b: a // b, lit_100, 100),
    ]

    for name, symbol, op, lit_val, raw_val in int_ops:
        print(f"{name} ({symbol}):")

        try:
            expr = op(col_int, lit_val)
            value = df.select(expr.alias('result'))['result'][0]
            print(f"  ✅ col {symbol} lit      → {expr} → {value}")
        except Exception as e:
            print(f"  ❌ col {symbol} lit      → {type(e).__name__}")
            failures += 1

        try:
            expr = op(raw_val, col_int)
            value = df.select(expr.alias('result'))['result'][0]
            print(f"  ✅ {raw_val} {symbol} col      → {expr} → {value}")
        except Exception as e:
            print(f"  ❌ {raw_val} {symbol} col      → {type(e).__name__}")
            failures += 1

        try:
            expr = op(lit_val, col_int)
            value = df.select(expr.alias('result'))['result'][0]
            print(f"  ✅ lit {symbol} col      → {expr} → {value}")
        except Exception as e:
            print(f"  ❌ lit {symbol} col      → {type(e).__name__}")
            failures += 1
        print()

    # Test 2: Float arithmetic
    print(f"\n{'='*60}")
    print("2. FLOAT ARITHMETIC (Expr)")
    print(f"{'='*60}")
    print(f"Test data: x_float = [10.5]")
    print()

    col_float = pl.col('x_float')
    lit_float = pl.lit(2.5)

    print(f"Types: col={type(col_float).__name__}, lit={type(lit_float).__name__}")
    print()

    float_ops = [
        ('Addition', '+', lambda a, b: a + b, lit_float, 2.5),
        ('Subtraction', '-', lambda a, b: a - b, pl.lit(20.0), 20.0),
        ('Multiplication', '*', lambda a, b: a * b, lit_float, 2.5),
    ]

    for name, symbol, op, lit_val, raw_val in float_ops:
        print(f"{name} ({symbol}):")

        try:
            expr = op(col_float, lit_val)
            value = df.select(expr.alias('result'))['result'][0]
            print(f"  ✅ col {symbol} lit      → {expr} → {value}")
        except Exception as e:
            print(f"  ❌ col {symbol} lit      → {type(e).__name__}")
            failures += 1

        try:
            expr = op(raw_val, col_float)
            value = df.select(expr.alias('result'))['result'][0]
            print(f"  ✅ {raw_val} {symbol} col      → {expr} → {value}")
        except Exception as e:
            print(f"  ❌ {raw_val} {symbol} col      → {type(e).__name__}")
            failures += 1

        try:
            expr = op(lit_val, col_float)
            value = df.select(expr.alias('result'))['result'][0]
            print(f"  ✅ lit {symbol} col      → {expr} → {value}")
        except Exception as e:
            print(f"  ❌ lit {symbol} col      → {type(e).__name__}")
            failures += 1
        print()

    # Test 3: Boolean logic
    print(f"\n{'='*60}")
    print("3. BOOLEAN LOGIC (Expr)")
    print(f"{'='*60}")
    print(f"Test data: x_bool = [True]")
    print()

    col_bool = pl.col('x_bool')
    lit_true = pl.lit(True)
    lit_false = pl.lit(False)

    print(f"Types: col={type(col_bool).__name__}, lit={type(lit_true).__name__}")
    print()

    bool_ops = [
        ('AND', '&', lambda a, b: a & b, lit_true, True),
        ('OR', '|', lambda a, b: a | b, lit_false, False),
    ]

    for name, symbol, op, lit_val, raw_val in bool_ops:
        print(f"{name} ({symbol}):")

        try:
            expr = op(col_bool, lit_val)
            value = df.select(expr.alias('result'))['result'][0]
            print(f"  ✅ col {symbol} lit      → {expr} → {value}")
        except Exception as e:
            print(f"  ❌ col {symbol} lit      → {type(e).__name__}")
            failures += 1

        try:
            expr = op(raw_val, col_bool)
            value = df.select(expr.alias('result'))['result'][0]
            print(f"  ✅ {raw_val} {symbol} col      → {expr} → {value}")
        except Exception as e:
            print(f"  ❌ {raw_val} {symbol} col      → {type(e).__name__}")
            failures += 1

        try:
            expr = op(lit_val, col_bool)
            value = df.select(expr.alias('result'))['result'][0]
            print(f"  ✅ lit {symbol} col      → {expr} → {value}")
        except Exception as e:
            print(f"  ❌ lit {symbol} col      → {type(e).__name__}")
            failures += 1
        print()

    # Test 4: String operations
    print(f"\n{'='*60}")
    print("4. STRING OPERATIONS (Expr)")
    print(f"{'='*60}")
    print(f"Test data: x_str = ['hello']")
    print()

    col_str = pl.col('x_str')
    lit_str = pl.lit(' world')

    print(f"Types: col={type(col_str).__name__}, lit={type(lit_str).__name__}")
    print()

    print("Concatenation (+):")

    try:
        expr = col_str + lit_str
        value = df.select(expr.alias('result'))['result'][0]
        print(f"  ✅ col + lit      → {expr} → '{value}'")
    except Exception as e:
        print(f"  ❌ col + lit      → {type(e).__name__}")
        failures += 1

    try:
        expr = ' world' + col_str
        value = df.select(expr.alias('result'))['result'][0]
        print(f"  ✅ ' world' + col      → {expr} → '{value}'")
    except Exception as e:
        print(f"  ❌ ' world' + col      → {type(e).__name__}")
        failures += 1

    try:
        expr = lit_str + col_str
        value = df.select(expr.alias('result'))['result'][0]
        print(f"  ✅ lit + col      → {expr} → '{value}'")
    except Exception as e:
        print(f"  ❌ lit + col      → {type(e).__name__}")
        failures += 1
    print()

    return failures


def main():
    """Run both tests."""
    print()
    ibis_failures = test_ibis()
    polars_failures = test_polars()

    # Calculate total tests: 7 int ops + 3 float ops + 2 bool ops + 1 string op = 13 ops
    # Each op has 3 tests (forward, reverse raw, reverse lit) = 39 total tests
    total_tests = 39

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"\nPolars failures: {polars_failures}/{total_tests} {'✅' if polars_failures == 0 else '❌'}")
    print(f"Ibis failures:   {ibis_failures}/{total_tests} {'✅' if ibis_failures == 0 else '❌'}")
    print()

    if ibis_failures > 0 and polars_failures == 0:
        print("Result:")
        print("  ✅ Polars: All forward and reverse operators work across all types")
        print("  ❌ Ibis:   Reverse operators fail when using ibis.literal()")
        print()
        print("Root cause:")
        print("  Polars Expr has reverse operators (__radd__, __rsub__, __rand__, etc.)")
        print("  Ibis scalar types (IntegerScalar, FloatingScalar, BooleanScalar, StringScalar)")
        print("  raise InputTypeError instead of returning NotImplemented")
        print()
        print("Affected types:")
        print("  IntegerScalar, FloatingScalar, BooleanScalar, StringScalar")
        print()
        print("Affected operators:")
        print("  Arithmetic: +, -, *, /, %, **, //")
        print("  Logical: &, |")
    print()


if __name__ == '__main__':
    main()
