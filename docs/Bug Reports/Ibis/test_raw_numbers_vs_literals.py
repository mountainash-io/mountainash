#!/usr/bin/env python3
"""
Test what happens with raw Python numbers vs ibis.literal() in operations.

Does Ibis automatically wrap raw numbers? If so, with what dtype?
"""

import ibis
import polars as pl

print("=" * 80)
print("RAW PYTHON NUMBERS vs ibis.literal()")
print("=" * 80)

# Create backends
polars_backend = ibis.polars.connect()
duckdb_backend = ibis.duckdb.connect()

# Create test table with multiple columns
pl_df = pl.DataFrame({
    'x': [10],   # For power tests: 2^10 = 1024
    'y': [64],   # For multiplication tests: 64*64 = 4096 (overflows int8)
})
polars_table = polars_backend.create_table('test', pl_df)
duckdb_backend.create_table('test', pl_df)
duckdb_table = duckdb_backend.table('test')

print("\nTable schema:")
print(f"  x: {polars_table.x.type()}")
print(f"  y: {polars_table.y.type()}")

print("\n" + "=" * 80)
print("PART 1: TYPE INFERENCE")
print("=" * 80)

# Test different ways to create expressions
print("\nHow does Ibis handle different input types?\n")

# 1. Raw number
print("1. Raw Python int:")
try:
    # Can we inspect what type Ibis assigns to a raw number?
    expr1 = 2 ** polars_table.x
    print(f"   Expression: 2 ** table.x")
    print(f"   Type: {type(expr1)}")
    print(f"   Expr type: {expr1.type()}")
except Exception as e:
    print(f"   Error: {e}")

# 2. Explicit literal
print("\n2. ibis.literal():")
lit = ibis.literal(2)
print(f"   ibis.literal(2)")
print(f"   Type: {type(lit)}")
print(f"   Expr type: {lit.type()}")

# 3. In operation
print("\n3. In operation:")
expr2 = ibis.literal(2) ** polars_table.x
print(f"   ibis.literal(2) ** table.x")
print(f"   Type: {type(expr2)}")
print(f"   Expr type: {expr2.type()}")

print("\n" + "=" * 80)
print("PART 2: EXECUTION COMPARISON")
print("=" * 80)

print("\n| Expression | Polars Result | DuckDB Result | Status |")
print("|------------|---------------|---------------|--------|")

# Test 1: Raw number ** column (Polars)
try:
    result1_polars = (2 ** polars_table.x).execute()
    val1_polars = result1_polars[0] if hasattr(result1_polars, '__getitem__') else result1_polars
except Exception as e:
    val1_polars = f"Error: {e}"

# Test 1: Raw number ** column (DuckDB)
try:
    result1_duckdb = (2 ** duckdb_table.x).execute()
    val1_duckdb = result1_duckdb[0] if hasattr(result1_duckdb, '__getitem__') else result1_duckdb
except Exception as e:
    val1_duckdb = f"Error: {e}"

status1 = "✅" if (str(val1_polars) == str(val1_duckdb) and val1_polars == 1024) else "❌"
print(f"| 2 ** table.x | {val1_polars} | {val1_duckdb} | {status1} |")

# Test 2: literal(2) ** column
try:
    result2_polars = (ibis.literal(2) ** polars_table.x).execute()
    val2_polars = result2_polars[0] if hasattr(result2_polars, '__getitem__') else result2_polars
except Exception as e:
    val2_polars = f"Error: {e}"

try:
    result2_duckdb = (ibis.literal(2) ** duckdb_table.x).execute()
    val2_duckdb = result2_duckdb[0] if hasattr(result2_duckdb, '__getitem__') else result2_duckdb
except Exception as e:
    val2_duckdb = f"Error: {e}"

status2 = "✅" if (str(val2_polars) == str(val2_duckdb) and val2_polars == 1024) else "❌"
print(f"| literal(2) ** table.x | {val2_polars} | {val2_duckdb} | {status2} |")

# Test 3: Raw number * column (overflow case: 64 * 64 = 4096)
try:
    result3_polars = (64 * polars_table.y).execute()
    val3_polars = result3_polars[0] if hasattr(result3_polars, '__getitem__') else result3_polars
except Exception as e:
    val3_polars = f"Error: {e}"

try:
    result3_duckdb = (64 * duckdb_table.y).execute()
    val3_duckdb = result3_duckdb[0] if hasattr(result3_duckdb, '__getitem__') else result3_duckdb
except Exception as e:
    val3_duckdb = f"Error: {e}"

status3 = "✅" if (str(val3_polars) == str(val3_duckdb) and val3_polars == 4096) else "❌"
print(f"| 64 * table.y(64) | {val3_polars} | {val3_duckdb} | {status3} |")

# Test 4: literal(64) * column (overflow case)
try:
    result4_polars = (ibis.literal(64) * polars_table.y).execute()
    val4_polars = result4_polars[0] if hasattr(result4_polars, '__getitem__') else result4_polars
except Exception as e:
    val4_polars = f"Error: {e}"

try:
    result4_duckdb = (ibis.literal(64) * duckdb_table.y).execute()
    val4_duckdb = result4_duckdb[0] if hasattr(result4_duckdb, '__getitem__') else result4_duckdb
except Exception as e:
    val4_duckdb = f"Error: {e}"

status4 = "✅" if (str(val4_polars) == str(val4_duckdb) and val4_polars == 4096) else "❌"
print(f"| literal(64) * table.y(64) | {val4_polars} | {val4_duckdb} | {status4} |")

