#!/usr/bin/env python3
"""
Minimal reproduction for Ibis Polars backend power operation bug.

Demonstrates that ibis.literal(2) ** column returns 0 instead of 1024
due to narrow type inference combined with Polars backend implementation.
"""

import sys
sys.path.insert(0, '/home/nathanielramm/git/ibis')

import ibis
import polars as pl

print("Ibis Polars Backend Power Operation Bug")
print("=" * 60)
print()

# Setup
conn = ibis.polars.connect()
df = pl.DataFrame({'x': [10]})
table = conn.create_table('test', df, overwrite=True)

print("Computing: 2 ** 10 = 1024")
print("-" * 60)
print()

# Show type inference
lit2 = ibis.literal(2)
print(f"Type inference: ibis.literal(2) → {lit2.type()}")
print()

# Case 1: Literal on left - FAILS
print("Case 1: ibis.literal(2) ** col")
try:
    expr1 = ibis.literal(2) ** ibis._['x']
    result1 = table.select(expr1.name('r'))['r'].execute().tolist()[0]
    print(f"  Result: {result1}")
    print(f"  Expected: 1024")
    print(f"  Status: {'✅ PASS' if result1 == 1024 else '❌ FAIL (returns 0)'}")
except Exception as e:
    print(f"  ERROR: {e}")
print()

# Case 2: Raw value on left - FAILS
print("Case 2: 2 ** col")
try:
    expr2 = 2 ** ibis._['x']
    result2 = table.select(expr2.name('r'))['r'].execute().tolist()[0]
    print(f"  Result: {result2}")
    print(f"  Expected: 1024")
    print(f"  Status: {'✅ PASS' if result2 == 1024 else '❌ FAIL (returns 0)'}")
except Exception as e:
    print(f"  ERROR: {e}")
print()

# Case 3: Literal on right - WORKS
print("Case 3: col ** ibis.literal(2)")
try:
    expr3 = ibis._['x'] ** ibis.literal(2)
    result3 = table.select(expr3.name('r'))['r'].execute().tolist()[0]
    print(f"  Result: {result3}")
    print(f"  Expected: 100 (10^2)")
    print(f"  Status: {'✅ PASS' if result3 == 100 else '❌ FAIL'}")
except Exception as e:
    print(f"  ERROR: {e}")
print()

# Case 4: Cast to wider type - WORKS
print("Case 4: ibis.literal(2).cast('int64') ** col")
try:
    expr4 = ibis.literal(2).cast('int64') ** ibis._['x']
    result4 = table.select(expr4.name('r'))['r'].execute().tolist()[0]
    print(f"  Result: {result4}")
    print(f"  Expected: 1024")
    print(f"  Status: {'✅ PASS' if result4 == 1024 else '❌ FAIL'}")
except Exception as e:
    print(f"  ERROR: {e}")
print()

# Comparison with other backends
print("=" * 60)
print("BACKEND COMPARISON:")
print("-" * 60)

# DuckDB
try:
    conn_duck = ibis.duckdb.connect()
    conn_duck.raw_sql("CREATE TABLE test AS SELECT 10 AS x")
    table_duck = conn_duck.table('test')
    result_duck = (ibis.literal(2) ** table_duck.x).execute()[0]
    print(f"  DuckDB:  {result_duck} {'✅' if result_duck == 1024 else '❌'}")
except Exception as e:
    print(f"  DuckDB:  ERROR - {e}")

# SQLite
try:
    conn_sqlite = ibis.sqlite.connect()
    conn_sqlite.raw_sql("CREATE TABLE test (x INTEGER)")
    conn_sqlite.raw_sql("INSERT INTO test VALUES (10)")
    table_sqlite = conn_sqlite.table('test')
    result_sqlite = (ibis.literal(2) ** table_sqlite.x).execute()[0]
    print(f"  SQLite:  {result_sqlite} {'✅' if result_sqlite == 1024 else '❌'}")
except Exception as e:
    print(f"  SQLite:  ERROR - {e}")

# Polars
print(f"  Polars:  {result1} {'✅' if result1 == 1024 else '❌'}")
print()

# Summary
print("=" * 60)
print("SUMMARY:")
print("  • literal(2) [Int8] ** col returns 0 (WRONG)")
print("  • literal(2).cast('int64') ** col returns 1024 (CORRECT)")
print("  • DuckDB and SQLite backends work correctly")
print("  • Issue is specific to Polars backend")
print()
print("ROOT CAUSE:")
print("  1. Ibis infers literal(2) as Int8")
print("  2. Polars backend passes dtype=Int8 to pl.lit()")
print("  3. Polars' .pow() method overflows Int8 → returns 0")
print()

if result1 == 0:
    print("🐛 BUG CONFIRMED: Ibis Polars backend produces wrong results")
else:
    print("✅ Bug appears to be fixed!")
