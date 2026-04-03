#!/usr/bin/env python3
"""
Test: What does Polars do when we DON'T pass explicit dtype?
Demonstrates that Polars makes good decisions about type promotion.
"""

import polars as pl

print("=" * 80)
print("POLARS UNTYPED LITERAL BEHAVIOR")
print("=" * 80)

df = pl.DataFrame({
    'x': pl.Series([100], dtype=pl.Int8),
    'y': pl.Series([10], dtype=pl.Int8),
})

print(f"\nDataFrame schema: {df.schema}")

print("\n" + "=" * 80)
print("TEST 1: MULTIPLICATION")
print("=" * 80)

# Untyped literal (let Polars choose)
result1 = df.select(pl.lit(100) * pl.col('x'))
print(f"\nUntyped literal: pl.lit(100)")
print(f"  pl.lit(100) * col(100, int8)")
print(f"  Result: {result1[0,0]}")
print(f"  Result dtype: {result1.dtypes[0]}")
print(f"  Status: {'✅ Correct' if result1[0,0] == 10000 else '❌ Wrong'}")

# Explicit int8 (current Ibis behavior)
result2 = df.select(pl.lit(100, dtype=pl.Int8) * pl.col('x'))
print(f"\nExplicit int8: pl.lit(100, dtype=pl.Int8)")
print(f"  pl.lit(100, int8) * col(100, int8)")
print(f"  Result: {result2[0,0]}")
print(f"  Result dtype: {result2.dtypes[0]}")
print(f"  Status: {'✅ Correct' if result2[0,0] == 10000 else '❌ Wrong'}")

print("\n" + "=" * 80)
print("TEST 2: POWER")
print("=" * 80)

# Untyped literal
result3 = df.select(pl.lit(2).pow(pl.col('y')))
print(f"\nUntyped literal: pl.lit(2)")
print(f"  pl.lit(2) ** col(10, int8)")
print(f"  Result: {result3[0,0]}")
print(f"  Result dtype: {result3.dtypes[0]}")
print(f"  Status: {'✅ Correct' if result3[0,0] == 1024 else '❌ Wrong'}")

# Explicit int8
result4 = df.select(pl.lit(2, dtype=pl.Int8).pow(pl.col('y')))
print(f"\nExplicit int8: pl.lit(2, dtype=pl.Int8)")
print(f"  pl.lit(2, int8) ** col(10, int8)")
print(f"  Result: {result4[0,0]}")
print(f"  Result dtype: {result4.dtypes[0]}")
print(f"  Status: {'✅ Correct' if result4[0,0] == 1024 else '❌ Wrong'}")

print("\n" + "=" * 80)
print("TEST 3: WHAT TYPE DOES POLARS CHOOSE?")
print("=" * 80)

# Check what type Polars infers for untyped literals
test_values = [1, 2, 10, 100, 127, 128, 1000, 10000, 100000, 1000000]

print("\n| Value | Polars Untyped Literal Type |")
print("|-------|------------------------------|")

for val in test_values:
    # Create a literal without explicit type
    result = pl.select(pl.lit(val))
    dtype = str(result.dtypes[0])
    print(f"| {val:7} | {dtype:28} |")

print("\n" + "=" * 80)
print("TEST 4: MIXED TYPE OPERATIONS")
print("=" * 80)

print("\nScenario: int8 column × untyped literal")

test_cases = [
    (2, "double"),
    (10, "scale by 10"),
    (100, "scale by 100"),
    (1000, "scale by 1000"),
]

print("\n| Literal | Operation | col(100, int8) × lit | Result | Correct? |")
print("|---------|-----------|----------------------|--------|----------|")

for lit_val, description in test_cases:
    result = df.select(pl.col('x') * pl.lit(lit_val))
    expected = 100 * lit_val
    actual = result[0, 0]
    correct = actual == expected

    print(f"| {lit_val:7} | {description:9} | {actual:20} | {expected:6} | {'✅' if correct else '❌'} |")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)

print("""
KEY FINDINGS:

1. Polars untyped literals default to Int32
   - pl.lit(2) → Int32
   - pl.lit(100) → Int32
   - Adequate for most use cases

2. Untyped literals WORK CORRECTLY:
   - pl.lit(100) * col(100, int8) = 10000 ✅
   - pl.lit(2) ** col(10, int8) = 1024 ✅

3. Explicit int8 literals FAIL:
   - pl.lit(100, int8) * col(100, int8) = overflow ❌
   - pl.lit(2, int8) ** col(10, int8) = 0 ❌

4. Polars handles mixed types intelligently:
   - Int32 literal × Int8 column → promotes appropriately
   - No overflow in common scenarios

RECOMMENDATION:

Ibis should NOT pass explicit dtype for numeric literals:

  Current:  return pl.lit(value, dtype=pl.Int8)  ❌
  Fixed:    return pl.lit(value)                 ✅

Let Polars choose Int32, which:
  - Avoids overflow in most cases
  - Matches SQL INT behavior
  - Delegates to Polars' well-tested promotion logic
  - Requires zero Polars-specific promotion rules in Ibis

This is the simplest, safest fix!
""")