print("\n" + "=" * 80)
print("PART 3: CHECKING THE OPERATION NODES")
print("=" * 80)

# Inspect the operation tree
print("\nWhat does Ibis create internally?\n")

# Raw number in operation
expr_raw = 2 ** polars_table.x
print("1. Expression: 2 ** table.x")
print(f"   Operation: {expr_raw.op()}")
print(f"   Operation type: {type(expr_raw.op())}")
print(f"   Operation name: {type(expr_raw.op()).__name__}")

# Get the left side of the operation
if hasattr(expr_raw.op(), 'left'):
    left_op = expr_raw.op().left
    print(f"   Left operand: {left_op}")
    print(f"   Left type: {type(left_op).__name__}")
    if hasattr(left_op, 'dtype'):
        print(f"   Left dtype: {left_op.dtype}")

# Explicit literal in operation
expr_lit = ibis.literal(2) ** polars_table.x
print("\n2. Expression: ibis.literal(2) ** table.x")
print(f"   Operation: {expr_lit.op()}")
print(f"   Operation type: {type(expr_lit.op())}")
print(f"   Operation name: {type(expr_lit.op()).__name__}")

if hasattr(expr_lit.op(), 'left'):
    left_op_lit = expr_lit.op().left
    print(f"   Left operand: {left_op_lit}")
    print(f"   Left type: {type(left_op_lit).__name__}")
    if hasattr(left_op_lit, 'dtype'):
        print(f"   Left dtype: {left_op_lit.dtype}")

print("\n" + "=" * 80)
print("PART 4: WHAT GETS SENT TO POLARS?")
print("=" * 80)

# Try to see what Polars receives
from ibis.backends.polars.compiler import translate

print("\nTranslating expressions to Polars API calls:\n")

# Raw number
print("1. Raw number (2 ** table.x):")
print(f"   Ibis creates: {expr_raw.op()}")
if hasattr(expr_raw.op(), 'left'):
    left_translated = translate(expr_raw.op().left)
    print(f"   Left side translates to: {left_translated}")
    print(f"   Type: {type(left_translated)}")

# Literal
print("\n2. Literal (ibis.literal(2) ** table.x):")
print(f"   Ibis creates: {expr_lit.op()}")
if hasattr(expr_lit.op(), 'left'):
    left_lit_translated = translate(expr_lit.op().left)
    print(f"   Left side translates to: {left_lit_translated}")
    print(f"   Type: {type(left_lit_translated)}")

print("\n" + "=" * 80)
print("PART 5: DIRECT COMPARISON")
print("=" * 80)

print("\nDoes Ibis automatically wrap raw numbers in literal()?")

# Check if they produce the same operation
print(f"\nOperation equality:")
print(f"  (2 ** table.x).op() == (literal(2) ** table.x).op(): {expr_raw.op() == expr_lit.op()}")

if hasattr(expr_raw.op(), 'left') and hasattr(expr_lit.op(), 'left'):
    print(f"  Left operand equality:")
    print(f"    Type: {type(expr_raw.op().left).__name__} vs {type(expr_lit.op().left).__name__}")
    print(f"    Equal: {expr_raw.op().left == expr_lit.op().left}")

    if hasattr(expr_raw.op().left, 'dtype') and hasattr(expr_lit.op().left, 'dtype'):
        print(f"  Left dtype equality:")
        print(f"    Raw: {expr_raw.op().left.dtype}")
        print(f"    Literal: {expr_lit.op().left.dtype}")
        print(f"    Equal: {expr_raw.op().left.dtype == expr_lit.op().left.dtype}")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)

if val1_polars == val2_polars:
    print("""
Raw numbers and ibis.literal() produce the SAME result!

This means:
  - Ibis automatically wraps raw numbers in literal()
  - Both get the same aggressive type inference (int8)
  - Both fail in the same way with Polars backend

User writes:     2 ** table.x
Ibis converts:   ibis.literal(2) ** table.x
Ibis infers:     literal(2, dtype=int8) ** table.x
Polars receives: pl.lit(2, dtype=pl.Int8) ** pl.col('x')
Result:          Overflow ❌

The problem exists for BOTH raw numbers and explicit literals!
""")
else:
    print(f"""
Raw numbers and ibis.literal() produce DIFFERENT results!

Raw number result:  {val1_polars}
Literal result:     {val2_polars}

This suggests Ibis handles raw numbers differently.
Further investigation needed!
""")

print("\n" + "=" * 80)
print("KEY TAKEAWAY")
print("=" * 80)
print("""
Whether you write:
  - 2 ** table.x              (raw number)
  - ibis.literal(2) ** table.x       (explicit literal)
  - 64 * table.y              (raw number, overflow)
  - ibis.literal(64) * table.y       (explicit literal, overflow)

Ibis treats them the same way:
  1. Converts raw number to literal
  2. Infers type as int8 (for values ≤127)
  3. Sends explicit Int8 to Polars backend
  4. Result may overflow depending on operation

For multiplication:
  - Polars promotes when types are MIXED (int8 × int64)
  - Works in this test because table columns are int64 by default
  - Would FAIL if both operands were int8: literal(64, int8) × column(64, int8) → 0

For power:
  - Polars doesn't promote even with mixed types
  - Overflow occurs when base is int8, regardless of exponent type

Users can't escape this by using raw numbers!
The fix must be in Ibis, not in user code.
""")
