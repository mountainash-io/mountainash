"""
Test precision loss bug across all Ibis backends.
Checks if the rounding issue is SQLite-specific or affects other backends too.
"""
import ibis
import pandas as pd

# Test data
df = pd.DataFrame({
    'a': [10, 20, 30],
    'b': [2, 3, 4],
    'c': [5, 10, 15]
})

# Expected values (Python calculation)
expected = [
    (10+2)*5 - 10/2,    # 55.0
    (20+3)*10 - 20/3,   # 223.33333333333334
    (30+4)*15 - 30/4    # 502.5
]

print("=" * 80)
print("TESTING PRECISION LOSS ACROSS IBIS BACKENDS")
print("=" * 80)
print(f"\nExpected (Python): {expected}")
print(f"Critical values: {expected[1]:.10f}, {expected[2]:.10f}")

backends = []

# Test SQLite
print("\n" + "=" * 80)
print("SQLite Backend")
print("=" * 80)
try:
    con_sqlite = ibis.sqlite.connect()
    t_sqlite = con_sqlite.create_table('test_sqlite', df)
    expr_sqlite = (t_sqlite.a + t_sqlite.b) * t_sqlite.c - t_sqlite.a / t_sqlite.b
    result_sqlite = t_sqlite.select(expr_sqlite.name('result')).execute()['result'].tolist()

    print(f"Result: {result_sqlite}")
    match = all(abs(r - e) < 0.0001 for r, e in zip(result_sqlite, expected))
    backends.append(('SQLite', result_sqlite, match))

    # Check raw SQL
    sql = ibis.to_sql(t_sqlite.select(expr_sqlite.name('result')), dialect='sqlite')
    cursor = con_sqlite.con.cursor()
    cursor.execute(sql)
    raw = [row[0] for row in cursor.fetchall()]
    print(f"Raw SQL: {raw}")
    print(f"Match .execute(): {match}")
    print(f"Match raw SQL: {all(abs(r - e) < 0.0001 for r, e in zip(raw, expected))}")
except Exception as e:
    print(f"Error: {e}")
    backends.append(('SQLite', f'Error: {e}', False))

# Test DuckDB
print("\n" + "=" * 80)
print("DuckDB Backend")
print("=" * 80)
try:
    con_duckdb = ibis.duckdb.connect()
    t_duckdb = con_duckdb.create_table('test_duckdb', df)
    expr_duckdb = (t_duckdb.a + t_duckdb.b) * t_duckdb.c - t_duckdb.a / t_duckdb.b
    result_duckdb = t_duckdb.select(expr_duckdb.name('result')).execute()['result'].tolist()

    print(f"Result: {result_duckdb}")
    match = all(abs(r - e) < 0.0001 for r, e in zip(result_duckdb, expected))
    backends.append(('DuckDB', result_duckdb, match))
    print(f"Match: {match}")
except Exception as e:
    print(f"Error: {e}")
    backends.append(('DuckDB', f'Error: {e}', False))

# Test Polars
print("\n" + "=" * 80)
print("Polars Backend")
print("=" * 80)
try:
    con_polars = ibis.polars.connect()
    t_polars = con_polars.create_table('test_polars', df)
    expr_polars = (t_polars.a + t_polars.b) * t_polars.c - t_polars.a / t_polars.b
    result_polars = t_polars.select(expr_polars.name('result')).execute()['result'].tolist()

    print(f"Result: {result_polars}")
    match = all(abs(r - e) < 0.0001 for r, e in zip(result_polars, expected))
    backends.append(('Polars', result_polars, match))
    print(f"Match: {match}")
except Exception as e:
    print(f"Error: {e}")
    backends.append(('Polars', f'Error: {e}', False))

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"\nExpected: {expected}")

for backend_name, result, match in backends:
    if isinstance(result, list):
        status = "✓ CORRECT" if match else "✗ PRECISION LOSS"
        print(f"\n{backend_name:8s}: {result}")
        print(f"             {status}")

        # Show specific differences
        if not match:
            print(f"             Differences:")
            for i, (r, e) in enumerate(zip(result, expected)):
                diff = r - e
                if abs(diff) > 0.0001:
                    print(f"               [{i}] {r} vs {e} (diff: {diff:+.10f})")
    else:
        print(f"\n{backend_name:8s}: {result}")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)
affected_backends = [name for name, result, match in backends if isinstance(result, list) and not match]
if affected_backends:
    print(f"Precision loss affects: {', '.join(affected_backends)}")
else:
    print("No precision loss detected in any backend!")
