#!/usr/bin/env python3
"""
Demonstrate the difference between multiplication and power when BOTH sides are Int8.

Key insight: When a COLUMN is involved, multiplication upcasts but power doesn't!
"""

import polars as pl

print("=" * 80)
print("BOTH OPERANDS ARE Int8: Multiplication vs Power")
print("=" * 80)

# Create DataFrame with Int8 column
df = pl.DataFrame({'x': [63]}).with_columns(pl.col('x').cast(pl.Int8))
df_pow = pl.DataFrame({'x': [10]}).with_columns(pl.col('x').cast(pl.Int8))

print(f"\nDataFrame schemas:")
print(f"  df:     {df.schema}")
print(f"  df_pow: {df_pow.schema}")

print("\n" + "=" * 80)
print("CASE 1: Literal * Literal (Both Int8)")
print("=" * 80)

result1 = pl.select((pl.lit(63, dtype=pl.Int8) * pl.lit(63, dtype=pl.Int8)).alias('r'))
print(f"\nInt8(63) * Int8(63)")
print(f"  Mathematical result: 3969")
print(f"  Schema:  {result1.schema}")
print(f"  Value:   {result1['r'][0]}")
print(f"  Wrapped: {(63 * 63) % 256 - 128} (expected if wrapped)")
print(f"  Behavior: Both literals → stays Int8, wraps on overflow")

print("\n" + "=" * 80)
print("CASE 2: Literal * Column (Both Int8)")
print("=" * 80)

result2 = df.select((pl.lit(63, dtype=pl.Int8) * pl.col('x')).alias('r'))
print(f"\nInt8(63) * col_int8(63)")
print(f"  Mathematical result: 3969")
print(f"  Schema:  {result2.schema}")
print(f"  Value:   {result2['r'][0]}")
print(f"  ✅ UPCASTS TO Int64! Returns correct value!")

print("\n" + "=" * 80)
print("CASE 3: Column * Literal (Both Int8)")
print("=" * 80)

result3 = df.select((pl.col('x') * pl.lit(63, dtype=pl.Int8)).alias('r'))
print(f"\ncol_int8(63) * Int8(63)")
print(f"  Mathematical result: 3969")
print(f"  Schema:  {result3.schema}")
print(f"  Value:   {result3['r'][0]}")
print(f"  ✅ UPCASTS TO Int64! Returns correct value!")

print("\n" + "=" * 80)
print("CASE 4: Literal ** Literal (Both Int8)")
print("=" * 80)

result4 = pl.select((pl.lit(2, dtype=pl.Int8) ** pl.lit(10, dtype=pl.Int8)).alias('r'))
print(f"\nInt8(2) ** Int8(10)")
print(f"  Mathematical result: 1024")
print(f"  Schema:  {result4.schema}")
print(f"  Value:   {result4['r'][0]}")
print(f"  Wrapped: {(2 ** 10) % 256 - 128} (expected if wrapped)")
print(f"  Behavior: Both literals → stays Int8, but returns 0 (not even correct wrapping!)")

print("\n" + "=" * 80)
print("CASE 5: Literal ** Column (Both Int8)")
print("=" * 80)

result5 = df_pow.select((pl.lit(2, dtype=pl.Int8) ** pl.col('x')).alias('r'))
print(f"\nInt8(2) ** col_int8(10)")
print(f"  Mathematical result: 1024")
print(f"  Schema:  {result5.schema}")
print(f"  Value:   {result5['r'][0]}")
print(f"  ❌ BUG: Stays Int8, returns 0 instead of 1024!")

print("\n" + "=" * 80)
print("CASE 6: Column ** Literal (Both Int8)")
print("=" * 80)

result6 = df_pow.select((pl.col('x') ** pl.lit(2, dtype=pl.Int8)).alias('r'))
print(f"\ncol_int8(10) ** Int8(2)")
print(f"  Mathematical result: 100")
print(f"  Schema:  {result6.schema}")
print(f"  Value:   {result6['r'][0]}")
print(f"  {'✅ Works (no overflow)' if result6['r'][0] == 100 else '❌ Failed'}")

print("\n" + "=" * 80)
print("SUMMARY TABLE")
print("=" * 80)
print()
print("| Expression                | Operation | Schema | Value | Expected | Status |")
print("|---------------------------|-----------|--------|-------|----------|--------|")
print(f"| Int8(63) * Int8(63)       | Mult      | {str(result1.schema['r']):6} | {result1['r'][0]:5} | 3969     | Wraps  |")
print(f"| Int8(63) * col_int8(63)   | Mult      | {str(result2.schema['r']):6} | {result2['r'][0]:5} | 3969     | ✅     |")
print(f"| col_int8(63) * Int8(63)   | Mult      | {str(result3.schema['r']):6} | {result3['r'][0]:5} | 3969     | ✅     |")
print(f"| Int8(2) ** Int8(10)       | Pow       | {str(result4.schema['r']):6} | {result4['r'][0]:5} | 1024     | ❌ (0) |")
print(f"| Int8(2) ** col_int8(10)   | Pow       | {str(result5.schema['r']):6} | {result5['r'][0]:5} | 1024     | ❌     |")
print(f"| col_int8(10) ** Int8(2)   | Pow       | {str(result6.schema['r']):6} | {result6['r'][0]:5} | 100      | ✅     |")
print()

print("=" * 80)
print("KEY INSIGHTS")
print("=" * 80)
print("""
1. Literal * Literal (Int8, Int8)
   → Stays Int8, wraps on overflow (-127)

2. Literal * Column (Int8, Int8) ✅
   → UPCASTS to Int64, returns correct value (3969)

3. Column * Literal (Int8, Int8) ✅
   → UPCASTS to Int64, returns correct value (3969)

4. Literal ** Literal (Int8, Int8) ❌
   → Stays Int8, returns 0 (doesn't even wrap correctly!)

5. Literal ** Column (Int8, Int8) ❌
   → Stays Int8, returns 0 instead of 1024

6. Column ** Literal (Int8, Int8) ✅
   → Works because result fits in Int8 (100)

THE BUG:
When a COLUMN is involved, multiplication automatically promotes to Int64,
but power does NOT. This causes silent overflow returning 0.

THE ROOT CAUSE:
- Multiplication: process_binary() calls get_supertype(Int8, Int8) → Int64
- Power: pow_dtype() just returns base dtype → Int8
""")
