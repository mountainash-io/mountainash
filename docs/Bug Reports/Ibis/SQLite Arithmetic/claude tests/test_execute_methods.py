"""
Test difference between con.execute() and cursor.execute().
"""
import sqlite3
import pandas as pd

# Create database
conn = sqlite3.connect(':memory:')
df = pd.DataFrame({'a': [10, 20, 30], 'b': [2, 3, 4], 'c': [5, 10, 15]})
df.to_sql('test', conn, index=False, if_exists='replace')

sql = """
SELECT
  ((a + b) * c) - (CAST(a AS REAL) / b) AS result
FROM test
"""

print("=" * 80)
print("METHOD 1: cursor.execute()")
print("=" * 80)
cursor1 = conn.cursor()
cursor1.execute(sql)
rows1 = cursor1.fetchall()
print(f"Result: {rows1}")
print(f"Types: {[type(r[0]) for r in rows1]}")

print("\n" + "=" * 80)
print("METHOD 2: conn.execute()")
print("=" * 80)
cursor2 = conn.execute(sql)
rows2 = cursor2.fetchall()
print(f"Result: {rows2}")
print(f"Types: {[type(r[0]) for r in rows2]}")

print("\n" + "=" * 80)
print("METHOD 3: conn.execute() then iterate")
print("=" * 80)
cursor3 = conn.execute(sql)
rows3 = list(cursor3)
print(f"Result: {rows3}")
print(f"Types: {[type(r[0]) for r in rows3]}")

conn.close()
