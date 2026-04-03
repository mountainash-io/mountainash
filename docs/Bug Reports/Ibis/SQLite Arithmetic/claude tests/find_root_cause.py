"""
Find the root cause - what does the cursor actually return?
"""
import pandas as pd
import sqlite3

# Create test database
conn = sqlite3.connect(':memory:')
cursor = conn.cursor()
cursor.execute("CREATE TABLE test (a INTEGER, b INTEGER, c INTEGER)")
cursor.execute("INSERT INTO test VALUES (10, 2, 5), (20, 3, 10), (30, 4, 15)")
conn.commit()

# Execute the problematic SQL (same as Ibis generates)
sql = """
SELECT
  ((a + b) * c) - (CAST(a AS REAL) / b) AS result
FROM test
"""

print("=" * 80)
print("CURSOR RAW DATA")
print("=" * 80)
cursor.execute(sql)
rows = cursor.fetchall()
print(f"Raw rows: {rows}")
print(f"Types: {[type(row[0]) for row in rows]}")

# Now test pd.DataFrame.from_records with a fresh cursor
cursor.execute(sql)
print("\n" + "=" * 80)
print("PANDAS from_records (coerce_float=True)")
print("=" * 80)

# Peek at first row without consuming cursor
first_row = cursor.fetchone()
print(f"First row from cursor: {first_row}, type: {type(first_row[0])}")

# Reset cursor
cursor.execute(sql)

# This is what Ibis does
df = pd.DataFrame.from_records(cursor, columns=['result'], coerce_float=True)
print(f"DataFrame:\n{df}")
print(f"Dtypes: {df.dtypes}")
print(f"Values: {df['result'].tolist()}")

# Test with column names from schema
cursor.execute(sql)
print("\n" + "=" * 80)
print("PANDAS from_records (with explicit columns)")
print("=" * 80)
df2 = pd.DataFrame.from_records(
    cursor,
    columns=['result'],  # Explicitly name columns
    coerce_float=True
)
print(f"DataFrame:\n{df2}")
print(f"Dtypes: {df2.dtypes}")

# Test consuming cursor as list first
cursor.execute(sql)
print("\n" + "=" * 80)
print("PANDAS DataFrame from list of tuples")
print("=" * 80)
rows_list = list(cursor)
print(f"Rows list: {rows_list}")
print(f"Types in list: {[type(r[0]) for r in rows_list]}")
df3 = pd.DataFrame(rows_list, columns=['result'])
print(f"DataFrame:\n{df3}")
print(f"Dtypes: {df3.dtypes}")

conn.close()
