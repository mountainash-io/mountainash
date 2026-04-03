"""
Test pandas dtype inference with float values that could be integers.
"""
import pandas as pd

# Test 1: Values where first is a "clean" float
print("=" * 80)
print("TEST 1: First value is 55.0 (can be int)")
print("=" * 80)
data1 = [(55.0,), (223.33333333333334,), (502.5,)]
df1 = pd.DataFrame.from_records(data1, columns=['result'], coerce_float=True)
print(f"Data: {data1}")
print(f"Inferred dtype: {df1['result'].dtype}")
print(f"Values: {df1['result'].tolist()}")

# Test 2: Same but without coerce_float
print("\n" + "=" * 80)
print("TEST 2: Same but coerce_float=False")
print("=" * 80)
df2 = pd.DataFrame.from_records(data1, columns=['result'], coerce_float=False)
print(f"Inferred dtype: {df2['result'].dtype}")
print(f"Values: {df2['result'].tolist()}")

# Test 3: Force DataFrame to read all data before inferring
print("\n" + "=" * 80)
print("TEST 3: Create from list (not iterator)")
print("=" * 80)
df3 = pd.DataFrame(data1, columns=['result'])
print(f"Inferred dtype: {df3['result'].dtype}")
print(f"Values: {df3['result'].tolist()}")

# Test 4: Simulating cursor behavior - iterator
print("\n" + "=" * 80)
print("TEST 4: Iterator that yields tuples")
print("=" * 80)

def row_generator():
    yield (55.0,)
    yield (223.33333333333334,)
    yield (502.5,)

df4 = pd.DataFrame.from_records(row_generator(), columns=['result'], coerce_float=True)
print(f"Inferred dtype: {df4['result'].dtype}")
print(f"Values: {df4['result'].tolist()}")

# Test 5: Iterator without coerce_float
print("\n" + "=" * 80)
print("TEST 5: Iterator without coerce_float")
print("=" * 80)

def row_generator2():
    yield (55.0,)
    yield (223.33333333333334,)
    yield (502.5,)

df5 = pd.DataFrame.from_records(row_generator2(), columns=['result'], coerce_float=False)
print(f"Inferred dtype: {df5['result'].dtype}")
print(f"Values: {df5['result'].tolist()}")

# Test 6: What if we explicitly set dtype?
print("\n" + "=" * 80)
print("TEST 6: DataFrame with explicit dtype='float64'")
print("=" * 80)
df6 = pd.DataFrame(data1, columns=['result'], dtype='float64')
print(f"Inferred dtype: {df6['result'].dtype}")
print(f"Values: {df6['result'].tolist()}")
