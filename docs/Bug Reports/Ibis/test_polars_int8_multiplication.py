#!/usr/bin/env python3
"""
Test whether Polars promotes int8 * int8 to avoid overflow.
Based on user's power operation example.
"""

import polars as pl

df = pl.DataFrame({'x': [64], 'y': [64]})

# Expression definitions
lit_64 = pl.lit(64)

# Forced to Int8
lit_64_i8 = pl.lit(64, dtype=pl.Int8)
col_x_i8 = pl.col('x').cast(pl.Int8)
col_y_i8 = pl.col('y').cast(pl.Int8)

print("=" * 80)
print("POLARS MULTIPLICATION: Does int8 * int8 promote?")
print("=" * 80)
print(f"\nExpected result: 64 * 64 = 4096")
print(f"int8 range: -128 to 127")
print(f"4096 overflows int8!\n")

# Test multiplication cases
results = df.select(
    # Correct Cases (should be 4096)
    (lit_64 * pl.col('y')).alias("lit_64 * col_y"),
    (pl.col('x') * lit_64).alias("col_x * lit_64"),
    (pl.col('x') * pl.col('y')).alias("col_x * col_y"),

    # Int8 Cases (will it overflow?)
    (lit_64_i8 * pl.col('y')).alias("lit_64_i8 * col_y"),
    (pl.col('x') * lit_64_i8).alias("col_x * lit_64_i8"),
    (lit_64_i8 * col_y_i8).alias("lit_64_i8 * col_y_i8"),
    (col_x_i8 * lit_64_i8).alias("col_x_i8 * lit_64_i8"),
    (col_x_i8 * col_y_i8).alias("col_x_i8 * col_y_i8"),
).unpivot(variable_name="case", value_name="result")

print(results.to_pandas().to_markdown(index=False))

print("\n" + "=" * 80)
print("ANALYSIS")
print("=" * 80)

# Check which cases are correct
correct_results = results.filter(pl.col("result") == 4096)
overflow_results = results.filter(pl.col("result") != 4096)

print(f"\nCorrect results (4096): {correct_results.height}")
print(f"Overflow/Wrong results: {overflow_results.height}")

if overflow_results.height > 0:
    print("\nFailed cases:")
    for row in overflow_results.iter_rows(named=True):
        print(f"  {row['case']}: {row['result']}")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)

if overflow_results.height == 0:
    print("""
✅ Polars DOES promote types for multiplication!
All int8 * int8 cases returned 4096 (correct).
""")
else:
    print("""
❌ Polars DOES NOT promote types for multiplication!
int8 * int8 overflows when result exceeds int8 range.
""")

print("\n" + "=" * 80)
print("COMPARISON WITH POWER")
print("=" * 80)

# Now test power for comparison
power_results = df.select(
    # Correct Case
    (lit_64 ** pl.lit(2)).alias("lit_64 ** lit_2"),

    # Int8 Cases
    (lit_64_i8 ** pl.lit(2)).alias("lit_64_i8 ** lit_2"),
    (col_x_i8 ** pl.lit(2)).alias("col_x_i8 ** lit_2"),
).unpivot(variable_name="case", value_name="result")

print("\nPower operation results:")
print(power_results.to_pandas().to_markdown(index=False))

print("\n" + "=" * 80)
print("KEY INSIGHT")
print("=" * 80)
print("""
If multiplication promotes but power doesn't:
  - This explains why 64 * 64 works in Ibis tests
  - But 2 ** 10 fails in Ibis tests
  - Polars has different type promotion rules for different operators

If BOTH overflow:
  - The Ibis test showing 64 * 64 = 4096 must be using mixed types
  - Not pure int8 * int8
  - Need to check what Ibis actually sends to Polars
""")
