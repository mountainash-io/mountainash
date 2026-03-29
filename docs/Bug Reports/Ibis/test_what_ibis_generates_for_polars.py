#!/usr/bin/env python3
"""
Test what Ibis actually generates for the Polars backend.
This is the key - what does Ibis's translator produce?
"""

import ibis
import polars as pl
from ibis.backends.polars.compiler import translate

print("=" * 80)
print("WHAT DOES IBIS GENERATE FOR POLARS BACKEND?")
print("=" * 80)

# Create table
df = pl.DataFrame({
    'x': pl.Series([100], dtype=pl.Int8),
    'y': pl.Series([10], dtype=pl.Int8),
})

polars_backend = ibis.polars.connect()
table = polars_backend.create_table('test', df)

print(f"\nTable schema: {table.schema()}")

print("\n" + "=" * 80)
print("TEST 1: WHAT POLARS EXPRESSION DOES IBIS GENERATE?")
print("=" * 80)

# Build Ibis expression
lit_100 = ibis.literal(100)
expr_mult = lit_100 * table.x

print(f"\nIbis expression: ibis.literal(100) * table.x")
print(f"Ibis literal type: {lit_100.type()}")

# Get the operation
print(f"\nOperation: {expr_mult.op()}")
print(f"Operation type: {type(expr_mult.op()).__name__}")

# Translate the literal to Polars
ibis_lit_op = lit_100.op()
polars_lit_expr = translate(ibis_lit_op)

print(f"\nWhat Ibis generates for literal(100):")
print(f"  Polars expression: {polars_lit_expr}")
print(f"  Type: {type(polars_lit_expr)}")

# Try to inspect the Polars expression
print(f"\nPolars expression details:")
print(f"  {polars_lit_expr}")

print("\n" + "=" * 80)
print("TEST 2: EXECUTE AND SEE RESULT")
print("=" * 80)

# Execute through Ibis
result = expr_mult.execute()
print(f"\nIbis result: {result[0]}")
print(f"Expected: 10000")
print(f"Status: {'❌ WRONG' if result[0] != 10000 else '✅ Correct'}")

print("\n" + "=" * 80)
print("TEST 3: COMPARE WITH PURE POLARS")
print("=" * 80)

# What does pure Polars do?
print("\nPure Polars (untyped literal):")
result_polars_untyped = df.select(pl.lit(100) * pl.col('x'))
print(f"  pl.lit(100) * pl.col('x'): {result_polars_untyped[0, 0]}")

print("\nPure Polars (int8 literal):")
result_polars_i8 = df.select(pl.lit(100, dtype=pl.Int8) * pl.col('x'))
print(f"  pl.lit(100, dtype=pl.Int8) * pl.col('x'): {result_polars_i8[0, 0]}")

print("\nPure Polars (int32 literal):")
result_polars_i32 = df.select(pl.lit(100, dtype=pl.Int32) * pl.col('x'))
print(f"  pl.lit(100, dtype=pl.Int32) * pl.col('x'): {result_polars_i32[0, 0]}")

print("\nPure Polars (int64 literal):")
result_polars_i64 = df.select(pl.lit(100, dtype=pl.Int64) * pl.col('x'))
print(f"  pl.lit(100, dtype=pl.Int64) * pl.col('x'): {result_polars_i64[0, 0]}")

print("\n" + "=" * 80)
print("TEST 4: POWER OPERATION")
print("=" * 80)

lit_2 = ibis.literal(2)
expr_pow = lit_2 ** table.y

print(f"\nIbis expression: ibis.literal(2) ** table.y")
print(f"Ibis literal type: {lit_2.type()}")

# Execute through Ibis
result_pow = expr_pow.execute()
print(f"\nIbis result: {result_pow[0]}")
print(f"Expected: 1024")
print(f"Status: {'❌ WRONG' if result_pow[0] == 0 else '✅ Correct'}")

# Compare with pure Polars
print("\nPure Polars (untyped literal):")
result_polars_pow_untyped = df.select(pl.lit(2).pow(pl.col('y')))
print(f"  pl.lit(2) ** pl.col('y'): {result_polars_pow_untyped[0, 0]}")

print("\nPure Polars (int8 literal):")
result_polars_pow_i8 = df.select(pl.lit(2, dtype=pl.Int8).pow(pl.col('y')))
print(f"  pl.lit(2, dtype=pl.Int8) ** pl.col('y'): {result_polars_pow_i8[0, 0]}")

print("\n" + "=" * 80)
print("TEST 5: INSPECT IBIS COMPILER OUTPUT")
print("=" * 80)

print("\nLet's see what the Ibis Polars compiler actually generates...")

# Get the full compiled expression
from ibis.backends.polars.compiler import translate

print("\nFor literal(100):")
lit_100_op = ibis.literal(100).op()
lit_100_polars = translate(lit_100_op)
print(f"  Ibis generates: {lit_100_polars}")

print("\nFor literal(2):")
lit_2_op = ibis.literal(2).op()
lit_2_polars = translate(lit_2_op)
print(f"  Ibis generates: {lit_2_polars}")

print("\nFor table.x:")
col_x_op = table.x.op()
col_x_polars = translate(col_x_op)
print(f"  Ibis generates: {col_x_polars}")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)

print("""
KEY QUESTIONS:

1. What type does Ibis pass to pl.lit()?
   - We saw Ibis infers int8 for literal(100)
   - But what does translate() actually generate?

2. Does "don't pass dtype" fix multiplication?
   - Pure Polars: Int32 literal works for power, NOT for mult
   - But what about through Ibis translation?

3. Is Ibis doing something else during translation?
   - Does it cast types?
   - Does it add promotion logic?

Need to inspect the actual Polars expressions Ibis generates!
""")
