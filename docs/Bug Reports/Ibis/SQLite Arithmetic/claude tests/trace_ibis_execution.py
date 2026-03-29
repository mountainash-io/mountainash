"""
Trace through Ibis execution to find where rounding occurs.
"""
import ibis
import pandas as pd
import sqlite3

# Monkey-patch to trace execution
original_from_records = pd.DataFrame.from_records
original_convert_table = None

def traced_from_records(*args, **kwargs):
    result = original_from_records(*args, **kwargs)
    print(f"\n[TRACE] pd.DataFrame.from_records called")
    print(f"  Result shape: {result.shape}")
    if 'result' in result.columns and len(result) > 0:
        print(f"  result[1] value: {result['result'].iloc[1] if len(result) > 1 else 'N/A'}")
        print(f"  result[1] dtype: {result['result'].dtype}")
    return result

pd.DataFrame.from_records = traced_from_records

# Import after monkey-patching
from ibis.backends.sqlite.converter import SQLitePandasData

original_convert_table = SQLitePandasData.convert_table.__func__

@classmethod
def traced_convert_table(cls, df, schema):
    print(f"\n[TRACE] SQLitePandasData.convert_table called")
    print(f"  Input df shape: {df.shape}")
    if 'result' in df.columns and len(df) > 0:
        print(f"  Input result[1]: {df['result'].iloc[1] if len(df) > 1 else 'N/A'}")

    result = original_convert_table(cls, df, schema)

    print(f"  Output df shape: {result.shape}")
    if 'result' in result.columns and len(result) > 0:
        print(f"  Output result[1]: {result['result'].iloc[1] if len(result) > 1 else 'N/A'}")
    return result

SQLitePandasData.convert_table = traced_convert_table

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
print(f"Result:\n{result}")
print(f"result[1]: {result['result'].iloc[1]}")

# Restore
pd.DataFrame.from_records = original_from_records
