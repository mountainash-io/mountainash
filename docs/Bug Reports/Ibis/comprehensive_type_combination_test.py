#!/usr/bin/env python3
"""
Comprehensive test: all backends, all type combinations, all operators.
Minimal comments - code is documentation.
"""

import ibis
import polars as pl
import pandas as pd

print("=" * 80)
print("PART 1: PURE POLARS (DIRECT API)")
print("=" * 80)

df = pl.DataFrame({'x': [2], 'y': [10], 'z': [64]})

# Literals
lit_2 = pl.lit(2)
lit_2_i8 = pl.lit(2, dtype=pl.Int8)
lit_10 = pl.lit(10)
lit_10_i8 = pl.lit(10, dtype=pl.Int8)
lit_64 = pl.lit(64)
lit_64_i8 = pl.lit(64, dtype=pl.Int8)

# Columns
col_x = pl.col('x')
col_x_i8 = pl.col('x').cast(pl.Int8)
col_y = pl.col('y')
col_y_i8 = pl.col('y').cast(pl.Int8)
col_z = pl.col('z')
col_z_i8 = pl.col('z').cast(pl.Int8)

print("\nPOWER: 2^10 = 1024")
power_results = df.select(
    # LHS literal (untyped/typed) ** RHS column (int64/int8)
    lit_2.pow(col_y).alias("lit_2 ** col_y"),
    lit_2_i8.pow(col_y).alias("lit_2_i8 ** col_y"),
    lit_2.pow(col_y_i8).alias("lit_2 ** col_y_i8"),
    lit_2_i8.pow(col_y_i8).alias("lit_2_i8 ** col_y_i8"),

    # LHS column (int64/int8) ** RHS literal (untyped/typed)
    col_x.pow(lit_10).alias("col_x ** lit_10"),
    col_x.pow(lit_10_i8).alias("col_x ** lit_10_i8"),
    col_x_i8.pow(lit_10).alias("col_x_i8 ** lit_10"),
    col_x_i8.pow(lit_10_i8).alias("col_x_i8 ** lit_10_i8"),

    # LHS literal ** RHS literal
    lit_2.pow(lit_10).alias("lit_2 ** lit_10"),
    lit_2_i8.pow(lit_10).alias("lit_2_i8 ** lit_10"),
    lit_2.pow(lit_10_i8).alias("lit_2 ** lit_10_i8"),
    lit_2_i8.pow(lit_10_i8).alias("lit_2_i8 ** lit_10_i8"),

    # LHS column ** RHS column
    col_x.pow(col_y).alias("col_x ** col_y"),
    col_x_i8.pow(col_y).alias("col_x_i8 ** col_y"),
    col_x.pow(col_y_i8).alias("col_x ** col_y_i8"),
    col_x_i8.pow(col_y_i8).alias("col_x_i8 ** col_y_i8"),
).unpivot(variable_name="case", value_name="result")

print(power_results.to_pandas().to_markdown(index=False))

print("\nMULTIPLICATION: 64*64 = 4096")
mult_results = df.select(
    # LHS literal (untyped/typed) * RHS column (int64/int8)
    (lit_64 * col_z).alias("lit_64 * col_z"),
    (lit_64_i8 * col_z).alias("lit_64_i8 * col_z"),
    (lit_64 * col_z_i8).alias("lit_64 * col_z_i8"),
    (lit_64_i8 * col_z_i8).alias("lit_64_i8 * col_z_i8"),

    # LHS column (int64/int8) * RHS literal (untyped/typed)
    (col_z * lit_64).alias("col_z * lit_64"),
    (col_z * lit_64_i8).alias("col_z * lit_64_i8"),
    (col_z_i8 * lit_64).alias("col_z_i8 * lit_64"),
    (col_z_i8 * lit_64_i8).alias("col_z_i8 * lit_64_i8"),

    # LHS literal * RHS literal
    (lit_64 * lit_64).alias("lit_64 * lit_64"),
    (lit_64_i8 * lit_64).alias("lit_64_i8 * lit_64"),
    (lit_64 * lit_64_i8).alias("lit_64 * lit_64_i8"),
    (lit_64_i8 * lit_64_i8).alias("lit_64_i8 * lit_64_i8"),

    # LHS column * RHS column
    (col_z * col_z).alias("col_z * col_z"),
    (col_z_i8 * col_z).alias("col_z_i8 * col_z"),
    (col_z * col_z_i8).alias("col_z * col_z_i8"),
    (col_z_i8 * col_z_i8).alias("col_z_i8 * col_z_i8"),
).unpivot(variable_name="case", value_name="result")

