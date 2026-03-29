import ibis
import ibis.selectors as s
import polars as pl
import pandas as pd


ibis.set_backend('polars')
polars_backend = ibis.polars.connect()
sqlite_backend = ibis.sqlite.connect()
duckdb_backend = ibis.duckdb.connect()

# Create base table
pl_df = pl.DataFrame({'base': [2], 'exp': [8]})

#ibis backend tables
df_polars = polars_backend.create_table('df_polars', pl_df)
df_sqlite = sqlite_backend.create_table('pl_df', pl_df)
df_duckdb = duckdb_backend.create_table('pl_df', pl_df)

# Expression definitions
lit_base = ibis.literal(2)
lit_exp = ibis.literal(8)

# Build the results
# Polars - will fail with literals on the LHS as they are cast to Int8
polars_results = df_polars.select(
    ibis.literal("polars").name("backend"),
    lit_base.pow(df_polars.exp).name("lit_base**col_exp"),
    df_polars.base.pow(lit_exp).name("col_base**lit_exp"),
    lit_base.pow(lit_exp).name("lit_base**lit_exp"),
    df_polars.base.pow(df_polars.exp).name("col_base**col_exp"),
).execute()

# SQLite - all correct
sqlite_results = df_sqlite.select(
    ibis.literal("sqlite").name("backend"),
    lit_base.pow(df_sqlite.exp).name("lit_base**col_exp"),
    df_sqlite.base.pow(lit_exp).name("col_base**lit_exp"),
    lit_base.pow(lit_exp).name("lit_base**lit_exp"),
    df_sqlite.base.pow(df_sqlite.exp).name("col_base**col_exp"),
).execute()

# DuckDB - all correct
duckdb_results = df_duckdb.select(
    ibis.literal("duckdb").name("backend"),
    lit_base.pow(df_duckdb.exp).name("lit_base**col_exp"),
    df_duckdb.base.pow(lit_exp).name("col_base**lit_exp"),
    lit_base.pow(lit_exp).name("lit_base**lit_exp"),
    df_duckdb.base.pow(df_duckdb.exp).name("col_base**col_exp"),
).execute()

results = pd.concat([polars_results, duckdb_results, sqlite_results])

print(results.to_markdown(index=False))
