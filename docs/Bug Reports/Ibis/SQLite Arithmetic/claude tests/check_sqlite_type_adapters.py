"""
Check if Ibis configures any type adapters on SQLite connection.
"""
import ibis
import pandas as pd
import sqlite3

# Check what converters/adapters are registered
print("=" * 80)
print("SQLITE3 TYPE CONVERTERS")
print("=" * 80)
print(f"sqlite3.converters: {sqlite3.converters}")

# Create Ibis connection
con_ibis = ibis.sqlite.connect()

print("\n" + "=" * 80)
print("IBIS CONNECTION ATTRIBUTES")
print("=" * 80)
print(f"Connection type: {type(con_ibis.con)}")
print(f"Connection row_factory: {con_ibis.con.row_factory}")

# Check if there's a custom row factory or cursor factory
print(f"text_factory: {con_ibis.con.text_factory}")

# Try to see if there are any custom type adapters
print("\n" + "=" * 80)
print("TEST WITH DIFFERENT DETECT_TYPES")
print("=" * 80)

# Test with PARSE_DECLTYPES
conn_parse_decltypes = sqlite3.connect(':memory:', detect_types=sqlite3.PARSE_DECLTYPES)
df_test = pd.DataFrame({'a': [10, 20], 'b': [2, 3]})
df_test.to_sql('test', conn_parse_decltypes, index=False, if_exists='replace')

cursor_dt = conn_parse_decltypes.cursor()
cursor_dt.execute("SELECT ((a + b) * 5) - (CAST(a AS REAL) / b) AS result FROM test")
rows_dt = cursor_dt.fetchall()
print(f"With PARSE_DECLTYPES: {rows_dt}")
print(f"Types: {[type(r[0]) for r in rows_dt]}")

# Test with PARSE_COLNAMES
conn_parse_colnames = sqlite3.connect(':memory:', detect_types=sqlite3.PARSE_COLNAMES)
df_test.to_sql('test', conn_parse_colnames, index=False, if_exists='replace')

cursor_cn = conn_parse_colnames.cursor()
cursor_cn.execute("SELECT ((a + b) * 5) - (CAST(a AS REAL) / b) AS result FROM test")
rows_cn = cursor_cn.fetchall()
print(f"\nWith PARSE_COLNAMES: {rows_cn}")
print(f"Types: {[type(r[0]) for r in rows_cn]}")

# Test without any detect_types
conn_no_detect = sqlite3.connect(':memory:', detect_types=0)
df_test.to_sql('test', conn_no_detect, index=False, if_exists='replace')

cursor_nd = conn_no_detect.cursor()
cursor_nd.execute("SELECT ((a + b) * 5) - (CAST(a AS REAL) / b) AS result FROM test")
rows_nd = cursor_nd.fetchall()
print(f"\nWithout detect_types: {rows_nd}")
print(f"Types: {[type(r[0]) for r in rows_nd]}")

# Check Ibis connection detect_types
print("\n" + "=" * 80)
print("IBIS CONNECTION detect_types")
print("=" * 80)
# SQLite doesn't expose detect_types directly, but we can test behavior

conn_parse_decltypes.close()
conn_parse_colnames.close()
conn_no_detect.close()
con_ibis.con.close()
