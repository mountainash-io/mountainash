#!/usr/bin/env python3
"""
Test Polars overflow behavior across different operations.

Compares how Polars handles overflow in:
- Multiplication
- Addition
- Power operations
"""

import polars as pl

print("Polars Overflow Behavior Comparison")
print("=" * 70)
print()

df = pl.DataFrame({'x': [63]})

print("Testing operations that would overflow Int8 (range: -128 to 127)")
print("-" * 70)
print()

# Test 1: Multiplication (63 * 63 = 3969, overflows Int8)
print("1. MULTIPLICATION: Int8(63) * Int8(63)")
print("   Mathematical result: 3969 (overflows Int8)")
result1 = df.select((pl.lit(63, dtype=pl.Int8) * pl.lit(63, dtype=pl.Int8)).alias('r'))['r'][0]
print(f"   Polars result: {result1}")
print(f"   Status: {'✅ Works (wraps or upcasts)' if result1 != 0 else '❌ Returns 0'}")
print()

# Test 2: Addition (127 + 127 = 254, overflows Int8)
print("2. ADDITION: Int8(127) + Int8(127)")
print("   Mathematical result: 254 (overflows Int8)")
result2 = df.select((pl.lit(127, dtype=pl.Int8) + pl.lit(127, dtype=pl.Int8)).alias('r'))['r'][0]
print(f"   Polars result: {result2}")
print(f"   Status: {'✅ Works (wraps or upcasts)' if result2 != 0 else '❌ Returns 0'}")
print()

# Test 3: Multiplication with column (63 * col(63) = 3969)
print("3. MULTIPLICATION WITH COLUMN: Int8(63) * col(63)")
print("   Mathematical result: 3969 (overflows Int8)")
result3 = df.select((pl.lit(63, dtype=pl.Int8) * pl.col('x')).alias('r'))['r'][0]
print(f"   Polars result: {result3}")
print(f"   Status: {'✅ Works (wraps or upcasts)' if result3 != 0 else '❌ Returns 0'}")
print()

# Test 4: Power (2^10 = 1024, overflows Int8)
print("4. POWER: Int8(2) ** col(10)")
df2 = pl.DataFrame({'x': [10]})
print("   Mathematical result: 1024 (overflows Int8)")
result4 = df2.select((pl.lit(2, dtype=pl.Int8) ** pl.col('x')).alias('r'))['r'][0]
print(f"   Polars result: {result4}")
print(f"   Status: {'✅ Works (wraps or upcasts)' if result4 != 0 else '❌ Returns 0'}")
print()

# Test 5: Check the actual dtypes of results
print("=" * 70)
print("DTYPE ANALYSIS:")
print("-" * 70)

tests = [
    ("Int8(63) * Int8(63)", pl.lit(63, dtype=pl.Int8) * pl.lit(63, dtype=pl.Int8)),
    ("Int8(127) + Int8(127)", pl.lit(127, dtype=pl.Int8) + pl.lit(127, dtype=pl.Int8)),
    ("Int8(63) * col(63)", pl.lit(63, dtype=pl.Int8) * pl.col('x')),
    ("Int8(2) ** col(10)", pl.lit(2, dtype=pl.Int8) ** pl.col('x')),
]

for desc, expr in tests:
    try:
        result_df = df.select(expr.alias('r')) if 'col(10)' not in desc else df2.select(expr.alias('r'))
        dtype = str(result_df.schema['r'])
        value = result_df['r'][0]
        print(f"{desc:30} → dtype: {dtype:8} value: {value}")
    except Exception as e:
        print(f"{desc:30} → ERROR: {e}")

print()

# Test 6: Wrapping behavior
print("=" * 70)
print("WRAPPING vs UPCASTING:")
print("-" * 70)
print()

# Check if multiplication wraps around
mult_result = df.select((pl.lit(63, dtype=pl.Int8) * pl.lit(63, dtype=pl.Int8)).alias('r'))['r'][0]
expected_wrap = (63 * 63) % 256 - 128  # Two's complement wrapping for signed Int8
print(f"Int8(63) * Int8(63):")
print(f"  Result: {mult_result}")
print(f"  Expected if wrapped: {expected_wrap}")
print(f"  Expected if upcasted: 3969")
print(f"  Behavior: {'Wrapping' if mult_result == expected_wrap else 'Upcasting' if mult_result == 3969 else 'Unknown'}")
print()

# Check power
pow_result = df2.select((pl.lit(2, dtype=pl.Int8) ** pl.col('x')).alias('r'))['r'][0]
expected_wrap_pow = (2 ** 10) % 256 - 128
print(f"Int8(2) ** col(10):")
print(f"  Result: {pow_result}")
print(f"  Expected if wrapped: {expected_wrap_pow}")
print(f"  Expected if upcasted: 1024")
print(f"  Behavior: {'Wrapping' if pow_result == expected_wrap_pow else 'Upcasting' if pow_result == 1024 else 'Returns 0 (BUG)' if pow_result == 0 else 'Unknown'}")
print()

# Summary
print("=" * 70)
print("CONCLUSION:")
print("-" * 70)

if mult_result != 0 and pow_result == 0:
    print("✅ Multiplication handles overflow (wraps or upcasts)")
    print("❌ Power returns 0 on overflow")
    print()
    print("This IS a bug - power should handle overflow like multiplication does!")
elif mult_result == 0 and pow_result == 0:
    print("Both operations return 0 on overflow")
    print("This might be consistent behavior (though surprising)")
else:
    print("Overflow behavior varies - needs more investigation")