print(mult_results.to_pandas().to_markdown(index=False))

print("\n" + "=" * 80)
print("PART 2: IBIS BACKENDS")
print("=" * 80)

polars_backend = ibis.polars.connect()
duckdb_backend = ibis.duckdb.connect()
sqlite_backend = ibis.sqlite.connect()

pl_df = pl.DataFrame({'x': [2], 'y': [10], 'z': [64]})
pl_df_i8 = pl.DataFrame({
    'x': pl.Series([2], dtype=pl.Int8),
    'y': pl.Series([10], dtype=pl.Int8),
    'z': pl.Series([64], dtype=pl.Int8),
})

# Tables with int64 columns
t_polars = polars_backend.create_table('t_polars', pl_df)
t_duckdb = duckdb_backend.create_table('t_duckdb', pl_df)
t_sqlite = sqlite_backend.create_table('t_sqlite', pl_df)

# Tables with int8 columns
t_polars_i8 = polars_backend.create_table('t_polars_i8', pl_df_i8)
t_duckdb_i8 = duckdb_backend.create_table('t_duckdb_i8', pl_df_i8)
t_sqlite_i8 = sqlite_backend.create_table('t_sqlite_i8', pl_df_i8)

# Literals
lit_2 = ibis.literal(2)
lit_10 = ibis.literal(10)
lit_64 = ibis.literal(64)

print("\nPOWER: Ibis literal (infers int8) ** column")

def safe_execute(expr, index=None):
    try:
        result = expr.execute()
        return result[index] if index is not None else result
    except Exception as e:
        return f"ERROR: {type(e).__name__}"

def count_failures(df):
    return ((df['result'] == 0) | df['result'].astype(str).str.startswith('ERROR')).sum()

def test_backend_power(backend_name, table, table_i8):
    results = []

    results.append({
        'backend': backend_name,
        'case': 'lit_2 ** col_y(i64)',
        'result': safe_execute(lit_2 ** table.y, 0)
    })

    results.append({
        'backend': backend_name,
        'case': 'lit_2 ** col_y(i8)',
        'result': safe_execute(lit_2 ** table_i8.y, 0)
    })

    results.append({
        'backend': backend_name,
        'case': 'col_x(i64) ** lit_10',
        'result': safe_execute(table.x ** lit_10, 0)
    })

    results.append({
        'backend': backend_name,
        'case': 'col_x(i8) ** lit_10',
        'result': safe_execute(table_i8.x ** lit_10, 0)
    })

    results.append({
        'backend': backend_name,
        'case': 'lit_2 ** lit_10',
        'result': safe_execute(lit_2 ** lit_10)
    })

    results.append({
        'backend': backend_name,
        'case': 'col_x(i64) ** col_y(i64)',
        'result': safe_execute(table.x ** table.y, 0)
    })

    results.append({
        'backend': backend_name,
        'case': 'col_x(i8) ** col_y(i8)',
        'result': safe_execute(table_i8.x ** table_i8.y, 0)
    })

    return pd.DataFrame(results)

power_polars = test_backend_power('ibis-polars', t_polars, t_polars_i8)
power_duckdb = test_backend_power('ibis-duckdb', t_duckdb, t_duckdb_i8)
power_sqlite = test_backend_power('ibis-sqlite', t_sqlite, t_sqlite_i8)

power_all = pd.concat([power_polars, power_duckdb, power_sqlite])
print(power_all.to_markdown(index=False))

print("\nMULTIPLICATION: Ibis literal (infers int8) * column")

