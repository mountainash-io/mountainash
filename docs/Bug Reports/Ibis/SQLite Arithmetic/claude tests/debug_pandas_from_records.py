"""
Test what pd.DataFrame.from_records with coerce_float=True does.
"""
import pandas as pd
import sqlite3

# Create test database
conn = sqlite3.connect(':memory:')
cursor = conn.cursor()
cursor.execute("CREATE TABLE test (a INTEGER, b INTEGER, c INTEGER)")
cursor.execute("INSERT INTO test VALUES (20, 3, 10)")
conn.commit()

# Execute the problematic SQL
sql = "SELECT ((a + b) * c) - (CAST(a AS REAL) / b) AS result FROM test"
cursor.execute(sql)

# Check raw values
print("=" * 80)
print("RAW CURSOR VALUES")
print("=" * 80)
raw_result = cursor.fetchone()
print(f"Raw fetchone(): {raw_result}")
print(f"Type: {type(raw_result[0])}")
print(f"Value: {raw_result[0]}")

# Re-execute for from_records test
cursor.execute(sql)
print("\n" + "=" * 80)
print("PANDAS from_records WITH coerce_float=True")
print("=" * 80)
df_coerce = pd.DataFrame.from_records(cursor, columns=['result'], coerce_float=True)
print(f"DataFrame:\n{df_coerce}")
print(f"Value: {df_coerce['result'][0]}")
print(f"Dtype: {df_coerce['result'].dtype}")

# Re-execute for from_records test without coerce
cursor.execute(sql)
print("\n" + "=" * 80)
print("PANDAS from_records WITH coerce_float=False")
print("=" * 80)
df_no_coerce = pd.DataFrame.from_records(cursor, columns=['result'], coerce_float=False)
print(f"DataFrame:\n{df_no_coerce}")
print(f"Value: {df_no_coerce['result'][0]}")
print(f"Dtype: {df_no_coerce['result'].dtype}")

# Test with list instead of cursor
cursor.execute(sql)
all_rows = cursor.fetchall()
print("\n" + "=" * 80)
print("PANDAS from list of tuples")
print("=" * 80)
print(f"Raw rows: {all_rows}")
df_from_list = pd.DataFrame(all_rows, columns=['result'])
print(f"DataFrame:\n{df_from_list}")
print(f"Value: {df_from_list['result'][0]}")
print(f"Dtype: {df_from_list['result'].dtype}")

conn.close()
