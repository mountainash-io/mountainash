import ibis
import pandas as pd

df = pd.DataFrame({
    'a': [10, 20, 30],
    'b': [2, 3, 4],
    'c': [5, 10, 15]
})

con = ibis.sqlite.connect()
t = con.create_table('test', df)

# Test individual operations
print("Individual operations:")
print("=" * 60)

# Just division
result_div = t.select((t.a / t.b).name('result')).execute()
print("a / b:", result_div['result'].tolist())
sql_div = ibis.to_sql(t.select((t.a / t.b).name('result')), dialect='sqlite')
print("SQL:", sql_div.strip())

# a + b
result_add = t.select((t.a + t.b).name('result')).execute()
print("\na + b:", result_add['result'].tolist())

# (a + b) * c
result_mult = t.select(((t.a + t.b) * t.c).name('result')).execute()
print("\n(a + b) * c:", result_mult['result'].tolist())

# Full expression
print("\nFull expression: (a + b) * c - a / b")
print("=" * 60)
expr = (t.a + t.b) * t.c - t.a / t.b
result_full = t.select(expr.name('result')).execute()
print("Result:", result_full['result'].tolist())

sql_full = ibis.to_sql(t.select(expr.name('result')), dialect='sqlite')
print("\nGenerated SQL:")
print(sql_full)

# Manual calculation
print("\nManual calculation:")
print("Row 0: (10+2)*5 - 10/2 = 60 - 5.0 = 55.0")
print("Row 1: (20+3)*10 - 20/3 = 230 - 6.666... = 223.333...")
print("Row 2: (30+4)*15 - 30/4 = 510 - 7.5 = 502.5")

# Test what types the columns have
print("\nColumn types in created table:")
import sqlite3
conn = sqlite3.connect(':memory:')
df.to_sql('test2', conn, index=False, if_exists='replace')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(test2)")
for row in cursor.fetchall():
    print(f"  {row[1]}: {row[2]}")
