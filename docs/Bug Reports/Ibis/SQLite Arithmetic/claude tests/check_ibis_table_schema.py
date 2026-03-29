"""
Check the exact SQL and table schema that Ibis creates.
"""
import ibis
import pandas as pd
import sqlite3

df = pd.DataFrame({
    'a': [10, 20, 30],
    'b': [2, 3, 4],
    'c': [5, 10, 15]
})

print("=" * 80)
print("PANDAS INPUT DTYPES")
print("=" * 80)
print(df.dtypes)

con = ibis.sqlite.connect()
t = con.create_table('test', df)

# Check the actual table schema in SQLite
print("\n" + "=" * 80)
print("SQLITE TABLE SCHEMA")
print("=" * 80)
cursor = con.con.cursor()
cursor.execute("PRAGMA table_info(test)")
for row in cursor.fetchall():
    print(f"  Column: {row[1]}, Type: {row[2]}")

# Check Ibis schema
print("\n" + "=" * 80)
print("IBIS TABLE SCHEMA")
print("=" * 80)
print(t.schema())

# Generate the SQL for our expression
expr = (t.a + t.b) * t.c - t.a / t.b
table_expr = t.select(expr.name('result'))

print("\n" + "=" * 80)
print("GENERATED SQL")
print("=" * 80)
sql = ibis.to_sql(table_expr, dialect='sqlite')
print(sql)

# Execute the SQL directly
print("\n" + "=" * 80)
print("DIRECT SQL EXECUTION ON IBIS CONNECTION")
print("=" * 80)
cursor = con.con.cursor()
cursor.execute(sql)
rows = cursor.fetchall()
print(f"Raw rows: {rows}")
print(f"Types: {[type(r[0]) for r in rows]}")

# Test pd.DataFrame.from_records on this cursor
cursor.execute(sql)
df_direct = pd.DataFrame.from_records(cursor, columns=['result'], coerce_float=True)
print(f"\npd.DataFrame.from_records:")
print(f"  Values: {df_direct['result'].tolist()}")
print(f"  Dtype: {df_direct['result'].dtype}")

# Now test through Ibis
print("\n" + "=" * 80)
print("IBIS .execute()")
print("=" * 80)
result_ibis = table_expr.execute()
print(f"  Values: {result_ibis['result'].tolist()}")
print(f"  Dtype: {result_ibis['result'].dtype}")

con.con.close()
