"""
Backend implementations for mountainash-dataframes.

Three supported backends:
- polars/: Native Polars DataFrame support (primary backend)
- narwhals/: Universal adapter (pandas, pyarrow, cudf via Narwhals)
- ibis/: SQL backend support (DuckDB, Postgres, BigQuery, etc.)

Each backend provides a DataFrameSystem implementation that is auto-registered
with the DataFrameSystemFactory via the @register_dataframe_system decorator.

Usage:
    from mountainash.dataframes.core.dataframe_system import DataFrameSystemFactory

    # Auto-detect backend and get system
    system = DataFrameSystemFactory.get_system(df)

    # Use any operation
    pandas_df = system.to_pandas(df)
"""

# Import backends to trigger registration (lazy via submodule access)
import lazy_loader

__getattr__, __dir__, __all__ = lazy_loader.attach(
    __name__,
    submodules=["polars", "narwhals", "ibis"],
    submod_attrs={},
)
