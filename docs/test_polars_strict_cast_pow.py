#!/usr/bin/env python3
"""Test if strict_cast is causing the power issue."""

import polars as pl

df = pl.DataFrame({'x': [10]})

print("Testing Polars strict_cast with pow")
print("=" * 60)
print()

# Test 1: Without strict_cast
print("1. Without strict_cast:")
expr1 = pl.lit(2).pow(pl.col('x'))
result1 = df.select(expr1.alias('r'))['r'][0]
print(f"   pl.lit(2).pow(pl.col('x')) = {result1} (expected 1024) {'✅' if result1 == 1024 else '❌'}")
print(f"   Expression: {expr1}")
print()

# Test 2: With strict_cast
print("2. With strict_cast(Int8):")
expr2 = pl.lit(2).strict_cast(pl.Int8).pow(pl.col('x'))
result2 = df.select(expr2.alias('r'))['r'][0]
print(f"   pl.lit(2).strict_cast(Int8).pow(pl.col('x')) = {result2} (expected 1024) {'✅' if result2 == 1024 else '❌'}")
print(f"   Expression: {expr2}")
print()

# Test 3: Cast to Int64 instead
print("3. With strict_cast(Int64):")
expr3 = pl.lit(2).strict_cast(pl.Int64).pow(pl.col('x'))
result3 = df.select(expr3.alias('r'))['r'][0]
print(f"   pl.lit(2).strict_cast(Int64).pow(pl.col('x')) = {result3} (expected 1024) {'✅' if result3 == 1024 else '❌'}")
print(f"   Expression: {expr3}")
print()

# Test 4: Regular cast
print("4. With cast(Int8):")
expr4 = pl.lit(2).cast(pl.Int8).pow(pl.col('x'))
result4 = df.select(expr4.alias('r'))['r'][0]
print(f"   pl.lit(2).cast(Int8).pow(pl.col('x')) = {result4} (expected 1024) {'✅' if result4 == 1024 else '❌'}")
print(f"   Expression: {expr4}")
print()

# Test 5: Check what happens with Int8 overflow
print("5. Understanding the issue:")
print(f"   2^10 = 1024")
print(f"   Int8 range: -128 to 127")
print(f"   Int16 range: -32768 to 32767")
print(f"   Int64 range: -9223372036854775808 to 9223372036854775807")
print()
print("   Hypothesis: Int8 can't hold 1024, so it overflows to 0")
print()

# Test 6: Verify with smaller exponent
print("6. Test with smaller exponent (2^6 = 64, fits in Int8):")
df2 = pl.DataFrame({'x': [6]})
expr6 = pl.lit(2).strict_cast(pl.Int8).pow(pl.col('x'))
result6 = df2.select(expr6.alias('r'))['r'][0]
print(f"   pl.lit(2).strict_cast(Int8).pow(pl.col('x=6')) = {result6} (expected 64) {'✅' if result6 == 64 else '❌'}")
print()

# Test 7: Test with exponent that causes overflow
print("7. Test with exponent causing overflow (2^8 = 256, doesn't fit in Int8):")
df3 = pl.DataFrame({'x': [8]})
expr7 = pl.lit(2).strict_cast(pl.Int8).pow(pl.col('x'))
result7 = df3.select(expr7.alias('r'))['r'][0]
print(f"   pl.lit(2).strict_cast(Int8).pow(pl.col('x=8')) = {result7} (expected 256) {'✅' if result7 == 256 else '❌'}")
print()

print("=" * 60)
print("CONCLUSION:")
if result2 == 0 and result3 == 1024:
    print("✅ The issue is Int8 overflow!")
    print("   strict_cast(Int8) causes the result to overflow")
    print()
    print("FIX: Ibis should not cast integer literals to Int8 when")
    print("     used in power operations (or should use a wider type)")
elif result2 == 0:
    print("❌ strict_cast causes the issue (but not necessarily overflow)")
