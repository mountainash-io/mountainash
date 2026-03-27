"""
Sophisticated typing system for mountainash-dataframes.

This module provides type definitions using TYPE_CHECKING to avoid runtime imports
while maintaining full type safety. Inspired by narwhals' typing architecture.

Submodules:
- dataframes: DataFrame type aliases and detection
- expressions: Expression type aliases and detection
- series: Series type aliases and detection
- python_data: Python data type aliases
"""

from __future__ import annotations


from .dataframes import (
    PandasFrame,
    PolarsFrame,
    PolarsLazyFrame,
    PyArrowTable,
    IbisTable,
    NarwhalsFrame,
    NarwhalsLazyFrame,
    PolarsExpr,
    IbisExpr,
    NarwhalsExpr,
    PandasSeries,
    PolarsSeries,
    NarwhalsSeries,
    PyArrowArray,
    PolarsFrameTypes,
    NarwhalsFrameTypes,
    SupportedDataFrames,
    SupportedExpressions,
    SupportedSeries,
    # DataFrame type guards
    is_pandas_dataframe,
    is_polars_dataframe,
    is_polars_lazyframe,
    is_pyarrow_table,
    is_ibis_table,
    is_narwhals_dataframe,
    is_narwhals_lazyframe,
    is_supported_dataframe,
    detect_dataframe_backend_type,
)

from .expressions import (
    # Expression type guards
    is_polars_expression,
    is_narwhals_expression,
    is_ibis_expression,
    is_mountainash_expression,
    is_native_expression,
    is_supported_expression,
    detect_expression_backend,
)

from .series import (
    # Series type guards
    is_polars_series,
    is_pandas_series,
    is_narwhals_series,
    is_pyarrow_array,
    is_native_series,
    is_supported_series,
    detect_series_backend,
)

from .python_data import (
    PyListData,
    PyDictData,
    CollectionData,
    TupleData,
    NamedTupleData,
    IndexedData,
    SeriesDictData,
    SupportedPythonData,
    DataFrameOrPythonData,
)
# ============================================================================
# Export List
# ============================================================================

__all__ = [
    # Main type aliases
    "SupportedDataFrames",
    "SupportedExpressions",
    "SupportedSeries",
    # Backend-specific types - dataframes
    "PandasFrame",
    "PolarsFrame",
    "PolarsLazyFrame",
    "PyArrowTable",
    "IbisTable",
    "NarwhalsFrame",
    "NarwhalsLazyFrame",
    # Multi-types - dataframes
    "PolarsFrameTypes",
    "NarwhalsFrameTypes",
    # Backend-specific types - expressions
    "PolarsExpr",
    "IbisExpr",
    "NarwhalsExpr",
    # Backend-specific types - series
    "PandasSeries",
    "PolarsSeries",
    "NarwhalsSeries",
    "PyArrowArray",
    # Python data types
    "PyListData",
    "PyDictData",
    "CollectionData",
    "TupleData",
    "NamedTupleData",
    "IndexedData",
    "SeriesDictData",
    "SupportedPythonData",
    "DataFrameOrPythonData",
    # DataFrame type guards
    "is_pandas_dataframe",
    "is_polars_dataframe",
    "is_polars_lazyframe",
    "is_pyarrow_table",
    "is_ibis_table",
    "is_narwhals_dataframe",
    "is_narwhals_lazyframe",
    "is_supported_dataframe",
    "detect_dataframe_backend_type",
    # Expression type guards
    "is_polars_expression",
    "is_narwhals_expression",
    "is_ibis_expression",
    "is_mountainash_expression",
    "is_native_expression",
    "is_supported_expression",
    "detect_expression_backend",
    # Series type guards
    "is_polars_series",
    "is_pandas_series",
    "is_narwhals_series",
    "is_pyarrow_array",
    "is_native_series",
    "is_supported_series",
    "detect_series_backend",
]
