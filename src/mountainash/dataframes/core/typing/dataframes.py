"""
DataFrame type aliases and detection utilities.

Type aliases and guards are imported from mountainash.core.types (single source of truth).
This module re-exports them and adds dataframes-specific callable type aliases.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, Union, Protocol, Any
from typing_extensions import TypeAlias, TypeGuard
from collections.abc import Sequence, Mapping, Callable

# Re-export all shared types from core
from mountainash.core.types import (
    # Runtime modules (needed for callable type aliases below)
    pd, pl, pa, ir, ibis, nw,
    # DataFrame type aliases
    PandasFrame,
    PolarsFrame,
    PolarsLazyFrame,
    PyArrowTable,
    IbisTable,
    IbisBaseBackend,
    IbisSchema,
    NarwhalsFrame,
    NarwhalsLazyFrame,
    # Expression type aliases
    PolarsExpr,
    IbisExpr,
    NarwhalsExpr,
    # Series type aliases
    PandasSeries,
    PolarsSeries,
    NarwhalsSeries,
    PyArrowArray,
    # Composite unions
    PolarsFrameTypes,
    NarwhalsFrameTypes,
    SupportedDataFrames,
    SupportedExpressions,
    SupportedSeries,
    # Type variables
    DataFrameT,
    ExpressionT,
    SeriesT,
    # Protocols
    DataFrameLike,
    LazyFrameLike,
    ExpressionLike,
    # Column types
    ColumnTypes,
    ColumnMapping,
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


# ============================================================================
# Callable Type Aliases (dataframes-specific)
# ============================================================================

if TYPE_CHECKING:
    DataFrameTransform: TypeAlias = Callable[[DataFrameT], DataFrameT]
    ExpressionBuilder: TypeAlias = Callable[[str], ExpressionT]
    FilterPredicate: TypeAlias = Callable[[DataFrameT], DataFrameT]
