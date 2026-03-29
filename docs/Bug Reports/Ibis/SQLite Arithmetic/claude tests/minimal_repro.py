"""
Minimal reproduction case.
"""
import ibis
import pandas as pd
import sqlite3

# Test with simplest possible case
df = pd.DataFrame({'a': [20], 'b': [3]})

# Test 1: Raw SQLite
print("=" * 80)
print("TEST 1: RAW SQLITE")
print("=" * 80)

conn_raw = sqlite3.connect(':memory:')
df.to_sql('test', conn_raw, index=False, if_exists='replace')

cursor_raw = conn_raw.cursor()
sql = "SELECT 60 - (CAST(a AS REAL) / b) AS result FROM test"
print(f"SQL: {sql}")

cursor_raw.execute(sql)
row_raw = cursor_raw.fetchone()
print(f"Result: {row_raw}")
print(f"Type: {type(row_raw[0])}")
print(f"Value: {repr(row_raw[0])}")

# Now with pd.DataFrame.from_records
cursor_raw.execute(sql)
df_raw = pd.DataFrame.from_records(cursor_raw, columns=['result'], coerce_float=True)
print(f"DataFrame dtype: {df_raw['result'].dtype}")
print(f"DataFrame value: {df_raw['result'][0]}")

# Test 2: Ibis
print("\n" + "=" * 80)
print("TEST 2: IBIS")
print("=" * 80)

con_ibis = ibis.sqlite.connect()
t_ibis = con_ibis.create_table('test', df)

# Same expression
expr_ibis = 60 - t_ibis.a / t_ibis.b

sql_ibis = ibis.to_sql(t_ibis.select(expr_ibis.name('result')), dialect='sqlite')
print(f"Generated SQL:\n{sql_ibis}")

# Execute via cursor
cursor_ibis = con_ibis.con.cursor()
cursor_ibis.execute(sql_ibis)
row_ibis_cursor = cursor_ibis.fetchone()
print(f"\nDirect cursor result: {row_ibis_cursor}")
print(f"Type: {type(row_ibis_cursor[0])}")

# Execute via Ibis
result_ibis = t_ibis.select(expr_ibis.name('result')).execute()
print(f"\nIbis .execute() result: {result_ibis['result'][0]}")
print(f"Type: {type(result_ibis['result'][0])}")

# Test 3: Check if it's specific to subtraction
print("\n" + "=" * 80)
print("TEST 3: JUST DIVISION (NO SUBTRACTION)")
print("=" * 80)

expr_div_only = t_ibis.a / t_ibis.b
result_div = t_ibis.select(expr_div_only.name('result')).execute()
print(f"Just division result: {result_div['result'][0]}")
print(f"Type: {type(result_div['result'][0])}")

conn_raw.close()
con_ibis.con.close()
