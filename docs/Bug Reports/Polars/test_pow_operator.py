#!/usr/bin/env python3
"""Test the power operator specifically to understand its behavior."""

import sys
sys.path.insert(0, '/home/nathanielramm/git/ibis')

import ibis
import polars as pl

# Create test data
conn = ibis.polars.connect()
df = pl.DataFrame({'x': [10]})
table = conn.create_table('test', df, overwrite=True)

col = ibis._['x']
lit_2 = ibis.literal(2)

print("Testing Power Operator (**)")
print("=" * 60)
print()

# Test 1: Forward operator (col ** lit)
print("1. Forward: col ** lit")
try:
    expr = col ** lit_2
    print(f"   Expression: {expr}")
    print(f"   Type: {type(expr)}")
    result = table.select(expr.name('r'))['r'].execute().tolist()[0]
    print(f"   Result: {result}")
    print("   ✅ Works")
except Exception as e:
    print(f"   ❌ Failed: {type(e).__name__}: {e}")
print()

# Test 2: Reverse with raw value (2 ** col)
print("2. Reverse with raw value: 2 ** col")
try:
    expr = 2 ** col
    print(f"   Expression: {expr}")
    print(f"   Type: {type(expr)}")
    result = table.select(expr.name('r'))['r'].execute().tolist()[0]
    print(f"   Result: {result}")
    print("   ✅ Works")
except Exception as e:
    print(f"   ❌ Failed: {type(e).__name__}: {e}")
print()

# Test 3: Reverse with literal (lit ** col)
print("3. Reverse with literal: lit ** col")
try:
    expr = lit_2 ** col
    print(f"   Expression: {expr}")
    print(f"   Type: {type(expr)}")
    result = table.select(expr.name('r'))['r'].execute().tolist()[0]
    print(f"   Result: {result}")
    print("   ✅ Works")
except Exception as e:
    print(f"   ❌ Failed: {type(e).__name__}: {e}")
print()

# Test 4: Check if __rpow__ exists
print("4. Checking methods on IntegerScalar:")
print(f"   Has __pow__: {hasattr(lit_2, '__pow__')}")
print(f"   Has __rpow__: {hasattr(lit_2, '__rpow__')}")
print()

# Test 5: Manual call to __rpow__
print("5. Manual call to __rpow__:")
try:
    result = col.__rpow__(lit_2)
    print(f"   col.__rpow__(lit_2) → {result}")
    print("   ✅ Works")
except Exception as e:
    print(f"   ❌ Failed: {type(e).__name__}: {e}")
print()

# Test 6: Manual call to __pow__ with reverse order
print("6. Manual call to __pow__ on literal:")
try:
    result = lit_2.__pow__(col)
    print(f"   lit_2.__pow__(col) → {result}")
    print(f"   Type: {type(result)}")
    if result is NotImplemented:
        print("   Returns NotImplemented (good!)")
    else:
        print("   Returns an expression (also good!)")
except Exception as e:
    print(f"   ❌ Failed: {type(e).__name__}: {e}")
