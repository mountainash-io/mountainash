#!/usr/bin/env python3
"""
Test that Ibis aggressively downcasts literals to smallest possible type,
causing overflow issues with Polars backend.
"""

import ibis
import polars as pl

# Create test DataFrame
df = pl.DataFrame({'x': [63]})

# Connect to Polars backend with table
conn = ibis.polars.connect(tables={'test': df})
table = conn.table('test')

print("=" * 80)
print("IBIS LITERAL TYPE INFERENCE")
print("=" * 80)

# Test what dtype Ibis infers for different literals
literals = [2, 63, 127, 128, 255, 256, 1000, 10000, 100000]

print("\n| Value | Ibis Inferred Type | Can Fit In |")
print("|-------|-------------------|------------|")
for val in literals:
    lit = ibis.literal(val)
    dtype = lit.type()
    print(f"| {val:5} | {str(dtype):17} | {'Int8' if val <= 127 else 'Int16' if val <= 32767 else 'Int32'} |")

print("\n" + "=" * 80)
print("TEST 1: literal(63) * literal(63) with Polars Backend")
print("=" * 80)

# Test multiplication
lit_63 = ibis.literal(63)
print(f"\nibis.literal(63) type: {lit_63.type()}")

result_mult = (lit_63 * lit_63).execute()
print(f"\nResult of literal(63) * literal(63):")
print(f"  Value: {result_mult}")
print(f"  Expected: 3969")
print(f"  {'✅ Correct' if result_mult == 3969 else '❌ FAILED - Overflow!'}")

print("\n" + "=" * 80)
print("TEST 2: literal(2) ** literal(10) with Polars Backend")
print("=" * 80)

lit_2 = ibis.literal(2)
lit_10 = ibis.literal(10)
print(f"\nibis.literal(2) type: {lit_2.type()}")
print(f"ibis.literal(10) type: {lit_10.type()}")

result_pow_lits = (lit_2 ** lit_10).execute()
print(f"\nResult of literal(2) ** literal(10):")
print(f"  Value: {result_pow_lits}")
print(f"  Expected: 1024")
print(f"  {'✅ Correct' if result_pow_lits == 1024 else '❌ FAILED - Overflow!'}")

print("\n" + "=" * 80)
print("TEST 3: literal(2) ** column (with Polars Backend)")
print("=" * 80)

df_pow = pl.DataFrame({'x': [10]})
conn2 = ibis.polars.connect(tables={'test_pow': df_pow})
table_pow = conn2.table('test_pow')

result_pow_col = (ibis.literal(2) ** table_pow.x).execute()
print(f"\nResult of literal(2) ** column(10):")
print(f"  Value: {result_pow_col[0]}")
print(f"  Expected: 1024")
print(f"  {'✅ Correct' if result_pow_col[0] == 1024 else '❌ FAILED - Overflow!'}")

print("\n" + "=" * 80)
print("TEST 4: Direct Polars Comparison (No Ibis)")
print("=" * 80)

# What Polars does without dtype specified
print("\nPolars without explicit dtype (Polars chooses):")
result_polars = pl.select(pl.lit(63) * pl.lit(63))
print(f"  pl.lit(63) * pl.lit(63)")
print(f"  Schema: {result_polars.schema}")
print(f"  Value: {result_polars.item()}")

# What Polars does when Ibis specifies Int8
print("\nPolars with Ibis's explicit Int8 dtype:")
result_polars_int8 = pl.select(pl.lit(63, dtype=pl.Int8) * pl.lit(63, dtype=pl.Int8))
print(f"  pl.lit(63, dtype=Int8) * pl.lit(63, dtype=Int8)")
print(f"  Schema: {result_polars_int8.schema}")
print(f"  Value: {result_polars_int8.item()}")

print("\n" + "=" * 80)
print("ROOT CAUSE ANALYSIS")
print("=" * 80)
print("""
Polars' Behavior (by design):
  - When dtype is NOT specified: Polars chooses Int64 (safe)
  - When dtype IS specified as Int8: Polars stays Int8, wraps on overflow

Ibis' Behavior (the problem):
  - Infers literal(63) as Int8 (smallest type that fits)
  - Explicitly passes dtype=Int8 to Polars backend
  - This causes Polars to stay in Int8 and overflow

The Issue:
  Ibis is being TOO AGGRESSIVE with type inference!
  It should either:
    1. Not pass explicit dtypes to Polars (let Polars choose)
    2. Use wider types for literals that might be used in operations
    3. Upcast before operations that might overflow
""")

print("\n" + "=" * 80)
print("WHERE IN IBIS CODE?")
print("=" * 80)
print("""
Literal type inference:
  File: ibis/expr/operations/generic.py or ibis/expr/types.py

Polars backend translation:
  File: ibis/backends/polars/compiler.py:85-110
  Function: literal(op, **_)

The bug: Line ~54 (estimated):
  typ = PolarsType.from_ibis(dtype)
  return pl.lit(op.value, dtype=typ)  # ← Explicitly passes narrow dtype!

The fix: Don't pass dtype for integer literals:
  elif dtype.is_integer():
      return pl.lit(value)  # Let Polars choose appropriate type
""")
