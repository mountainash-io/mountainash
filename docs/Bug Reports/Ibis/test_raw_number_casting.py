#!/usr/bin/env python3
"""
Can you cast a raw Python number before Ibis wraps it in literal()?
"""

import ibis
import polars as pl

polars_backend = ibis.polars.connect()
pl_df = pl.DataFrame({'x': [10]})
table = polars_backend.create_table('test', pl_df)

print("=" * 80)
print("RAW NUMBER CASTING EXPERIMENT")
print("=" * 80)

print("\n1. Can you cast a raw Python number?")
print("-" * 80)

try:
    # This won't work - raw numbers don't have .cast()
    result = (2).cast('int64')
    print(f"  (2).cast('int64') → {result}")
except AttributeError as e:
    print(f"  (2).cast('int64') → AttributeError: {e}")

print("\n2. What about ibis.literal() first?")
print("-" * 80)

# You have to wrap in literal first
lit_2 = ibis.literal(2)
print(f"  ibis.literal(2).type() → {lit_2.type()}")

lit_2_i64 = ibis.literal(2).cast('int64')
print(f"  ibis.literal(2).cast('int64').type() → {lit_2_i64.type()}")

print("\n3. What happens with raw number in expression?")
print("-" * 80)

# When you write: 2 ** table.x
# Python calls: table.x.__rpow__(2)
# Ibis wraps: ibis.literal(2) ** table.x
# Result: Already inferred as int8 by the time it's an Ibis expression

expr_raw = 2 ** table.x
print(f"  Expression: 2 ** table.x")
print(f"  Operation: {expr_raw.op()}")
print(f"  Left operand: {expr_raw.op().left}")
print(f"  Left dtype: {expr_raw.op().left.dtype}")

print("\n4. Can you cast AFTER creating the expression?")
print("-" * 80)

# The expression result is float64, can't fix the int8 base
print(f"  (2 ** table.x).type() → {expr_raw.type()}")
print(f"  Result type is float64 - casting the result won't help!")

result_raw = (2 ** table.x).execute()[0]
print(f"  (2 ** table.x).execute()[0] → {result_raw}")

print("\n5. The ONLY way to fix raw numbers:")
print("-" * 80)

# You MUST wrap in literal and cast BEFORE the operation
fixed = ibis.literal(2).cast('int64') ** table.x
print(f"  ibis.literal(2).cast('int64') ** table.x")
result_fixed = fixed.execute()[0]
print(f"  Result: {result_fixed}")

# Or specify type upfront
fixed2 = ibis.literal(2, type='int64') ** table.x
print(f"\n  ibis.literal(2, type='int64') ** table.x")
result_fixed2 = fixed2.execute()[0]
print(f"  Result: {result_fixed2}")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)

print("""
Raw Python numbers (like 2, 10, 64) cannot be cast before Ibis wraps them.

The wrapping happens automatically via operator overloading:
  User writes:  2 ** table.x
  Python calls: table.x.__rpow__(2)  ← Raw number passed here
  Ibis wraps:   ibis.literal(2) ** table.x  ← Already int8!

By the time you have an Ibis expression, it's too late - the literal
has already been created with int8 dtype.

The ONLY workaround is to explicitly create the literal yourself:
  ✅ ibis.literal(2).cast('int64') ** table.x
  ✅ ibis.literal(2, type='int64') ** table.x
  ❌ 2 ** table.x  (no way to cast the 2 beforehand)

Users cannot use natural syntax (2 ** table.x) without hitting the bug.
The fix MUST be in Ibis.
""")
