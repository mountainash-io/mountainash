#!/usr/bin/env python3
"""
Investigate how Ibis infers types differently for literals vs columns.
"""

import ibis
import polars as pl
import pandas as pd

print("=" * 80)
print("IBIS TYPE INFERENCE: Literals vs Columns")
print("=" * 80)

# Test literal type inference
print("\n" + "=" * 80)
print("PART 1: LITERAL TYPE INFERENCE")
print("=" * 80)

test_values = [2, 10, 63, 127, 128, 255, 256, 1000, 10000, 100000, 1000000]

print("\n| Value | Ibis Literal Type | Fits in Int8? | Fits in Int16? | Fits in Int32? |")
print("|-------|-------------------|---------------|----------------|----------------|")

for val in test_values:
    lit = ibis.literal(val)
    dtype = str(lit.type())
    fits_int8 = -128 <= val <= 127
    fits_int16 = -32768 <= val <= 32767
    fits_int32 = -2147483648 <= val <= 2147483647

    print(f"| {val:7} | {dtype:17} | {str(fits_int8):13} | {str(fits_int16):14} | {str(fits_int32):14} |")

print("\n" + "=" * 80)
print("PART 2: COLUMN TYPE INFERENCE")
print("=" * 80)

# Create DataFrames with different column types
test_data = {
    'int8_col': [2],
    'int16_col': [1000],
    'int32_col': [100000],
    'int64_col': [10000000000],
}

# Create with Polars (which has explicit dtypes)
pl_df = pl.DataFrame({
    'int8_val': pl.Series([2], dtype=pl.Int8),
    'int16_val': pl.Series([1000], dtype=pl.Int16),
    'int32_val': pl.Series([100000], dtype=pl.Int32),
    'int64_val': pl.Series([10000000000], dtype=pl.Int64),
})

print("\nOriginal Polars DataFrame dtypes:")
print(pl_df.schema)

# Connect and register
polars_backend = ibis.polars.connect()
table = polars_backend.create_table('test', pl_df)

print("\nIbis table schema:")
print(table.schema())

print("\n" + "=" * 80)
print("PART 3: OPERATION TYPE RESOLUTION")
print("=" * 80)

# Test how operations between literals and columns are typed
print("\nLiteral-Column operations:")
print("| Expression | Literal Type | Column Type | Operation | Result |")
print("|------------|--------------|-------------|-----------|--------|")

# literal(2) * int8_col
lit_2 = ibis.literal(2)
expr1 = lit_2 * table.int8_val
result1 = expr1.execute()
print(f"| lit(2) * int8_col | {lit_2.type()} | {table.int8_val.type()} | multiply | {result1[0]} |")

# literal(2) ** int8_col
expr2 = lit_2 ** table.int8_val
result2 = expr2.execute()
print(f"| lit(2) ** int8_col | {lit_2.type()} | {table.int8_val.type()} | power | {result2[0]} |")

# literal(2) * int64_col
expr3 = lit_2 * table.int64_val
result3 = expr3.execute()
print(f"| lit(2) * int64_col | {lit_2.type()} | {table.int64_val.type()} | multiply | {result3[0]} |")

# literal(2) ** int64_col with smaller value
pl_df2 = pl.DataFrame({'x': pl.Series([10], dtype=pl.Int64)})
table2 = polars_backend.create_table('test2', pl_df2)
expr4 = lit_2 ** table2.x
result4 = expr4.execute()
print(f"| lit(2) ** int64_col | {lit_2.type()} | {table2.x.type()} | power | {result4[0]} |")

print("\n" + "=" * 80)
print("PART 4: COLUMN-COLUMN OPERATIONS")
print("=" * 80)

# Create DataFrame with two columns
pl_df3 = pl.DataFrame({
    'base': pl.Series([2], dtype=pl.Int8),
    'exp': pl.Series([10], dtype=pl.Int8),
})
table3 = polars_backend.create_table('test3', pl_df3)

print("\nColumn-column operations:")
print("| Expression | Left Type | Right Type | Operation | Result |")
print("|------------|-----------|------------|-----------|--------|")

expr5 = table3.base * table3.exp
result5 = expr5.execute()
print(f"| col(int8) * col(int8) | {table3.base.type()} | {table3.exp.type()} | multiply | {result5[0]} |")

expr6 = table3.base ** table3.exp
result6 = expr6.execute()
print(f"| col(int8) ** col(int8) | {table3.base.type()} | {table3.exp.type()} | power | {result6[0]} |")

