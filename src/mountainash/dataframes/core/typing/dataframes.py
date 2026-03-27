"""
Sophisticated typing system for mountainash-dataframes.

This module provides type definitions using TYPE_CHECKING to avoid runtime imports
while maintaining full type safety. Inspired by narwhals' typing architecture.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, Union, Protocol, Any
from typing_extensions import TypeAlias, TypeGuard
from collections.abc import Sequence, Mapping, Callable

if TYPE_CHECKING:
    import ibis as ibis
    import ibis.expr.types as ir
    import pandas as pd
    import polars as pl
    import pyarrow as pa
    import narwhals as nw
else:
    # Runtime fallback for optional imports
    # This enables runtime type introspection (e.g., Hamilton) while keeping dependencies optional
    import types

    # Pandas
    try:
        import pandas as pd
    except ImportError:
        pd = types.ModuleType('pandas')
        pd.DataFrame = Any
        pd.Series = Any

    # Polars
    try:
        import polars as pl
    except ImportError:
        pl = types.ModuleType('polars')
        pl.DataFrame = Any
        pl.LazyFrame = Any
        pl.Series = Any
        pl.Expr = Any

    # PyArrow
    try:
        import pyarrow as pa
    except ImportError:
        pa = types.ModuleType('pyarrow')
        pa.Table = Any
        pa.Array = Any

    # Ibis
    try:
        import ibis as ibis
        import ibis.expr.types as ir
    except ImportError:
        ibis = types.ModuleType('ibis')
        ibis.BaseBackend = Any
        ir = types.ModuleType('ibis.expr.types')
        ir.Table = Any
        ir.Expr = Any
        # Add to ibis module for ibis.expr.schema.Schema reference
        ibis.expr = types.ModuleType('ibis.expr')
        ibis.expr.schema = types.ModuleType('ibis.expr.schema')
        ibis.expr.schema.Schema = Any

    # Narwhals
    try:
        import narwhals as nw
    except ImportError:
        nw = types.ModuleType('narwhals')
        nw.DataFrame = Any
        nw.LazyFrame = Any
        nw.Series = Any
        nw.Expr = Any

# Historical note: Previous lazy loading approach (kept for reference)
# else:
#     ibis = lazy.load("ibis")
#     pd = lazy.load("pandas")
#     pl = lazy.load("polars")
#     pa = lazy.load("pyarrow")
#     nw = lazy.load("narwhals")
# ============================================================================
# Type Aliases for Each Backend
# ============================================================================

# Pandas types
PandasFrame: TypeAlias = pd.DataFrame
PandasSeries: TypeAlias = pd.Series

# Polars types
PolarsFrame: TypeAlias = pl.DataFrame
PolarsLazyFrame: TypeAlias = pl.LazyFrame
PolarsSeries: TypeAlias = pl.Series
PolarsExpr: TypeAlias = pl.Expr

# PyArrow types
PyArrowTable: TypeAlias = pa.Table
PyArrowArray: TypeAlias = pa.Array

# Ibis types
IbisTable: TypeAlias = ir.Table
IbisExpr: TypeAlias = ir.Expr
IbisBaseBackend: TypeAlias = ibis.BaseBackend
IbisSchema: TypeAlias = ibis.expr.schema.Schema


# Narwhals types
NarwhalsFrame: TypeAlias = nw.DataFrame
NarwhalsLazyFrame: TypeAlias = nw.LazyFrame
NarwhalsSeries: TypeAlias = nw.Series
NarwhalsExpr: TypeAlias = nw.Expr

# ============================================================================
# Composite Type Unions
# ============================================================================

# Backend-specific frame types
PolarsFrameTypes: TypeAlias = Union[PolarsFrame, PolarsLazyFrame]
NarwhalsFrameTypes: TypeAlias = Union[NarwhalsFrame, NarwhalsLazyFrame]

# Expression types across backends
SupportedExpressions: TypeAlias = Union[PolarsExpr, IbisExpr, NarwhalsExpr]

# Series types across backends
SupportedSeries: TypeAlias = Union[PandasSeries, PolarsSeries, NarwhalsSeries, PyArrowArray]

# Main union type for all supported dataframes
SupportedDataFrames: TypeAlias = Union[
    PandasFrame,
    PolarsFrame,
    PolarsLazyFrame,
    PyArrowTable,
    IbisTable,
    NarwhalsFrame,
    NarwhalsLazyFrame
]

# Legacy alias for backward compatibility
# SUPPORTED_DATAFRAMES: TypeAlias = SupportedDataFrames

# ============================================================================
# Generic Type Variables
# ============================================================================

# Standard type variables for dataframes
DataFrameT = TypeVar("DataFrameT", bound=SupportedDataFrames)
# DataFrameT_co = TypeVar("DataFrameT_co", bound=SupportedDataFrames, covariant=True)
# DataFrameT_contra = TypeVar("DataFrameT_contra", bound=SupportedDataFrames, contravariant=True)

# # Backend-specific type variables
# PandasT = TypeVar("PandasT", bound=PandasFrame)
# PandasT_co = TypeVar("PandasT_co", bound=PandasFrame, covariant=True)

# PolarsT = TypeVar("PolarsT", bound=PolarsFrameTypes)
# PolarsT_co = TypeVar("PolarsT_co", bound=PolarsFrameTypes, covariant=True)

# IbisT = TypeVar("IbisT", bound=IbisTable)
# IbisT_co = TypeVar("IbisT_co", bound=IbisTable, covariant=True)

# PyArrowT = TypeVar("PyArrowT", bound=PyArrowTable)
# PyArrowT_co = TypeVar("PyArrowT_co", bound=PyArrowTable, covariant=True)

# NarwhalsT = TypeVar("NarwhalsT", bound=NarwhalsFrameTypes)
# NarwhalsT_co = TypeVar("NarwhalsT_co", bound=NarwhalsFrameTypes, covariant=True)

# Expression type variables
ExpressionT = TypeVar("ExpressionT", bound=SupportedExpressions)
# ExpressionT_co = TypeVar("ExpressionT_co", bound=SupportedExpressions, covariant=True)

# Series type variables
SeriesT = TypeVar("SeriesT", bound=SupportedSeries)
# SeriesT_co = TypeVar("SeriesT_co", bound=SupportedSeries, covariant=True)

# ============================================================================
# Protocols for Structural Typing
# ============================================================================

class DataFrameLike(Protocol):
    """Protocol for dataframe-like objects with common interface."""

    @property
    def shape(self) -> tuple[int, int]:
        """Return (n_rows, n_columns) tuple."""
        ...

    @property
    def columns(self) -> Sequence[str]:
        """Return column names."""
        ...

    def __len__(self) -> int:
        """Return number of rows."""
        ...

class LazyFrameLike(Protocol):
    """Protocol for lazy dataframe-like objects."""

    def collect(self) -> DataFrameLike:
        """Materialize the lazy frame."""
        ...

    @property
    def columns(self) -> Sequence[str]:
        """Return column names."""
        ...

class ExpressionLike(Protocol):
    """Protocol for expression-like objects."""

    def alias(self, name: str) -> ExpressionLike:
        """Rename the expression."""
        ...

# ============================================================================
# Type Guards for Runtime Type Checking
# ============================================================================

def is_pandas_dataframe(obj: Any) -> TypeGuard[PandasFrame]:
    """Type guard for pandas DataFrames."""
    return type(obj).__module__.startswith("pandas") and type(obj).__name__ == "DataFrame"

def is_polars_dataframe(obj: Any) -> TypeGuard[PolarsFrame]:
    """Type guard for polars DataFrames."""
    return type(obj).__module__.startswith("polars") and type(obj).__name__ == "DataFrame"

def is_polars_lazyframe(obj: Any) -> TypeGuard[PolarsLazyFrame]:
    """Type guard for polars LazyFrames."""
    return type(obj).__module__.startswith("polars") and type(obj).__name__ == "LazyFrame"

def is_pyarrow_table(obj: Any) -> TypeGuard[PyArrowTable]:
    """Type guard for PyArrow Tables."""
    return type(obj).__module__.startswith("pyarrow") and type(obj).__name__ == "Table"

def is_ibis_table(obj: Any) -> TypeGuard[IbisTable]:
    """Type guard for Ibis Tables."""
    module = type(obj).__module__
    return "ibis" in module and hasattr(obj, "execute")

def is_narwhals_dataframe(obj: Any) -> TypeGuard[NarwhalsFrame]:
    """Type guard for Narwhals DataFrames."""
    return type(obj).__module__.startswith("narwhals") and type(obj).__name__ == "DataFrame"

def is_narwhals_lazyframe(obj: Any) -> TypeGuard[NarwhalsLazyFrame]:
    """Type guard for Narwhals LazyFrames."""
    return type(obj).__module__.startswith("narwhals") and type(obj).__name__ == "LazyFrame"

def is_supported_dataframe(obj: Any) -> TypeGuard[SupportedDataFrames]:
    """Type guard for any supported dataframe type."""
    return any([
        is_pandas_dataframe(obj),
        is_polars_dataframe(obj),
        is_polars_lazyframe(obj),
        is_pyarrow_table(obj),
        is_ibis_table(obj),
        is_narwhals_dataframe(obj),
        is_narwhals_lazyframe(obj),
    ])

# ============================================================================
# Backend Detection Utilities
# ============================================================================

def detect_dataframe_backend_type(obj: Any) -> str:
    """
    Detect the backend type of a dataframe object without importing libraries.

    Returns:
        Backend name: 'pandas', 'polars', 'pyarrow', 'ibis', 'narwhals'

    Raises:
        ValueError: If the object type is not recognized
    """
    if is_pandas_dataframe(obj):
        return "pandas"
    elif is_polars_dataframe(obj) or is_polars_lazyframe(obj):
        return "polars"
    elif is_pyarrow_table(obj):
        return "pyarrow"
    elif is_ibis_table(obj):
        return "ibis"
    elif is_narwhals_dataframe(obj) or is_narwhals_lazyframe(obj):
        return "narwhals"
    else:
        raise ValueError(f"Unknown dataframe type: {type(obj).__module__}.{type(obj).__name__}")

# ============================================================================
# Column Type Mappings
# ============================================================================

ColumnTypes: TypeAlias = Union[type, str]

if TYPE_CHECKING:
    ColumnMapping: TypeAlias = Mapping[str, ColumnTypes]
else:
    ColumnMapping: TypeAlias = "Mapping[str, ColumnTypes]"

# ============================================================================
# Callable Type Aliases for Functions
# ============================================================================

if TYPE_CHECKING:

    # DataFrame transformation functions
    DataFrameTransform: TypeAlias = Callable[[DataFrameT], DataFrameT]
    # DataFrameConverter: TypeAlias = Callable[[DataFrameT_co], DataFrameT]

    # Expression builder functions
    ExpressionBuilder: TypeAlias = Callable[[str], ExpressionT]

    # Filter functions
    FilterPredicate: TypeAlias = Callable[[DataFrameT], DataFrameT]

# ============================================================================
# Factory Input Type Aliases
# ============================================================================

# Input type aliases for factory specialization
# DataFrameFactoryInput: TypeAlias = SupportedDataFrames
# ExpressionFactoryInput: TypeAlias = SupportedExpressions
# PythonDataFactoryInput: TypeAlias = Any

# # Multi-input type aliases for special cases (like join operations)
# MultiDataFrameInput: TypeAlias = tuple[SupportedDataFrames, ...]

# # Factory input type constraints for BaseStrategyFactory
# FactoryInputT = TypeVar('FactoryInputT',
#                        DataFrameFactoryInput,
#                        ExpressionFactoryInput,
#                        PythonDataFactoryInput)


# ============================================================================
# Export List
# ============================================================================

# __all__ = [
#     # Main type aliases
#     "SupportedDataFrames",
#     "SupportedExpressions",
#     "SupportedSeries",

#     # Backend-specific types
#     "PandasFrame",
#     "PolarsFrame",
#     "PolarsLazyFrame",
#     "PyArrowTable",
#     "IbisTable",
#     "NarwhalsFrame",
#     "NarwhalsLazyFrame",

#     # Factory input type aliases
#     "DataFrameFactoryInput",
#     "ExpressionFactoryInput",
#     "PythonDataFactoryInput",
#     "MultiDataFrameInput",
#     "FactoryInputT",

#     # Type variables
#     "DataFrameT",
#     # "DataFrameT_co",
#     # "DataFrameT_contra",
#     # "PandasT",
#     # "PolarsT",
#     # "IbisT",
#     # "PyArrowT",
#     # "NarwhalsT",
#     "ExpressionT",
#     "SeriesT",

#     # Protocols
#     "DataFrameLike",
#     "LazyFrameLike",
#     "ExpressionLike",

#     # Type guards
#     "is_pandas_dataframe",
#     "is_polars_dataframe",
#     "is_polars_lazyframe",
#     "is_pyarrow_table",
#     "is_ibis_table",
#     "is_narwhals_dataframe",
#     "is_narwhals_lazyframe",
#     "is_supported_dataframe",
#     "is_dataframe_input",
#     "is_expression_input",
#     "is_python_data_input",

#     # Utilities
#     "detect_dataframe_backend_type",
# ]
