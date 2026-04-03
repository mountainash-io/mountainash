#!/usr/bin/env python3
"""
Minimal example showing the EXACT edge case:
- Int8 literal * Int64 column → Upcasts to Int64 ✅
- Int8 literal ** Int64 column → Stays Int8, returns 0 ❌

This demonstrates the CORRECT behavior that multiplication has but pow() lacks.
"""

import polars as pl

print("=" * 70)
print("THE EDGE CASE: Int8 Literal with Int64 Column")
print("=" * 70)

# Create DataFrame with Int64 column (default)
df = pl.DataFrame({'x': [63]})
print(f"\nDataFrame schema: {df.schema}")
print(f"Column 'x' dtype: {df.schema['x']}")

print("\n" + "-" * 70)
print("MULTIPLICATION: Automatic Upcast to Int64 ✅")
print("-" * 70)

# Int8 literal * Int64 column → Upcasts to Int64
result_mult = df.select((pl.lit(63, dtype=pl.Int8) * pl.col('x')).alias('r'))
print(f"\nInt8(63) * col_int64(63)")
print(f"  Schema:   {result_mult.schema}")
print(f"  Value:    {result_mult['r'][0]}")
print(f"  Expected: Int64: 3969")
print(f"  ✅ Correct! Upcasts to Int64" if result_mult['r'][0] == 3969 else f"  ❌ Failed!")

print("\n" + "-" * 70)
print("POWER: NO Upcast (BUG) ❌")
print("-" * 70)

# Int8 literal ** Int64 column → Stays Int8, overflows to 0
df_pow = pl.DataFrame({'x': [10]})
result_pow = df_pow.select((pl.lit(2, dtype=pl.Int8) ** pl.col('x')).alias('r'))
print(f"\nInt8(2) ** col_int64(10)")
print(f"  Schema:   {result_pow.schema}")
print(f"  Value:    {result_pow['r'][0]}")
print(f"  Expected: Int64: 1024")
print(f"  ❌ BUG: Stays Int8, returns 0" if result_pow['r'][0] == 0 else f"  ✅ Fixed!")

print("\n" + "=" * 70)
print("ROOT CAUSE")
print("=" * 70)
print("""
Both operations receive: (Int8 literal, Int64 column)

Multiplication (*, Operator::Multiply):
  File: polars-plan/src/plans/conversion/type_coercion/binary.rs
  Code: get_supertype(&type_left, &type_right)  // Line 242
        → get_supertype(Int8, Int64) = Int64
  Result: Int64 ✅

Power (**, PowFunction::Generic):
  File: polars-plan/src/plans/aexpr/function_expr/schema.rs
  Code: let out_dtype = if dtype1.is_integer() {   // Line 714-715
            if dtype2.is_float() { dtype2 } else { dtype1 }
        }
        → Returns dtype1 (Int8) without checking supertype
  Result: Int8 ❌

THE FIX:
Power should use get_supertype() like multiplication does!
""")

print("\n" + "=" * 70)
print("COMPARISON TABLE")
print("=" * 70)
print()
print("| Operands              | Operation | Result Dtype | Value | Status |")
print("|---------------------- |-----------|--------------|-------|--------|")
print(f"| Int8(63) * Int64(63)  | Multiply  | {str(result_mult.schema['r']):12} | {result_mult['r'][0]:5} | ✅     |")
print(f"| Int8(2) ** Int64(10)  | Power     | {str(result_pow.schema['r']):12} | {result_pow['r'][0]:5} | ❌     |")
print()
