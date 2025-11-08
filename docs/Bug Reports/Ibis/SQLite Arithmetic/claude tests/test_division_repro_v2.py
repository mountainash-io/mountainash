import ibis
import sqlite3

# Create a REAL SQLite database with INTEGER columns
db_path = "docs/Bug Reports/Ibis/SQLite Arithmetic/test.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create table with explicit INTEGER types
cursor.execute("DROP TABLE IF EXISTS test")
cursor.execute("""
    CREATE TABLE test (
        dividend INTEGER,
        divisor INTEGER
    )
""")

# Insert integer data
cursor.execute("INSERT INTO test VALUES (20, 3), (10, 4), (5, 2), (7, 3)")
conn.commit()

# Test raw SQLite behavior
print("=== Raw SQLite behavior ===")
cursor.execute("SELECT dividend / divisor AS result FROM test")
raw_results = cursor.fetchall()
print("Raw SQLite (no cast):", raw_results)

cursor.execute("SELECT CAST(dividend AS REAL) / divisor AS result FROM test")
casted_results = cursor.fetchall()
print("SQLite with cast:", casted_results)

conn.close()

# Now test with Ibis
print("\n=== Ibis behavior ===")
con_sqlite = ibis.sqlite.connect(db_path)
t_sqlite = con_sqlite.table('test')

result_sqlite = t_sqlite.select(
    (t_sqlite.dividend / t_sqlite.divisor).name('result')
).execute()

print("Ibis SQLite results:")
print(result_sqlite)
print(f"Types: {result_sqlite['result'].dtype}")

# Show the generated SQL
print("\nGenerated SQL:")
sql = ibis.to_sql(t_sqlite.select((t_sqlite.dividend / t_sqlite.divisor).name('result')), dialect='sqlite')
print(sql)

# Test with literal integers
print("\n=== Testing with literals ===")
t = con_sqlite.table('test')
expr_col_div_lit = t.select((t.dividend / 3).name('result'))
expr_lit_div_col = t.select((20 / t.divisor).name('result'))

print("Column / Literal (dividend / 3):")
print(expr_col_div_lit.execute())
print("SQL:", ibis.to_sql(expr_col_div_lit, dialect='sqlite'))

print("\nLiteral / Column (20 / divisor):")
print(expr_lit_div_col.execute())
print("SQL:", ibis.to_sql(expr_lit_div_col, dialect='sqlite'))

# Clean up
import os
os.remove(db_path)
