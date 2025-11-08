import ibis
import pandas as pd

# Test data with negative operands
test_cases = [
    (-10, 3),
    (10, -3),
    (-10, -3),
    (-17, 4),
    (17, -4),
]

print("=== Expected (Python Modulo) ===")
for dividend, divisor in test_cases:
    result = dividend % divisor
    print(f"{dividend:3d} % {divisor:3d} = {result:3d}")

df = pd.DataFrame(test_cases, columns=['dividend', 'divisor'])

# Test each backend
backends = []

# SQLite
try:
    con_sqlite = ibis.sqlite.connect()
    t_sqlite = con_sqlite.create_table('test_sqlite', df)
    result = t_sqlite.select(
        (t_sqlite.dividend % t_sqlite.divisor).name('result')
    ).execute()['result'].tolist()
    backends.append(('SQLite', result))
except Exception as e:
    backends.append(('SQLite', f'Error: {e}'))

# DuckDB
try:
    con_duckdb = ibis.duckdb.connect()
    t_duckdb = con_duckdb.create_table('test_duckdb', df)
    result = t_duckdb.select(
        (t_duckdb.dividend % t_duckdb.divisor).name('result')
    ).execute()['result'].tolist()
    backends.append(('DuckDB', result))
except Exception as e:
    backends.append(('DuckDB', f'Error: {e}'))

# Polars
try:
    con_polars = ibis.polars.connect()
    t_polars = con_polars.create_table('test_polars', df)
    result = t_polars.select(
        (t_polars.dividend % t_polars.divisor).name('result')
    ).execute()['result'].tolist()
    backends.append(('Polars', result))
except Exception as e:
    backends.append(('Polars', f'Error: {e}'))

# Pandas
try:
    con_pandas = ibis.pandas.connect()
    t_pandas = con_pandas.create_table('test_pandas', df)
    result = t_pandas.select(
        (t_pandas.dividend % t_pandas.divisor).name('result')
    ).execute()['result'].tolist()
    backends.append(('Pandas', result))
except Exception as e:
    backends.append(('Pandas', f'Error: {e}'))

# Print results
print("\n=== Backend Results ===")
expected = [dividend % divisor for dividend, divisor in test_cases]
print(f"Expected:  {expected}")
for backend_name, result in backends:
    if isinstance(result, str):
        print(f"{backend_name:8s}: {result}")
    else:
        match = "✓" if result == expected else "✗"
        print(f"{backend_name:8s}: {result} {match}")

# Check which match Python semantics
print("\n=== Summary ===")
for backend_name, result in backends:
    if isinstance(result, list) and result == expected:
        print(f"✓ {backend_name} correctly implements Python modulo")
    elif isinstance(result, list):
        print(f"✗ {backend_name} implements remainder (not modulo)")
    else:
        print(f"? {backend_name} failed to test")
