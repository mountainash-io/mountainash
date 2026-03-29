#!/usr/bin/env python3
"""Test power operator across different Ibis backends."""

import sys
sys.path.insert(0, '/home/nathanielramm/git/ibis')

import ibis

print("Testing Power Operator Across Backends")
print("=" * 60)
print()

# Test with DuckDB backend
print("1. DuckDB Backend:")
print("-" * 60)
try:
    con = ibis.duckdb.connect()
    con.raw_sql("CREATE TABLE test AS SELECT 10 AS x")
    table = con.table('test')

    col = table.x
    lit_2 = ibis.literal(2)

    # Forward
    expr1 = col ** lit_2
    result1 = expr1.execute()[0]
    print(f"col ** lit (10 ** 2) = {result1} {'✅' if result1 == 100 else '❌'}")

    # Reverse with literal
    expr2 = lit_2 ** col
    result2 = expr2.execute()[0]
    print(f"lit ** col (2 ** 10) = {result2} {'✅' if result2 == 1024 else '❌'}")

    # Reverse with raw
    expr3 = 2 ** col
    result3 = expr3.execute()[0]
    print(f"2 ** col (2 ** 10) = {result3} {'✅' if result3 == 1024 else '❌'}")

    # Show SQL
    print()
    print("Generated SQL for lit ** col:")
    print(ibis.to_sql(lit_2 ** col))

except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")

print()

# Test with SQLite backend
print("2. SQLite Backend:")
print("-" * 60)
try:
    con = ibis.sqlite.connect()
    con.raw_sql("CREATE TABLE test (x INTEGER)")
    con.raw_sql("INSERT INTO test VALUES (10)")
    table = con.table('test')

    col = table.x
    lit_2 = ibis.literal(2)

    # Forward
    expr1 = col ** lit_2
    result1 = expr1.execute()[0]
    print(f"col ** lit (10 ** 2) = {result1} {'✅' if result1 == 100 else '❌'}")

    # Reverse with literal
    expr2 = lit_2 ** col
    result2 = expr2.execute()[0]
    print(f"lit ** col (2 ** 10) = {result2} {'✅' if result2 == 1024 else '❌'}")

    # Reverse with raw
    expr3 = 2 ** col
    result3 = expr3.execute()[0]
    print(f"2 ** col (2 ** 10) = {result3} {'✅' if result3 == 1024 else '❌'}")

    # Show SQL
    print()
    print("Generated SQL for lit ** col:")
    print(ibis.to_sql(lit_2 ** col))

except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")

print()

# Test with Polars backend (for comparison)
print("3. Polars Backend:")
print("-" * 60)
try:
    import polars as pl

    con = ibis.polars.connect()
    df = pl.DataFrame({'x': [10]})
    table = con.create_table('test', df, overwrite=True)

    col = ibis._['x']
    lit_2 = ibis.literal(2)

    # Forward
    expr1 = col ** lit_2
    result1 = table.select(expr1.name('r'))['r'].execute().tolist()[0]
    print(f"col ** lit (10 ** 2) = {result1} {'✅' if result1 == 100 else '❌'}")

    # Reverse with literal
    expr2 = lit_2 ** col
    result2 = table.select(expr2.name('r'))['r'].execute().tolist()[0]
    print(f"lit ** col (2 ** 10) = {result2} {'✅' if result2 == 1024 else '❌'}")

    # Reverse with raw
    expr3 = 2 ** col
    result3 = table.select(expr3.name('r'))['r'].execute().tolist()[0]
    print(f"2 ** col (2 ** 10) = {result3} {'✅' if result3 == 1024 else '❌'}")

except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")

print()
print("=" * 60)
print("Summary:")
print("If DuckDB and SQLite work but Polars fails, it's a Polars backend issue")
print("If all backends fail, it's a core Ibis issue")
print("=" * 60)
