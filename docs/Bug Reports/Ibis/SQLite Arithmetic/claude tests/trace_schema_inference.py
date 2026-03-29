"""
Trace what schema is being inferred and passed to convert_table.
"""
import ibis
import pandas as pd

# Monkey-patch to trace schema
from ibis.backends.sqlite.converter import SQLitePandasData

original_convert_table = SQLitePandasData.convert_table.__func__

@classmethod
def traced_convert_table(cls, df, schema):
    print(f"\n[TRACE] SQLitePandasData.convert_table called")
    print(f"  Schema: {schema}")
    for name, dtype in schema.items():
        print(f"    {name}: {dtype} (class: {dtype.__class__.__name__})")
    print(f"  Input df dtypes:")
    for col in df.columns:
        print(f"    {col}: {df[col].dtype}")
    print(f"  Input df values (first 3 rows):")
    print(f"    {df.head(3).to_dict('records')}")

    result = original_convert_table(cls, df, schema)

    print(f"  Output df dtypes:")
    for col in result.columns:
        print(f"    {col}: {result[col].dtype}")
    print(f"  Output df values (first 3 rows):")
    print(f"    {result.head(3).to_dict('records')}")
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
table_expr = t.select(expr.name('result'))

# Check the schema that Ibis infers
print("\nInferred schema for expression:")
print(f"  {table_expr.schema()}")

result = table_expr.execute()

print("\n" + "=" * 80)
print("FINAL RESULT")
print("=" * 80)
print(f"Result:\n{result}")

# Restore
SQLitePandasData.convert_table = original_convert_table

con.con.close()
