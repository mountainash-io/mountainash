#!/usr/bin/env python3
"""Detailed investigation of power operator issue."""

import sys
sys.path.insert(0, '/home/nathanielramm/git/ibis')

import ibis
import polars as pl

# Create test data with clear value
conn = ibis.polars.connect()
df = pl.DataFrame({'x': [10]})
table = conn.create_table('test', df, overwrite=True)

col = ibis._['x']
lit_2 = ibis.literal(2)

print("Power Operator Detailed Investigation")
print("=" * 60)
print("Test data: x = [10]")
print()

# Test with different combinations
test_cases = [
    ("col ** lit (10 ** 2)", col ** lit_2, 100),
    ("lit ** col (2 ** 10)", lit_2 ** col, 1024),
    ("2 ** col (2 ** 10)", 2 ** col, 1024),
    ("col ** 2 (10 ** 2)", col ** 2, 100),
]

for name, expr, expected in test_cases:
    print(f"{name}:")
    print(f"  Expression: {expr}")
    print(f"  Repr: {repr(expr)}")

    # Execute
    try:
        result = table.select(expr.name('r'))['r'].execute().tolist()[0]
        status = "✅" if result == expected else "❌"
        print(f"  Result: {result} (expected {expected}) {status}")
    except Exception as e:
        print(f"  Error: {type(e).__name__}: {e}")
    print()

# Now let's look at what the ops.Power node looks like
print("Examining the operation nodes:")
print("=" * 60)
print()

# Forward: col ** lit
expr1 = col ** lit_2
print("1. col ** lit_2:")
print(f"   Expression: {expr1}")
if hasattr(expr1, 'op'):
    op = expr1.op()
    print(f"   Operation: {op}")
    print(f"   Left: {op.left}")
    print(f"   Right: {op.right}")
print()

# Reverse: lit ** col
expr2 = lit_2 ** col
print("2. lit_2 ** col:")
print(f"   Expression: {expr2}")
if hasattr(expr2, 'op'):
    op = expr2.op()
    print(f"   Operation: {op}")
    print(f"   Left: {op.left}")
    print(f"   Right: {op.right}")
print()

# Reverse: 2 ** col
expr3 = 2 ** col
print("3. 2 ** col:")
print(f"   Expression: {expr3}")
if hasattr(expr3, 'op'):
    op = expr3.op()
    print(f"   Operation: {op}")
    print(f"   Left: {op.left}")
    print(f"   Right: {op.right}")
print()

# Check what Polars does
print("Comparison with Polars:")
print("=" * 60)

polars_col = pl.col('x')
polars_lit = pl.lit(2)

test_cases_polars = [
    ("col ** lit (10 ** 2)", polars_col ** polars_lit, 100),
    ("lit ** col (2 ** 10)", polars_lit ** polars_col, 1024),
    ("2 ** col (2 ** 10)", 2 ** polars_col, 1024),
    ("col ** 2 (10 ** 2)", polars_col ** 2, 100),
]

for name, expr, expected in test_cases_polars:
    result = df.select(expr.alias('r'))['r'][0]
    status = "✅" if result == expected else "❌"
    print(f"{name}: {result} (expected {expected}) {status}")
