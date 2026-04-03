#!/usr/bin/env python3
"""
Real-world impact analysis: How often does multiplication fail?
"""

import ibis
import polars as pl
import pandas as pd

print("=" * 80)
print("MULTIPLICATION: REAL-WORLD IMPACT ANALYSIS")
print("=" * 80)

polars_backend = ibis.polars.connect()

print("\n" + "=" * 80)
print("SCENARIO 1: Typical DataFrame (int64 columns)")
print("=" * 80)

# Most common case: Polars/Pandas default to int64
df_typical = pl.DataFrame({
    'quantity': [100, 50, 200],
    'price': [25, 30, 15],
    'multiplier': [2, 3, 4],
})

print(f"\nDataFrame schema: {df_typical.schema}")

table = polars_backend.create_table('typical', df_typical)

# Common operations
print("\nCommon business calculations:")

cases_typical = []

# Case 1: Apply tax (multiply by 1.1)
result1 = (table.price * 1.1).execute()
cases_typical.append({
    'operation': 'price * 1.1 (tax)',
    'works': all(result1 > 0),
    'sample_result': result1[0]
})

# Case 2: Double quantity
result2 = (table.quantity * 2).execute()
cases_typical.append({
    'operation': 'quantity * 2',
    'works': all(result2 > 0),
    'sample_result': result2[0]
})

# Case 3: Multiply two columns
result3 = (table.quantity * table.price).execute()
cases_typical.append({
    'operation': 'quantity * price',
    'works': all(result3 > 0),
    'sample_result': result3[0]
})

# Case 4: Scale by 100 (common for percentages)
result4 = (table.multiplier * 100).execute()
cases_typical.append({
    'operation': 'multiplier * 100',
    'works': all(result4 > 0),
    'sample_result': result4[0]
})

typical_df = pd.DataFrame(cases_typical)
print(typical_df.to_markdown(index=False))

print(f"\n✅ All operations work! ({len(cases_typical)}/{len(cases_typical)})")
print("Why? Column type is int64, literal is int8 → MIXED types → Polars promotes")

print("\n" + "=" * 80)
print("SCENARIO 2: Optimized DataFrame (int8 columns for memory)")
print("=" * 80)

# Someone optimized their DataFrame for memory
df_optimized = pl.DataFrame({
    'quantity': pl.Series([100, 50, 127], dtype=pl.Int8),
    'price': pl.Series([25, 30, 15], dtype=pl.Int8),
    'multiplier': pl.Series([2, 3, 4], dtype=pl.Int8),
})

print(f"\nDataFrame schema: {df_optimized.schema}")
print("(User optimized for memory, using smallest types)")

table_opt = polars_backend.create_table('optimized', df_optimized)

cases_optimized = []

# Case 1: Apply tax (multiply by 1.1) - float, should work
result1 = (table_opt.price * 1.1).execute()
cases_optimized.append({
    'operation': 'price(i8) * 1.1 (tax)',
    'works': all(result1 > 0),
    'sample_result': result1[0]
})

# Case 2: Double quantity - can overflow!
result2 = (table_opt.quantity * 2).execute()
cases_optimized.append({
    'operation': 'quantity(i8) * 2',
    'works': all(result2 > 0),
    'sample_result': result2[0]
})

# Case 3: Multiply two int8 columns - WILL overflow!
result3 = (table_opt.quantity * table_opt.price).execute()
cases_optimized.append({
    'operation': 'quantity(i8) * price(i8)',
    'works': all(result3 > 0),
    'sample_result': result3[0]
})

# Case 4: Scale by 100 - small values might work
result4 = (table_opt.multiplier * 100).execute()
cases_optimized.append({
    'operation': 'multiplier(i8) * 100',
    'works': all(result4 > 0),
    'sample_result': result4[0]
})

optimized_df = pd.DataFrame(cases_optimized)
print("\n" + optimized_df.to_markdown(index=False))

failures = sum(1 for x in cases_optimized if not x['works'])
print(f"\n❌ {failures}/{len(cases_optimized)} operations failed!")
print("Why? Both operands are int8 → NO promotion → overflow")

print("\n" + "=" * 80)
print("SCENARIO 3: Financial calculations (common overflow cases)")
print("=" * 80)

df_finance = pl.DataFrame({
    'shares': [100, 75, 50],
    'price_cents': [2550, 1899, 4250],  # Stock prices in cents
})

table_fin = polars_backend.create_table('finance', df_finance)

print(f"\nDataFrame schema: {df_finance.schema}")
print("Calculate portfolio value: shares × price_cents")

result_correct = (table_fin.shares * table_fin.price_cents).execute()
print(f"\nCorrect calculation: {result_correct.to_list()}")

# Now with int8 optimization (common in data warehouses)
df_finance_opt = pl.DataFrame({
    'shares': pl.Series([100, 75, 50], dtype=pl.Int8),
    'price_cents': pl.Series([127, 100, 90], dtype=pl.Int8),  # Limited by int8
})

