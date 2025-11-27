#!/usr/bin/env python3
"""Compare how Ibis translates cast vs literal."""

import sys
sys.path.insert(0, '/home/nathanielramm/git/ibis')

import ibis
import polars as pl
from ibis.backends.polars import compiler

# Monkey-patch to see translations
translations = []

original_translate = compiler.translate.registry.copy()

def capture_translate(expr, **kw):
    result = original_translate[type(expr)](expr, **kw)
    translations.append((type(expr).__name__, str(result)))
    return result

# Patch the main types we care about
for key in [ibis.expr.operations.generic.Literal, ibis.expr.operations.generic.Cast]:
    compiler.translate.register(key)(capture_translate)

conn = ibis.polars.connect()
df = pl.DataFrame({'x': [10]})
table = conn.create_table('test', df, overwrite=True)
col = ibis._['x']

print("Translation Comparison: Literal vs Cast")
print("=" * 60)
print()

# Test 1: Plain literal
print("1. Plain literal (int16):")
translations.clear()
lit_128 = ibis.literal(128)
print(f"   Ibis type: {lit_128.type()}")
expr1 = lit_128 ** col
print(f"   Expression: {expr1}")
try:
    result1 = table.select(expr1.name('r'))['r'].execute().tolist()[0]
    print(f"   Result: {result1} {'✅' if result1 == 1024 else '❌'}")
except Exception as e:
    print(f"   Error: {e}")
print(f"   Translations: {translations}")
print()

# Test 2: Cast literal
print("2. Cast literal (int8 -> int16):")
translations.clear()
lit_2_cast = ibis.literal(2).cast('int16')
print(f"   Ibis type: {lit_2_cast.type()}")
expr2 = lit_2_cast ** col
print(f"   Expression: {expr2}")
try:
    result2 = table.select(expr2.name('r'))['r'].execute().tolist()[0]
    print(f"   Result: {result2} {'✅' if result2 == 1024 else '❌'}")
except Exception as e:
    print(f"   Error: {e}")
print(f"   Translations: {translations}")
print()

# Test 3: Check the actual Polars expressions
print("3. Direct Polars comparison:")
print("-" * 60)

# What Ibis generates for literal(128)
polars_lit_128 = pl.lit(128, dtype=pl.Int16)
result_lit = df.select(polars_lit_128.pow(pl.col('x')).alias('r'))['r'][0]
print(f"   pl.lit(128, dtype=Int16).pow(col) = {result_lit} {'✅' if result_lit == 1024 else '❌'}")

# What Ibis generates for cast
polars_cast = pl.lit(2, dtype=pl.Int8).cast(pl.Int16)
result_cast = df.select(polars_cast.pow(pl.col('x')).alias('r'))['r'][0]
print(f"   pl.lit(2, dtype=Int8).cast(Int16).pow(col) = {result_cast} {'✅' if result_cast == 1024 else '❌'}")

# Without dtype constraint
polars_no_dtype = pl.lit(128)
result_no_dtype = df.select(polars_no_dtype.pow(pl.col('x')).alias('r'))['r'][0]
print(f"   pl.lit(128).pow(col) = {result_no_dtype} {'✅' if result_no_dtype == 1024 else '❌'}")

print()
print("=" * 60)
