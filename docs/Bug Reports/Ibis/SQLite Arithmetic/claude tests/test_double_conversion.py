"""
Test if double conversion is the issue.
"""
import pandas as pd
from ibis.formats.pandas import PandasData
import ibis.expr.schema as sch

# Create a DataFrame with the correct float values
df = pd.DataFrame({
    'result': [55.0, 223.33333333333334, 502.5]
})

print("=" * 80)
print("ORIGINAL DATAFRAME")
print("=" * 80)
print(f"Values: {df['result'].tolist()}")
print(f"Dtype: {df['result'].dtype}")

# Create a schema (float64)
schema = sch.Schema({'result': 'float64'})

# Convert once
print("\n" + "=" * 80)
print("AFTER FIRST convert_table()")
print("=" * 80)
df_converted_1 = PandasData.convert_table(df, schema)
print(f"Values: {df_converted_1['result'].tolist()}")
print(f"Dtype: {df_converted_1['result'].dtype}")

# Convert twice
print("\n" + "=" * 80)
print("AFTER SECOND convert_table()")
print("=" * 80)
df_converted_2 = PandasData.convert_table(df_converted_1, schema)
print(f"Values: {df_converted_2['result'].tolist()}")
print(f"Dtype: {df_converted_2['result'].dtype}")
