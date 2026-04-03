#!/usr/bin/env python3
"""Inspect what Polars expressions Ibis is generating."""

import sys
sys.path.insert(0, '/home/nathanielramm/git/ibis')

import ibis
import polars as pl

# Monkey-patch the translate function to see what's being generated
from ibis.backends.polars import compiler

original_power = compiler.power

def debug_power(op, **kw):
    print(f"\n[DEBUG] Power operation:")
    print(f"  op.left: {op.left} (type: {type(op.left)})")
    print(f"  op.right: {op.right} (type: {type(op.right)})")

    left = compiler.translate(op.left, **kw)
    right = compiler.translate(op.right, **kw)

    print(f"  translated left: {left} (type: {type(left)})")
    print(f"  translated right: {right} (type: {type(right)})")

    result = left.pow(right)
    print(f"  result: {result}")

    return result

compiler.power = debug_power
compiler.translate.register(ibis.expr.operations.Power)(debug_power)

# Now run the test
print("Testing Ibis Power Operation Translation")
print("=" * 60)

conn = ibis.polars.connect()
df = pl.DataFrame({'x': [10]})
table = conn.create_table('test', df, overwrite=True)

col = ibis._['x']
lit_2 = ibis.literal(2)

print("\n1. Forward: col ** lit (10 ** 2)")
print("-" * 60)
expr1 = col ** lit_2
result1 = table.select(expr1.name('r'))['r'].execute().tolist()[0]
print(f"\nFinal result: {result1} (expected 100) {'✅' if result1 == 100 else '❌'}")

print("\n2. Reverse with literal: lit ** col (2 ** 10)")
print("-" * 60)
expr2 = lit_2 ** col
result2 = table.select(expr2.name('r'))['r'].execute().tolist()[0]
print(f"\nFinal result: {result2} (expected 1024) {'✅' if result2 == 1024 else '❌'}")

print("\n3. Reverse with raw: 2 ** col (2 ** 10)")
print("-" * 60)
expr3 = 2 ** col
result3 = table.select(expr3.name('r'))['r'].execute().tolist()[0]
print(f"\nFinal result: {result3} (expected 1024) {'✅' if result3 == 1024 else '❌'}")