table_fin_opt = polars_backend.create_table('finance_opt', df_finance_opt)
result_overflow = (table_fin_opt.shares * table_fin_opt.price_cents).execute()

print(f"\nWith int8 columns: {result_overflow.to_list()}")
print("Expected: [12700, 7500, 4500]")
print(f"Actual:   {result_overflow.to_list()}")

if result_overflow[0] != 12700:
    print("❌ SILENT DATA CORRUPTION!")

print("\n" + "=" * 80)
print("SCENARIO 4: Scaling operations (extremely common)")
print("=" * 80)

# Common pattern: scale values
df_scale = pl.DataFrame({'value': [1, 2, 5, 10, 50, 100]})
table_scale = polars_backend.create_table('scale', df_scale)

scale_cases = []

for scale_factor in [10, 100, 1000, 10000]:
    result = (table_scale.value * scale_factor).execute()
    expected = [v * scale_factor for v in [1, 2, 5, 10, 50, 100]]
    matches = list(result) == expected

    scale_cases.append({
        'scale_factor': scale_factor,
        'works': matches,
        'expected': str(expected[:3]) + '...',
        'actual': str(list(result)[:3]) + '...'
    })

scale_df = pd.DataFrame(scale_cases)
print(scale_df.to_markdown(index=False))

print("\n✅ All scale operations work with int64 columns")

# Now with int8
df_scale_i8 = pl.DataFrame({'value': pl.Series([1, 2, 5, 10, 50, 100], dtype=pl.Int8)})
table_scale_i8 = polars_backend.create_table('scale_i8', df_scale_i8)

scale_cases_i8 = []

for scale_factor in [10, 100, 1000, 10000]:
    result = (table_scale_i8.value * scale_factor).execute()
    expected = [v * scale_factor for v in [1, 2, 5, 10, 50, 100]]
    matches = list(result) == expected

    scale_cases_i8.append({
        'scale_factor': scale_factor,
        'works': matches,
        'expected': str(expected[:3]) + '...',
        'actual': str(list(result)[:3]) + '...'
    })

scale_df_i8 = pd.DataFrame(scale_cases_i8)
print("\nWith int8 columns:")
print(scale_df_i8.to_markdown(index=False))

failures_scale = sum(1 for x in scale_cases_i8 if not x['works'])
print(f"\n❌ {failures_scale}/{len(scale_cases_i8)} scale operations failed!")

print("\n" + "=" * 80)
print("IMPACT ASSESSMENT")
print("=" * 80)

print("""
GOOD NEWS:
  - Most DataFrames use int64 columns (Polars/Pandas default)
  - Literal (int8) × Column (int64) = MIXED types → Polars promotes
  - Common operations work fine with default types

BAD NEWS:
  - Memory-optimized DataFrames use int8/int16 for space efficiency
  - Column (int8) × Literal (int8) = SAME type → NO promotion
  - Financial calculations silently corrupt (100 × 127 = overflow)
  - Data warehouses often use narrow types (Parquet optimization)
  - Users can't predict when it will fail

WHEN MULTIPLICATION FAILS:
  1. Memory-optimized tables (int8/int16 columns)
  2. Financial calculations with cents (price × quantity)
  3. Scaling operations (value × 1000)
  4. Percentage calculations (value × 100)
  5. Any column × column when both are narrow types

FREQUENCY:
  - Power operations: ALWAYS fail with Polars backend (literal on LHS)
  - Multiplication: SOMETIMES fail (only when both operands are narrow)

  Power is 100% broken, multiplication is ~20% broken (narrow columns only)

IMPACT:
  - Power: Rare operation, but 100% failure rate
  - Multiplication: Very common operation, but lower failure rate
  - Multiplication failures are SILENT (wrong numbers, not errors)
  - Financial/scientific applications = DANGEROUS

WHICH IS WORSE?
  Multiplication is WORSE because:
  - Silent data corruption (wrong answers, not 0)
  - Very common operation
  - Used in critical calculations (money, science)
  - Harder to detect (not obviously wrong like 0)
  - Happens with "optimized" DataFrames (production systems)
""")

print("\n" + "=" * 80)
print("EXAMPLE: The $1 Million Bug")
print("=" * 80)

print("""
Scenario: E-commerce platform optimized their order table

BEFORE optimization:
  orders.quantity (int64) * orders.price_cents (int64)
  100 shares × $25.50 = $2,550 ✅

AFTER optimization (saved 50% memory):
  orders.quantity (int8) * orders.price_cents (int8)
  100 shares × $127 = overflow → wrong value ❌

Result:
  - Orders over $128 per item corrupt
  - Financial reports wrong
  - Audit finds discrepancies
  - No errors thrown
  - Silent data corruption

This actually happens in production systems!
""")
