"""
Core conversion utilities for mountainash-dataframes.

This module provides converters for transforming data between backends:
- series: Convert series/arrays between Polars, pandas, PyArrow, Narwhals

For DataFrame conversions, use DataFrameSystemFactory directly:
    from mountainash.dataframes.core.dataframe_system import DataFrameSystemFactory
    system = DataFrameSystemFactory.get_system(df)
    polars_df = system.to_polars(df)
"""

from __future__ import annotations

from .series import SeriesConverter, SeriesBackend

__all__ = [
    "SeriesConverter",
    "SeriesBackend",
]