def test_backend_mult(backend_name, table, table_i8):
    results = []

    results.append({
        'backend': backend_name,
        'case': 'lit_64 * col_z(i64)',
        'result': safe_execute(lit_64 * table.z, 0)
    })

    results.append({
        'backend': backend_name,
        'case': 'lit_64 * col_z(i8)',
        'result': safe_execute(lit_64 * table_i8.z, 0)
    })

    results.append({
        'backend': backend_name,
        'case': 'col_z(i64) * lit_64',
        'result': safe_execute(table.z * lit_64, 0)
    })

    results.append({
        'backend': backend_name,
        'case': 'col_z(i8) * lit_64',
        'result': safe_execute(table_i8.z * lit_64, 0)
    })

    results.append({
        'backend': backend_name,
        'case': 'lit_64 * lit_64',
        'result': safe_execute(lit_64 * lit_64)
    })

    results.append({
        'backend': backend_name,
        'case': 'col_z(i64) * col_z(i64)',
        'result': safe_execute(table.z * table.z, 0)
    })

    results.append({
        'backend': backend_name,
        'case': 'col_z(i8) * col_z(i8)',
        'result': safe_execute(table_i8.z * table_i8.z, 0)
    })

    return pd.DataFrame(results)

mult_polars = test_backend_mult('ibis-polars', t_polars, t_polars_i8)
mult_duckdb = test_backend_mult('ibis-duckdb', t_duckdb, t_duckdb_i8)
mult_sqlite = test_backend_mult('ibis-sqlite', t_sqlite, t_sqlite_i8)

mult_all = pd.concat([mult_polars, mult_duckdb, mult_sqlite])
print(mult_all.to_markdown(index=False))

print("\n" + "=" * 80)
print("PART 3: RAW PYTHON NUMBERS vs IBIS LITERALS")
print("=" * 80)

print("\nRaw numbers are automatically wrapped in ibis.literal()")
print("Testing on ibis-polars backend:\n")

raw_vs_lit = pd.DataFrame([
    {'case': 'raw_2 ** col_y(i64)', 'result': safe_execute(2 ** t_polars.y, 0)},
    {'case': 'lit_2 ** col_y(i64)', 'result': safe_execute(lit_2 ** t_polars.y, 0)},
    {'case': 'raw_64 * col_z(i64)', 'result': safe_execute(64 * t_polars.z, 0)},
    {'case': 'lit_64 * col_z(i64)', 'result': safe_execute(lit_64 * t_polars.z, 0)},
])

print(raw_vs_lit.to_markdown(index=False))

print("\n" + "=" * 80)
print("PART 4: EXPLICIT INT64 CASTING (THE WORKAROUND)")
print("=" * 80)

lit_2_i64_cast = ibis.literal(2).cast('int64')
lit_2_i64_type = ibis.literal(2, type='int64')
lit_64_i64_cast = ibis.literal(64).cast('int64')
lit_64_i64_type = ibis.literal(64, type='int64')

print("\nPOWER: Explicit int64 casting")

cast_power_results = []
for backend_name, table, table_i8 in [
    ('ibis-polars', t_polars, t_polars_i8),
    ('ibis-duckdb', t_duckdb, t_duckdb_i8),
    ('ibis-sqlite', t_sqlite, t_sqlite_i8),
]:
    # Original (fails with Polars)
    cast_power_results.append({
        'backend': backend_name,
        'case': 'lit_2(i8) ** col_y(i64)',
        'result': safe_execute(lit_2 ** table.y, 0)
    })

    # Cast to int64 (workaround)
    cast_power_results.append({
        'backend': backend_name,
        'case': 'lit_2.cast(i64) ** col_y(i64)',
        'result': safe_execute(lit_2_i64_cast ** table.y, 0)
    })

    # Type specified as int64 (alternative workaround)
    cast_power_results.append({
        'backend': backend_name,
        'case': 'lit_2(type=i64) ** col_y(i64)',
        'result': safe_execute(lit_2_i64_type ** table.y, 0)
    })

    # With int8 column
    cast_power_results.append({
        'backend': backend_name,
        'case': 'lit_2(i8) ** col_y(i8)',
        'result': safe_execute(lit_2 ** table_i8.y, 0)
    })

    cast_power_results.append({
        'backend': backend_name,
        'case': 'lit_2.cast(i64) ** col_y(i8)',
        'result': safe_execute(lit_2_i64_cast ** table_i8.y, 0)
    })

