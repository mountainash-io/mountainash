"""
Compare Ibis-created connection vs raw SQLite.
"""
import ibis
import pandas as pd
import sqlite3

df = pd.DataFrame({
    'a': [10, 20, 30],
    'b': [2, 3, 4],
    'c': [5, 10, 15]
})

# Test 1: Ibis connection
print("=" * 80)
print("TEST 1: IBIS CONNECTION")
print("=" * 80)

con_ibis = ibis.sqlite.connect()
t_ibis = con_ibis.create_table('test_ibis', df)

sql_ibis = """
SELECT
  ((a + b) * c) - (CAST(a AS REAL) / b) AS result
FROM test_ibis
"""

cursor_ibis = con_ibis.con.cursor()
cursor_ibis.execute(sql_ibis)
rows_ibis = cursor_ibis.fetchall()

print(f"Rows: {rows_ibis}")
print(f"Types: {[type(r[0]) for r in rows_ibis]}")

# Test 2: Fresh SQLite connection
print("\n" + "=" * 80)
print("TEST 2: FRESH SQLITE CONNECTION")
print("=" * 80)

conn_raw = sqlite3.connect(':memory:')
df.to_sql('test_raw', conn_raw, index=False, if_exists='replace')

cursor_raw = conn_raw.cursor()
cursor_raw.execute("""
SELECT
  ((a + b) * c) - (CAST(a AS REAL) / b) AS result
FROM test_raw
""")
rows_raw = cursor_raw.fetchall()

print(f"Rows: {rows_raw}")
print(f"Types: {[type(r[0]) for r in rows_raw]}")

# Test 3: Check actual table schemas
print("\n" + "=" * 80)
print("TEST 3: TABLE SCHEMAS")
print("=" * 80)

print("Ibis-created table:")
cursor_ibis.execute("PRAGMA table_info(test_ibis)")
for row in cursor_ibis.fetchall():
    print(f"  {row[1]}: {row[2]}")

print("\nRaw SQLite table:")
cursor_raw.execute("PRAGMA table_info(test_raw)")
for row in cursor_raw.fetchall():
    print(f"  {row[1]}: {row[2]}")

# Test 4: Test pd.DataFrame.from_records on both
print("\n" + "=" * 80)
print("TEST 4: pd.DataFrame.from_records")
print("=" * 80)

cursor_ibis.execute(sql_ibis)
df_ibis = pd.DataFrame.from_records(cursor_ibis, columns=['result'], coerce_float=True)
print(f"Ibis connection:")
print(f"  Dtype: {df_ibis['result'].dtype}")
print(f"  Values: {df_ibis['result'].tolist()}")

cursor_raw.execute("""
SELECT
  ((a + b) * c) - (CAST(a AS REAL) / b) AS result
FROM test_raw
""")
df_raw = pd.DataFrame.from_records(cursor_raw, columns=['result'], coerce_float=True)
print(f"\nRaw connection:")
print(f"  Dtype: {df_raw['result'].dtype}")
print(f"  Values: {df_raw['result'].tolist()}")

con_ibis.con.close()
conn_raw.close()
