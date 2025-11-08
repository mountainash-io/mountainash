"""
Trace the exact _fetch_from_cursor behavior.
"""
import ibis
import pandas as pd

# Monkey-patch _fetch_from_cursor to trace it
from ibis.backends.sqlite import Backend as SQLiteBackend

original_fetch = SQLiteBackend._fetch_from_cursor

def traced_fetch(self, cursor, schema):
    print(f"\n[TRACE] _fetch_from_cursor called")
    print(f"  Schema: {schema}")
    print(f"  Cursor type: {type(cursor)}")

    # Peek at first row
    first_row = cursor.fetchone()
    if first_row:
        print(f"  First row from cursor: {first_row}")
        print(f"  First row types: {[type(v) for v in first_row]}")
        # Put it back by creating new cursor (can't rewind sqlite cursor)
        # We'll let the original method handle the full fetch
        pass

    # Call original - but we consumed a row, so need to handle that
    # Actually, let's not peek and just trace the DataFrame creation
    print(f"  Calling pd.DataFrame.from_records...")

    # Manually do what _fetch_from_cursor does
    df = pd.DataFrame.from_records(cursor, columns=schema.names, coerce_float=True)
    print(f"  DataFrame created:")
    print(f"    Shape: {df.shape}")
    print(f"    Dtypes: {df.dtypes.to_dict()}")
    print(f"    First 3 rows: {df.head(3).to_dict('records')}")

    from ibis.backends.sqlite.converter import SQLitePandasData
    result = SQLitePandasData.convert_table(df, schema)
    print(f"  After convert_table:")
    print(f"    Dtypes: {result.dtypes.to_dict()}")
    print(f"    First 3 rows: {result.head(3).to_dict('records')}")

    return result

SQLiteBackend._fetch_from_cursor = traced_fetch

# Now run the test
print("=" * 80)
print("RUNNING TRACED EXECUTION")
print("=" * 80)

df = pd.DataFrame({
    'a': [10, 20, 30],
    'b': [2, 3, 4],
    'c': [5, 10, 15]
})

con = ibis.sqlite.connect()
t = con.create_table('test', df)

expr = (t.a + t.b) * t.c - t.a / t.b
result = t.select(expr.name('result')).execute()

print("\n" + "=" * 80)
print("FINAL RESULT")
print("=" * 80)
print(f"Result: {result['result'].tolist()}")

# Restore
SQLiteBackend._fetch_from_cursor = original_fetch

con.con.close()