cast_power_df = pd.DataFrame(cast_power_results)
print(cast_power_df.to_markdown(index=False))

print("\nMULTIPLICATION: Explicit int64 casting")

cast_mult_results = []
for backend_name, table, table_i8 in [
    ('ibis-polars', t_polars, t_polars_i8),
    ('ibis-duckdb', t_duckdb, t_duckdb_i8),
    ('ibis-sqlite', t_sqlite, t_sqlite_i8),
]:
    # Original (may fail with int8 columns)
    cast_mult_results.append({
        'backend': backend_name,
        'case': 'lit_64(i8) * col_z(i64)',
        'result': safe_execute(lit_64 * table.z, 0)
    })

    # Cast to int64 (workaround)
    cast_mult_results.append({
        'backend': backend_name,
        'case': 'lit_64.cast(i64) * col_z(i64)',
        'result': safe_execute(lit_64_i64_cast * table.z, 0)
    })

    # With int8 column (fails without cast)
    cast_mult_results.append({
        'backend': backend_name,
        'case': 'lit_64(i8) * col_z(i8)',
        'result': safe_execute(lit_64 * table_i8.z, 0)
    })

    cast_mult_results.append({
        'backend': backend_name,
        'case': 'lit_64.cast(i64) * col_z(i8)',
        'result': safe_execute(lit_64_i64_cast * table_i8.z, 0)
    })

cast_mult_df = pd.DataFrame(cast_mult_results)
print(cast_mult_df.to_markdown(index=False))

print("\n" + "=" * 80)
print("CAST WORKAROUND ANALYSIS")
print("=" * 80)

cast_power_failures = count_failures(cast_power_df)
cast_mult_failures = count_failures(cast_mult_df)

print(f"\nOriginal approach failures:")
print(f"  Power: {(cast_power_df['case'].str.contains('lit_2\\(i8\\)') & ((cast_power_df['result'] == 0) | cast_power_df['result'].astype(str).str.startswith('ERROR'))).sum()}")
print(f"  Mult: {(cast_mult_df['case'].str.contains('lit_64\\(i8\\)') & ((cast_mult_df['result'] == 0) | cast_mult_df['result'].astype(str).str.startswith('ERROR'))).sum()}")

print(f"\nWith .cast(int64) workaround failures:")
print(f"  Power: {(cast_power_df['case'].str.contains('cast.*i64') & ((cast_power_df['result'] == 0) | cast_power_df['result'].astype(str).str.startswith('ERROR'))).sum()}")
print(f"  Mult: {(cast_mult_df['case'].str.contains('cast.*i64') & ((cast_mult_df['result'] == 0) | cast_mult_df['result'].astype(str).str.startswith('ERROR'))).sum()}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

summary = []

# Count failures in each test (0 or ERROR)
polars_power_fail = count_failures(power_polars)
duckdb_power_fail = count_failures(power_duckdb)
sqlite_power_fail = count_failures(power_sqlite)

polars_mult_fail = count_failures(mult_polars)
duckdb_mult_fail = count_failures(mult_duckdb)
sqlite_mult_fail = count_failures(mult_sqlite)

summary_data = pd.DataFrame([
    {'Backend': 'Pure Polars', 'Power Failures': (power_results['result'] == 0).sum(), 'Mult Failures': (mult_results['result'] == 0).sum()},
    {'Backend': 'Ibis-Polars', 'Power Failures': polars_power_fail, 'Mult Failures': polars_mult_fail},
    {'Backend': 'Ibis-DuckDB', 'Power Failures': duckdb_power_fail, 'Mult Failures': duckdb_mult_fail},
    {'Backend': 'Ibis-SQLite', 'Power Failures': sqlite_power_fail, 'Mult Failures': sqlite_mult_fail},
])

print(summary_data.to_markdown(index=False))

print("\nExpected results: 2^10=1024, 64*64=4096")
print("Failure count = cases returning 0 (overflow) or ERROR (exception)")
