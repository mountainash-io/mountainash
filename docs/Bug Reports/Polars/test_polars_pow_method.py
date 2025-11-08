#!/usr/bin/env python3
"""Test Polars' .pow() method vs ** operator."""

import polars as pl

df = pl.DataFrame({'x': [10]})

print("Testing Polars Power Operations")
print("=" * 60)
print("Test data: x = [10]")
print()

# Test 1: ** operator with lit ** col
print("1. Using ** operator:")
expr1 = pl.lit(2) ** pl.col('x')
result1 = df.select(expr1.alias('r'))['r'][0]
print(f"   pl.lit(2) ** pl.col('x') = {result1} (expected 1024) {'✅' if result1 == 1024 else '❌'}")
print(f"   Expression: {expr1}")
print()

# Test 2: .pow() method with lit.pow(col)
print("2. Using .pow() method:")
expr2 = pl.lit(2).pow(pl.col('x'))
result2 = df.select(expr2.alias('r'))['r'][0]
print(f"   pl.lit(2).pow(pl.col('x')) = {result2} (expected 1024) {'✅' if result2 == 1024 else '❌'}")
print(f"   Expression: {expr2}")
print()

# Test 3: Reverse - col.pow(lit)
print("3. Reverse (col.pow(lit)):")
expr3 = pl.col('x').pow(pl.lit(2))
result3 = df.select(expr3.alias('r'))['r'][0]
print(f"   pl.col('x').pow(pl.lit(2)) = {result3} (expected 100) {'✅' if result3 == 100 else '❌'}")
print(f"   Expression: {expr3}")
print()

# Test 4: ** operator reverse - col ** lit
print("4. Using ** operator (reverse):")
expr4 = pl.col('x') ** pl.lit(2)
result4 = df.select(expr4.alias('r'))['r'][0]
print(f"   pl.col('x') ** pl.lit(2) = {result4} (expected 100) {'✅' if result4 == 100 else '❌'}")
print(f"   Expression: {expr4}")
print()

# Test 5: .pow() with raw integer
print("5. Using .pow() with raw int:")
expr5 = pl.lit(2).pow(10)
result5 = df.select(expr5.alias('r'))['r'][0]
print(f"   pl.lit(2).pow(10) = {result5} (expected 1024) {'✅' if result5 == 1024 else '❌'}")
print(f"   Expression: {expr5}")
print()

print("=" * 60)
print("Conclusion:")
if result1 == 1024 and result2 == 0:
    print("✅ ** operator works correctly")
    print("❌ .pow() method returns wrong result")
    print()
    print("ROOT CAUSE: Polars' .pow() method doesn't work with scalar.pow(column)")
    print("FIX: Ibis Polars backend should use ** operator instead of .pow() method")
elif result1 == 1024 and result2 == 1024:
    print("Both methods work - the issue is elsewhere")
else:
    print("Both methods fail - the issue is in Polars itself")
