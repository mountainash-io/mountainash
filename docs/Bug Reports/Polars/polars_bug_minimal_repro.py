#!/usr/bin/env python3
"""
Minimal reproduction for Polars power operation overflow bug.

Demonstrates that pl.lit(value, dtype=Int8).pow(col) silently returns 0
when the result would overflow, instead of upcasting or raising an error.
"""

import polars as pl

print("Polars Power Operation Overflow Bug")
print("=" * 60)
print()

df = pl.DataFrame({'x': [10]})

print("Computing: 2 ** 10 = 1024")
print("-" * 60)
print()

# Case 1: With Int8 dtype - FAILS
print("Case 1: pl.lit(2, dtype=Int8).pow(col)")
result1 = df.select(pl.lit(2, dtype=pl.Int8).pow(pl.col('x')).alias('result'))
print(f"  Result: {result1['result'][0]}")
print(f"  Expected: 1024")
print(f"  Status: {'✅ PASS' if result1['result'][0] == 1024 else '❌ FAIL (returns 0)'}")
print()

# Case 2: Without dtype - WORKS
print("Case 2: pl.lit(2).pow(col) [no dtype]")
result2 = df.select(pl.lit(2).pow(pl.col('x')).alias('result'))
print(f"  Result: {result2['result'][0]}")
print(f"  Expected: 1024")
print(f"  Status: {'✅ PASS' if result2['result'][0] == 1024 else '❌ FAIL'}")
print()

# Case 3: Using ** operator with Int8 - ALSO FAILS
print("Case 3: pl.lit(2, dtype=Int8) ** col [operator with dtype]")
result3 = df.select((pl.lit(2, dtype=pl.Int8) ** pl.col('x')).alias('result'))
print(f"  Result: {result3['result'][0]}")
print(f"  Expected: 1024")
print(f"  Status: {'✅ PASS' if result3['result'][0] == 1024 else '❌ FAIL (also returns 0)'}")
print()

# Case 4: Using ** operator without dtype - WORKS
print("Case 4: pl.lit(2) ** col [operator without dtype]")
result4 = df.select((pl.lit(2) ** pl.col('x')).alias('result'))
print(f"  Result: {result4['result'][0]}")
print(f"  Expected: 1024")
print(f"  Status: {'✅ PASS' if result4['result'][0] == 1024 else '❌ FAIL'}")
print()

# Summary
print("=" * 60)
print("SUMMARY:")
print("  • With Int8 dtype: BOTH .pow() and ** return 0 (WRONG)")
print("  • Without dtype: BOTH .pow() and ** return 1024 (CORRECT)")
print()
print("COMPARISON WITH MULTIPLICATION:")
print("  • Int8(63) * col(63) → Int64: 3969 ✅ (auto-upcasts)")
print("  • Int8(2) ** col(10) → Int8: 0 ❌ (doesn't upcast)")
print()
print("ROOT CAUSE:")
print("  Power operations don't auto-upcast when column involved,")
print("  unlike multiplication which correctly upcasts to Int64")
print()
print("EXPECTED:")
print("  Power should auto-upcast like multiplication does")
print()

if result1['result'][0] == 0 and result3['result'][0] == 0:
    print("🐛 BUG CONFIRMED: Int8 power operations silently overflow")
    print("   (Affects BOTH .pow() method and ** operator)")
else:
    print("✅ Bug appears to be fixed!")
