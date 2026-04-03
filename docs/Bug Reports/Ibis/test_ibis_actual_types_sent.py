#!/usr/bin/env python3
"""
Verify what types Ibis actually sends to Polars for the 64*64 case.
"""

import ibis
import polars as pl
from ibis.backends.polars.compiler import translate

print("=" * 80)
print("WHAT TYPES DOES IBIS ACTUALLY SEND TO POLARS?")
print("=" * 80)

# Create test table (Polars defaults to Int64 for Python ints)
pl_df = pl.DataFrame({'y': [64]})
polars_backend = ibis.polars.connect()
table = polars_backend.create_table('test', pl_df)

print("\n1. TABLE COLUMN TYPE:")
print(f"   table.y.type() = {table.y.type()}")

print("\n2. LITERAL TYPE:")
lit_64 = ibis.literal(64)
print(f"   ibis.literal(64).type() = {lit_64.type()}")

print("\n3. WHAT POLARS RECEIVES:")

# Case 1: 64 * table.y (raw number)
expr1 = 64 * table.y
print(f"\n   Expression: 64 * table.y")
print(f"   Operation: {expr1.op()}")

# Get the left operand (the literal)
left_op = expr1.op().left
print(f"   Left operand dtype: {left_op.dtype}")

# Translate to Polars
left_polars = translate(left_op)
print(f"   Left translates to: {left_polars}")

# Get the right operand (the column)
right_op = expr1.op().right
print(f"   Right operand dtype: {right_op.dtype}")
right_polars = translate(right_op)
print(f"   Right translates to: {right_polars}")

# Case 2: literal(64) * table.y
expr2 = ibis.literal(64) * table.y
print(f"\n   Expression: ibis.literal(64) * table.y")
left_op2 = expr2.op().left
print(f"   Left operand dtype: {left_op2.dtype}")
left_polars2 = translate(left_op2)
print(f"   Left translates to: {left_polars2}")

print("\n" + "=" * 80)
print("EXECUTE AND VERIFY")
print("=" * 80)

result1 = (64 * table.y).execute()
result2 = (ibis.literal(64) * table.y).execute()

print(f"\n64 * table.y = {result1[0]}")
print(f"ibis.literal(64) * table.y = {result2[0]}")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)

print(f"""
Table column type: {table.y.type()}
Literal type: {lit_64.type()}

This is a MIXED TYPE operation:
  - Literal: int8
  - Column: int64
  - Result: Polars promotes to avoid overflow

That's why 64 * 64 = 4096 works!

But if BOTH were int8, it would overflow and return 0.
""")

# Now test what happens if we force the column to int8
print("\n" + "=" * 80)
print("WHAT IF WE FORCE THE COLUMN TO INT8?")
print("=" * 80)

pl_df_i8 = pl.DataFrame({'y': pl.Series([64], dtype=pl.Int8)})
table_i8 = polars_backend.create_table('test_i8', pl_df_i8)

print(f"\nForced column type: {table_i8.y.type()}")

result3 = (ibis.literal(64) * table_i8.y).execute()
print(f"ibis.literal(64) * table_i8.y = {result3[0]}")

if result3[0] == 0:
    print("\n❌ OVERFLOW! When both are int8, multiplication fails!")
else:
    print(f"\n✅ Result: {result3[0]} (Polars still promotes)")
