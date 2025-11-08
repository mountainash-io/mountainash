"""
Final comprehensive trace without consuming cursor rows.
"""
import ibis
import pandas as pd

# Monkey-patch pd.DataFrame.from_records to see what it receives
original_from_records = pd.DataFrame.from_records

def traced_from_records(data, **kwargs):
    print(f"\n[TRACE] pd.DataFrame.from_records called")
    print(f"  data type: {type(data)}")
    print(f"  kwargs: {kwargs}")

    # Convert to list to inspect without consuming
    if hasattr(data, '__iter__') and not isinstance(data, (list, tuple)):
        data_list = list(data)
        print(f"  data (as list): {data_list[:5]}")  # First 5 rows
        if data_list:
            print(f"  first row: {data_list[0]}")
            print(f"  first row types: {[type(v) for v in data_list[0]]}")
        # Use the list for creating DataFrame
        data = data_list

    result = original_from_records(data, **kwargs)
    print(f"  result shape: {result.shape}")
    print(f"  result dtypes: {result.dtypes.to_dict()}")
    if len(result) > 0:
        print(f"  result first 3 values: {result.iloc[:3].to_dict('records')}")
    return result

pd.DataFrame.from_records = traced_from_records

# Run the test
print("=" * 80)
print("RUNNING COMPREHENSIVE TRACE")
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
print(f"Dtype: {result['result'].dtype}")

# Restore
pd.DataFrame.from_records = original_from_records

con.con.close()
