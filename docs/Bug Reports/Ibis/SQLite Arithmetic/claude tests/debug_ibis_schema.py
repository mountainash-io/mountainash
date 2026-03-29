"""
Debug what schema Ibis infers for the arithmetic expression.
"""
import ibis
import pandas as pd

df = pd.DataFrame({
    'a': [10, 20, 30],
    'b': [2, 3, 4],
    'c': [5, 10, 15]
})

con = ibis.sqlite.connect()
t = con.create_table('test', df)

# Create the expression
expr = (t.a + t.b) * t.c - t.a / t.b

# Check the inferred type
print("=" * 80)
print("EXPRESSION TYPE INFERENCE")
print("=" * 80)
print(f"Expression: (a + b) * c - a / b")
print(f"Inferred type: {expr.type()}")
print(f"Type class: {expr.type().__class__.__name__}")

# Check the table schema after selection
table_expr = t.select(expr.name('result'))
print(f"\nTable schema: {table_expr.schema()}")
print(f"Result column type: {table_expr.schema()['result']}")

# Check individual component types
print("\n" + "=" * 80)
print("COMPONENT TYPE INFERENCE")
print("=" * 80)
print(f"a type: {t.a.type()}")
print(f"b type: {t.b.type()}")
print(f"c type: {t.c.type()}")
print(f"a + b type: {(t.a + t.b).type()}")
print(f"(a + b) * c type: {((t.a + t.b) * t.c).type()}")
print(f"a / b type: {(t.a / t.b).type()}")
print(f"Full expression type: {expr.type()}")

# Now let's see what the converter does
from ibis.formats.pandas import PandasData, PandasType

schema = table_expr.schema()
result_dtype = schema['result']
pandas_type = PandasType.from_ibis(result_dtype)

print("\n" + "=" * 80)
print("PANDAS TYPE CONVERSION")
print("=" * 80)
print(f"Ibis dtype: {result_dtype}")
print(f"Pandas type from Ibis: {pandas_type}")

# Test the conversion manually
import numpy as np

print("\n" + "=" * 80)
print("MANUAL CONVERSION TEST")
print("=" * 80)

# Create a Series with the correct value
test_series = pd.Series([223.33333333333334], dtype='float64')
print(f"Original Series: {test_series[0]}")
print(f"Original dtype: {test_series.dtype}")

# Try converting to the pandas_type
converted = test_series.astype(pandas_type)
print(f"After astype({pandas_type}): {converted[0]}")
print(f"Converted dtype: {converted.dtype}")
