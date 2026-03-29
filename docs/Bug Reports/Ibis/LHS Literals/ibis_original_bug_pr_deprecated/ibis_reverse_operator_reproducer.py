#!/usr/bin/env python3
"""
Ibis Reverse Operator Bug Reproducer

This script demonstrates the bug where arithmetic operations with Deferred
column references fail when the literal is on the left side of the operator.

Usage:
    python ibis_reverse_operator_reproducer.py

Expected output:
    - Forward operators (col + lit) should work ✅
    - Reverse operators (lit + col) should fail ❌
"""

import sys


def test_operator_symmetry():
    """Test all arithmetic operators with Deferred and literals."""
    try:
        import ibis
    except ImportError:
        print("ERROR: ibis not installed")
        print("Install with: pip install 'ibis-framework[polars]'")
        sys.exit(1)

    print("=" * 70)
    print("IBIS REVERSE OPERATOR BUG REPRODUCER")
    print("=" * 70)
    print(f"\nIbis version: {ibis.__version__}")
    print(f"Python version: {sys.version.split()[0]}")
    print()

    # Create test objects
    col = ibis._['x']
    lit = ibis.literal(5)

    print("Test objects:")
    print(f"  col = ibis._['x']           -> {type(col).__name__}")
    print(f"  lit = ibis.literal(5)       -> {type(lit).__name__}")
    print()

    print("IMPORTANT CLARIFICATION:")
    print("-" * 70)
    print("This bug is specific to ibis.literal() wrapped values.")
    print()
    print("Raw Python values work:")
    print("  5 + ibis._['x']           ✅ Works (Deferred has __radd__)")
    print()
    print("Wrapped literals fail:")
    print("  ibis.literal(5) + ibis._['x']  ❌ Fails (IntegerScalar lacks __radd__)")
    print()
    print("Expression builders need ibis.literal() for type safety,")
    print("so this bug affects programmatic expression generation!")
    print("-" * 70)
    print()

    # Test each operator
    operators = [
        ('Addition', '+', lambda a, b: a + b, '5 + 10'),
        ('Subtraction', '-', lambda a, b: a - b, '100 - 10'),
        ('Multiplication', '*', lambda a, b: a * b, '3 * 10'),
        ('Division', '/', lambda a, b: a / b, '100 / 10'),
        ('Modulo', '%', lambda a, b: a % b, '100 % 7'),
        ('Power', '**', lambda a, b: a ** b, '2 ** 3'),
        ('Floor Division', '//', lambda a, b: a // b, '100 // 7'),
    ]

    results = []

    for name, symbol, op_func, example in operators:
        print(f"{name} ({symbol})")
        print(f"  Example: {example}")

        # Test forward direction (col op lit)
        print(f"  Forward (col {symbol} lit): ", end="")
        try:
            result = op_func(col, lit)
            print(f"✅ Works - {result}")
            forward_works = True
        except Exception as e:
            print(f"❌ FAILS - {type(e).__name__}: {e}")
            forward_works = False

        # Test reverse with raw Python value (should work)
        print(f"  Reverse (raw_int {symbol} col): ", end="")
        raw_val = 5 if symbol in ['+', '*'] else 100
        try:
            if symbol == '+':
                result = raw_val + col
            elif symbol == '-':
                result = raw_val - col
            elif symbol == '*':
                result = raw_val * col
            elif symbol == '/':
                result = raw_val / col
            elif symbol == '%':
                result = raw_val % col
            elif symbol == '**':
                result = 2 ** col
            elif symbol == '//':
                result = raw_val // col
            print(f"✅ Works - {result}")
            reverse_raw_works = True
        except Exception as e:
            print(f"❌ FAILS - {type(e).__name__}")
            reverse_raw_works = False

        # Test reverse with ibis.literal (should fail)
        print(f"  Reverse (literal {symbol} col): ", end="")
        try:
            result = op_func(lit, col)
            print(f"✅ Works - {result}")
            reverse_lit_works = True
        except Exception as e:
            print(f"❌ FAILS - {type(e).__name__}")
            reverse_lit_works = False

        print()
        results.append({
            'name': name,
            'symbol': symbol,
            'forward': forward_works,
            'reverse_raw': reverse_raw_works,
            'reverse_lit': reverse_lit_works,
        })

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()

    forward_count = sum(1 for r in results if r['forward'])
    reverse_raw_count = sum(1 for r in results if r['reverse_raw'])
    reverse_lit_count = sum(1 for r in results if r['reverse_lit'])

    print(f"Forward operators (col op lit):      {forward_count}/{len(results)}")
    print(f"Reverse with raw int (int op col):   {reverse_raw_count}/{len(results)}")
    print(f"Reverse with literal (lit op col):   {reverse_lit_count}/{len(results)}")
    print()

    if reverse_raw_count == len(results) and reverse_lit_count < len(results):
        print("❌ BUG CONFIRMED: Reverse operators broken for ibis.literal()!")
        print()
        print("✅ Raw Python values work (Deferred has __radd__, etc.)")
        print("❌ ibis.literal() values fail (IntegerScalar lacks __radd__, etc.)")
        print()
        print("Failed operators with ibis.literal():")
        for r in results:
            if not r['reverse_lit']:
                print(f"  - {r['name']} ({r['symbol']})")
        print()
        print("Root cause:")
        print("  NumericValue class in ibis/expr/types/numeric.py")
        print("  lacks reverse operators (__radd__, __rsub__, etc.)")
        print()
        print("Why this matters:")
        print("  Expression builders MUST use ibis.literal() for type safety.")
        print("  Raw Python values don't provide proper type inference.")
        print()
        print("Expected behavior:")
        print("  Both should work:")
        print("    5 + ibis._['col']              (raw int - works)")
        print("    ibis.literal(5) + ibis._['col']  (wrapped - should work)")
        print()
    elif reverse_lit_count == len(results):
        print("✅ All operators working correctly!")
        print()
        print("Either the bug has been fixed, or you're testing after the fix.")
        print()
    else:
        print("⚠️  Unexpected results - some operators have unusual failures")
        print()

    return reverse_lit_count == len(results)


def test_with_real_data():
    """Test reverse operators with actual table data."""
    print("=" * 70)
    print("TESTING WITH REAL DATA")
    print("=" * 70)
    print()

    try:
        import ibis
        import polars as pl
    except ImportError as e:
        print(f"Skipping real data test: {e}")
        return True

    try:
        # Create test table
        conn = ibis.polars.connect()
        df = pl.DataFrame({'x': [1, 2, 3, 4, 5]})
        table = conn.create_table('test_table', df, overwrite=True)

        print("Test table created:")
        print(f"  {df}")
        print()

        # Test forward operation
        print("Testing forward operation: col('x') + literal(10)")
        expr_forward = ibis._['x'] + ibis.literal(10)
        result_forward = table.select(expr_forward.name('result'))
        values_forward = result_forward['result'].execute().tolist()
        print(f"  Result: {values_forward}")
        print(f"  Status: ✅ Works")
        print()

        # Test reverse operation
        print("Testing reverse operation: literal(10) + col('x')")
        try:
            expr_reverse = ibis.literal(10) + ibis._['x']
            result_reverse = table.select(expr_reverse.name('result'))
            values_reverse = result_reverse['result'].execute().tolist()
            print(f"  Result: {values_reverse}")
            print(f"  Status: ✅ Works")
            print()

            # Verify results match
            if values_forward == values_reverse:
                print("✅ Results match - operators are commutative!")
            else:
                print("⚠️  Results differ - unexpected!")
            print()
            return True

        except Exception as e:
            print(f"  Status: ❌ FAILS")
            print(f"  Error: {type(e).__name__}: {e}")
            print()
            print("❌ BUG CONFIRMED with real data!")
            print()
            return False

    except Exception as e:
        print(f"Error in real data test: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_fix_preview():
    """Show what the fix looks like."""
    print("=" * 70)
    print("PROPOSED FIX")
    print("=" * 70)
    print()
    print("File: ibis/expr/types/numeric.py")
    print()
    print("Add to NumericValue class:")
    print()
    print("```python")
    print("from ibis.common.deferred import Deferred")
    print()
    print("class NumericValue(Value):")
    print("    # ... existing methods ...")
    print()
    print("    def __radd__(self, other):")
    print("        if isinstance(other, Deferred):")
    print("            return other.__add__(self)")
    print("        return _binop(ops.Add, other, self)")
    print()
    print("    # Similar for __rsub__, __rmul__, __rtruediv__,")
    print("    # __rmod__, __rpow__, __rfloordiv__")
    print("```")
    print()
    print("This allows Python to properly handle:")
    print("  literal(5) + ibis._['x']")
    print()
    print("By delegating to:")
    print("  ibis._['x'].__add__(literal(5))")
    print()


def main():
    """Run all tests."""
    print()

    # Test operator symmetry
    operators_ok = test_operator_symmetry()

    # Test with real data
    real_data_ok = test_with_real_data()

    # Show fix
    if not operators_ok or not real_data_ok:
        show_fix_preview()

    print("=" * 70)
    print("END OF REPRODUCER")
    print("=" * 70)
    print()

    if operators_ok and real_data_ok:
        print("✅ No bugs found - operators working correctly!")
        print()
        print("Either:")
        print("  1. The bug has been fixed in this version of Ibis")
        print("  2. You're testing after applying the fix")
        sys.exit(0)
    else:
        print("❌ Bug confirmed and reproduced!")
        print()
        print("Next steps:")
        print("  1. File issue at: https://github.com/ibis-project/ibis/issues/new")
        print("  2. Include this reproducer output")
        print("  3. Reference the proposed fix above")
        print("  4. Submit PR with fix and tests")
        print()
        print("See IBIS_REVERSE_OPERATOR_BUG_FIX.md for full details.")
        sys.exit(1)


if __name__ == '__main__':
    main()
