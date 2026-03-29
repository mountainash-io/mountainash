import ibis
import pandas as pd
import sqlite3

# Test data with negative operands
df = pd.DataFrame({
    'dividend': [-10, 10, -10, -17, 17],
    'divisor': [3, -3, -3, 4, -4]
})

print("=== Expected (Python) ===")
for i, row in df.iterrows():
    result = row['dividend'] % row['divisor']
    print(f"{row['dividend']:3d} % {row['divisor']:3d} = {result:3d}")

# SQLite backend
con_sqlite = ibis.sqlite.connect()
t_sqlite = con_sqlite.create_table('test', df)
result_sqlite = t_sqlite.select(
    t_sqlite.dividend,
    t_sqlite.divisor,
    (t_sqlite.dividend % t_sqlite.divisor).name('result')
).execute()

print("\n=== SQLite (via Ibis) ===")
for _, row in result_sqlite.iterrows():
    print(f"{row['dividend']:3d} % {row['divisor']:3d} = {row['result']:3d}")

# DuckDB backend (for comparison)
con_duckdb = ibis.duckdb.connect()
t_duckdb = con_duckdb.create_table('test', df)
result_duckdb = t_duckdb.select(
    t_duckdb.dividend,
    t_duckdb.divisor,
    (t_duckdb.dividend % t_duckdb.divisor).name('result')
).execute()

print("\n=== DuckDB ===")
for _, row in result_duckdb.iterrows():
    print(f"{row['dividend']:3d} % {row['divisor']:3d} = {row['result']:3d}")

# Show the generated SQL
print("\n=== Generated SQL ===")
expr = t_sqlite.select((t_sqlite.dividend % t_sqlite.divisor).name('result'))
print("SQLite SQL:")
print(ibis.to_sql(expr, dialect='sqlite'))

expr_duck = t_duckdb.select((t_duckdb.dividend % t_duckdb.divisor).name('result'))
print("\nDuckDB SQL:")
print(ibis.to_sql(expr_duck, dialect='duckdb'))

# Test raw SQLite
print("\n=== Raw SQLite ===")
db_path = "docs/Bug Reports/Ibis/SQLite Arithmetic/test_modulo.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("CREATE TABLE test (dividend INTEGER, divisor INTEGER)")
cursor.execute("INSERT INTO test VALUES (-10, 3), (10, -3), (-10, -3), (-17, 4), (17, -4)")
conn.commit()

cursor.execute("SELECT dividend, divisor, dividend % divisor FROM test")
raw_results = cursor.fetchall()
for row in raw_results:
    print(f"{row[0]:3d} % {row[1]:3d} = {row[2]:3d}")

conn.close()

# Clean up
import os
os.remove(db_path)
