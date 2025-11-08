import ibis
import pandas as pd
import sqlite3

df = pd.DataFrame({
    'a': [10, 20, 30],
    'b': [2, 3, 4],
    'c': [5, 10, 15]
})

# Test with Ibis
print("=" * 80)
print("IBIS")
print("=" * 80)
con_ibis = ibis.sqlite.connect()
t_ibis = con_ibis.create_table('test_ibis', df)
expr_ibis = (t_ibis.a + t_ibis.b) * t_ibis.c - t_ibis.a / t_ibis.b

result_ibis = t_ibis.select(expr_ibis.name('result')).execute()
print("Result:", result_ibis['result'].tolist())
print("Types:", result_ibis['result'].dtype)
print("\nDataFrame:")
print(result_ibis)

sql_ibis = ibis.to_sql(t_ibis.select(expr_ibis.name('result')), dialect='sqlite')
print("\nGenerated SQL:")
print(sql_ibis)

# Get the raw connection and test
print("\n" + "=" * 80)
print("DIRECT SQL ON IBIS CONNECTION")
print("=" * 80)
# Access Ibis's underlying connection
ibis_con = con_ibis.con
cursor = ibis_con.cursor()

cursor.execute(sql_ibis)
rows = cursor.fetchall()
print("Raw fetchall():", rows)
print("Types:", [type(val) for row in rows for val in row])

# Compare with fresh connection
print("\n" + "=" * 80)
print("FRESH SQLITE CONNECTION")
print("=" * 80)
fresh_conn = sqlite3.connect(':memory:')
df.to_sql('test_fresh', fresh_conn, index=False, if_exists='replace')
cursor2 = fresh_conn.cursor()

sql_fresh = """
SELECT
  ((a + b) * c) - (CAST(a AS REAL) / b) AS result
FROM test_fresh
"""
cursor2.execute(sql_fresh)
rows2 = cursor2.fetchall()
print("Raw fetchall():", rows2)
print("Types:", [type(val) for row in rows2 for val in row])

fresh_conn.close()