print("\n" + "=" * 80)
print("PART 5: WHAT POLARS ACTUALLY RECEIVES")
print("=" * 80)

print("\nLet's trace what Ibis sends to Polars backend:")

# We need to inspect the compiler
from ibis.backends.polars.compiler import translate
import ibis.expr.operations as ops

# Create a literal operation
lit_op = ibis.literal(2).op()
print(f"\nLiteral(2) operation: {lit_op}")
print(f"  dtype: {lit_op.dtype}")
print(f"  value: {lit_op.value}")

# What does the compiler do with it?
print("\nWhat Ibis compiler does:")
print("  1. infer_integer(2) → int8")
print("  2. Create ops.Literal(value=2, dtype=int8)")
print("  3. Polars backend translate() called")
print("  4. Returns: pl.lit(2, dtype=pl.Int8)")

# Column operation
print(f"\nColumn reference: {table.int64_val.op()}")
print(f"  dtype: {table.int64_val.type()}")

print("\n" + "=" * 80)
print("PART 6: THE KEY DIFFERENCE")
print("=" * 80)

print("""
LITERALS:
  User writes: ibis.literal(2)
  Ibis infers: int8 (smallest type that fits)
  Polars receives: pl.lit(2, dtype=pl.Int8)
  Problem: Type is TOO NARROW

COLUMNS:
  User creates: DataFrame with int64 column
  Ibis reads: int64 (from DataFrame schema)
  Polars receives: pl.col('x') (already int64)
  Result: Type is PRESERVED

THE MISMATCH:
  literal(2) → int8  (aggressively downsized)
  column(2) → int64  (preserved from DataFrame)

When they interact:
  int8 * int64 → depends on operation
  int8 ** int64 → int8 (bug!)
""")

print("\n" + "=" * 80)
print("PART 7: WHY COLUMN TYPES ARE PRESERVED")
print("=" * 80)

# Create DataFrames with Python ints (no explicit type)
df_python = pl.DataFrame({'x': [2, 10, 100]})
print(f"\nPolars DataFrame from Python ints:")
print(f"Schema: {df_python.schema}")
print("  → Polars chooses Int64 by default for Python ints")

df_pandas = pd.DataFrame({'x': [2, 10, 100]})
print(f"\nPandas DataFrame from Python ints:")
print(f"dtypes: {df_pandas.dtypes.to_dict()}")
print("  → Pandas chooses int64 by default")

print("""
INSIGHT:
  When you create a DataFrame from Python ints, Polars/Pandas choose Int64.
  When you create a literal from Python int, Ibis chooses Int8!

  This asymmetry is the root cause!
""")

print("\n" + "=" * 80)
print("PART 8: DEMONSTRATION OF THE PROBLEM")
print("=" * 80)

# Same value, different paths
value = 2

# Path 1: As a literal
lit = ibis.literal(value)
print(f"\nPath 1 - Literal:")
print(f"  ibis.literal({value}) → {lit.type()}")

# Path 2: As a DataFrame column
df = pl.DataFrame({'x': [value]})
table_temp = polars_backend.create_table('temp', df)
col = table_temp.x
print(f"\nPath 2 - Column:")
print(f"  DataFrame with [{value}] → {col.type()}")

# Now use them in operations
print(f"\nOperations with value {value}:")

# Test power operations
lit_10 = ibis.literal(10)
result_lit = (lit ** lit_10).execute()  # lit(2) ** lit(10) = ?
result_col_df = table_temp.select((table_temp.x ** lit_10).name('result')).execute()
result_col_val = result_col_df['result'][0]

print(f"  literal({value}) ** literal(10) = {result_lit} ({'❌ WRONG' if result_lit == 0 else '✅'})")
print(f"  column({value}) ** literal(10) = {result_col_val} ({'✅' if result_col_val == 1024 else '❌'})")

print("""
CONCLUSION:
  Both work here because:
  - literal ** literal: Ibis constant-folds at compile time ✅
  - column ** literal: Column is Int64 (wide enough) ✅

  The bug appears in PART 3 above:
  - literal(2) ** col_int64(10) = 0 ❌ (Int8 explicit dtype sent to Polars)

  Key insight:
  - Literals inferred as Int8
  - Columns default to Int64
  - When sent to Polars with explicit Int8 → overflow!
""")
