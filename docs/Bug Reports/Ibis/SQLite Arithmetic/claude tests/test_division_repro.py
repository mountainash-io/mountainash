import ibis
import pandas as pd

# Test data
df = pd.DataFrame({
    'dividend': [20, 10, 5, 7],
    'divisor': [3, 4, 2, 3]
})

# SQLite backend
con_sqlite = ibis.sqlite.connect()
t_sqlite = con_sqlite.create_table('test', df)
result_sqlite = t_sqlite.select(
    (t_sqlite.dividend / t_sqlite.divisor).name('result')
).execute()

print("SQLite results:")
print(result_sqlite)
print(f"Types: {result_sqlite['result'].dtype}")

# DuckDB backend (for comparison)
con_duckdb = ibis.duckdb.connect()
t_duckdb = con_duckdb.create_table('test', df)
result_duckdb = t_duckdb.select(
    (t_duckdb.dividend / t_duckdb.divisor).name('result')
).execute()

print("\nDuckDB results:")
print(result_duckdb)
print(f"Types: {result_duckdb['result'].dtype}")

# Show the generated SQL
print("\n--- Generated SQL ---")
print("SQLite SQL:")
print(ibis.to_sql(t_sqlite.select((t_sqlite.dividend / t_sqlite.divisor).name('result')), dialect='sqlite'))

print("\nDuckDB SQL:")
print(ibis.to_sql(t_duckdb.select((t_duckdb.dividend / t_duckdb.divisor).name('result')), dialect='duckdb'))
