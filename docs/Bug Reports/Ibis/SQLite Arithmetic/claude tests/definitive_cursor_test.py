"""
Definitive test - patch _fetch_from_cursor to see exact cursor state.
"""
import ibis
import pandas as pd
from ibis.backends.sqlite import Backend as SQLiteBackend

# Save original
original_fetch = SQLiteBackend._fetch_from_cursor

def instrumented_fetch(self, cursor, schema):
    print(f"\n[_fetch_from_cursor CALLED]")
    print(f"Schema: {schema}")

    # Save cursor state by converting to list
    rows_list = list(cursor)
    print(f"Cursor contents (as list): {rows_list}")
    if rows_list:
        print(f"First row: {rows_list[0]}")
        print(f"First row type: {type(rows_list[0][0])}")

    # Create a new cursor-like iterator from the list
    class ListCursor:
        def __init__(self, data):
            self.data = iter(data)

        def __iter__(self):
            return self.data

        def __next__(self):
            return next(self.data)

    # Call original with list-based iterator
    fake_cursor = ListCursor(rows_list)

    # Now call the original method
    df = pd.DataFrame.from_records(fake_cursor, columns=schema.names, coerce_float=True)
    print(f"DataFrame from fake_cursor:")
    print(f"  dtype: {df.dtypes.to_dict()}")
    print(f"  values: {df.head().to_dict('records')}")

    from ibis.backends.sqlite.converter import SQLitePandasData
    result = SQLitePandasData.convert_table(df, schema)
    print(f"After convert_table:")
    print(f"  dtype: {result.dtypes.to_dict()}")
    print(f"  values: {result.head().to_dict('records')}")

    return result

# Patch
SQLiteBackend._fetch_from_cursor = instrumented_fetch

# Run test
print("=" * 80)
print("RUNNING INSTRUMENTED TEST")
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
print(f"Values: {result['result'].tolist()}")

# Restore
SQLiteBackend._fetch_from_cursor = original_fetch

con.con.close()
