#!/usr/bin/env python3
"""Check what dtype Ibis assigns to integer literals."""

import sys
sys.path.insert(0, '/home/nathanielramm/git/ibis')

import ibis
import polars as pl

print("Ibis Literal Dtype Investigation")
print("=" * 60)
print()

# Check different literal values
literals = [
    (2, "Small integer"),
    (127, "Max Int8"),
    (128, "Min value that needs Int16"),
    (1024, "Pow result"),
    (32767, "Max Int16"),
    (32768, "Min value that needs Int32"),
]

print("1. Ibis literal dtypes:")
for value, desc in literals:
    lit = ibis.literal(value)
    print(f"   ibis.literal({value:5}) → {lit.type()} ({desc})")
print()

# Test power with different literal types
print("2. Testing power with different sized literals:")
print("-" * 60)

conn = ibis.polars.connect()
df = pl.DataFrame({'x': [10]})
table = conn.create_table('test', df, overwrite=True)
col = ibis._['x']

test_cases = [
    (ibis.literal(2), "int8"),
    (ibis.literal(128), "int16"),
    (ibis.literal(32768), "int32"),
    (ibis.literal(2).cast('int16'), "int16 (cast)"),
    (ibis.literal(2).cast('int32'), "int32 (cast)"),
    (ibis.literal(2).cast('int64'), "int64 (cast)"),
]

for lit, desc in test_cases:
    try:
        expr = lit ** col
        result = table.select(expr.name('r'))['r'].execute().tolist()[0]
        status = "✅" if result == 1024 else f"❌ (got {result})"
        print(f"   {desc:15} ** col = {result:6} (expected 1024) {status}")
    except Exception as e:
        print(f"   {desc:15} ** col = ERROR: {type(e).__name__}")
print()

# Test if it's an Int8 overflow issue
print("3. Testing with Polars directly (Int8 literal):")
print("-" * 60)

# Direct Polars test with Int8 dtype
expr_int8 = pl.lit(2, dtype=pl.Int8).pow(pl.col('x'))
result_int8 = df.select(expr_int8.alias('r'))['r'][0]
print(f"   pl.lit(2, dtype=Int8).pow(col) = {result_int8} (expected 1024) {'✅' if result_int8 == 1024 else '❌'}")

# Direct Polars test without dtype
expr_default = pl.lit(2).pow(pl.col('x'))
result_default = df.select(expr_default.alias('r'))['r'][0]
print(f"   pl.lit(2).pow(col) = {result_default} (expected 1024) {'✅' if result_default == 1024 else '❌'}")

# Direct Polars test with Int64 dtype
expr_int64 = pl.lit(2, dtype=pl.Int64).pow(pl.col('x'))
result_int64 = df.select(expr_int64.alias('r'))['r'][0]
print(f"   pl.lit(2, dtype=Int64).pow(col) = {result_int64} (expected 1024) {'✅' if result_int64 == 1024 else '❌'}")

print()
print("=" * 60)
print("ANALYSIS:")
print("Int8 range: -128 to 127")
print("2^10 = 1024 (does not fit in Int8!)")
print()
if result_int8 == 0:
    print("✅ CONFIRMED: Int8 overflow causes the power operation to return 0")
    print()
    print("ROOT CAUSE:")
    print("  - Ibis infers ibis.literal(2) as Int8")
    print("  - Polars backend passes dtype=Int8 to pl.lit()")
    print("  - When computing 2^10, result (1024) doesn't fit in Int8")
    print("  - Polars returns 0 due to overflow")
    print()
    print("FIX:")
    print("  - Ibis should use a wider integer type for power operations")
    print("  - OR Polars backend should not enforce narrow types for literals")
    print("  - OR Power operation should automatically upcast")
