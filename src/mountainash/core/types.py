"""
Unified typing system for the mountainash package.

Single source of truth for all shared type aliases, runtime fallback imports,
type guards, and protocols used across expressions, dataframes, schema, and pydata.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, Union, Protocol, Any
from typing_extensions import TypeAlias, TypeGuard
from collections.abc import Sequence, Mapping

if TYPE_CHECKING:
    import ibis as ibis
    import ibis.expr.types as ir
    import pandas as pd
    import polars as pl
    import pyarrow as pa
    import narwhals as nw

    # ========================================================================
    # Type Aliases — DataFrames
    # ========================================================================

    PandasFrame: TypeAlias = pd.DataFrame
    PolarsFrame: TypeAlias = pl.DataFrame
    PolarsLazyFrame: TypeAlias = pl.LazyFrame
    PyArrowTable: TypeAlias = pa.Table
    IbisTable: TypeAlias = ir.Table
    IbisBaseBackend: TypeAlias = ibis.BaseBackend
    IbisSchema: TypeAlias = ibis.expr.schema.Schema
    NarwhalsFrame: TypeAlias = nw.DataFrame
    NarwhalsLazyFrame: TypeAlias = nw.LazyFrame

    # ========================================================================
    # Type Aliases — Expressions
    # ========================================================================

    PolarsExpr: TypeAlias = pl.Expr
    IbisExpr: TypeAlias = Union[ir.Expr, ir.Column, ir.Scalar]
    NarwhalsExpr: TypeAlias = nw.Expr

    # ========================================================================
    # Type Aliases — Series
    # ========================================================================

    PandasSeries: TypeAlias = pd.Series
    PolarsSeries: TypeAlias = pl.Series
    NarwhalsSeries: TypeAlias = nw.Series
    PyArrowArray: TypeAlias = pa.Array

    # ========================================================================
    # Composite Type Unions
    # ========================================================================

    PolarsFrameTypes: TypeAlias = Union[PolarsFrame, PolarsLazyFrame]
    NarwhalsFrameTypes: TypeAlias = Union[NarwhalsFrame, NarwhalsLazyFrame]

    SupportedDataFrames: TypeAlias = Union[
        PandasFrame,
        PolarsFrame,
        PolarsLazyFrame,
        PyArrowTable,
        IbisTable,
        NarwhalsFrame,
        NarwhalsLazyFrame,
    ]

    SupportedExpressions: TypeAlias = Union[PolarsExpr, IbisExpr, NarwhalsExpr]

    SupportedSeries: TypeAlias = Union[PandasSeries, PolarsSeries, NarwhalsSeries, PyArrowArray]

    # ========================================================================
    # Ibis Domain-Specific Type Aliases
    # ========================================================================

    IbisNumericExpr: TypeAlias = ir.NumericValue
    IbisBooleanExpr: TypeAlias = ir.BooleanValue
    IbisStringExpr: TypeAlias = ir.StringValue
    IbisTemporalExpr: TypeAlias = Union[ir.TimestampValue, ir.DateValue, ir.TimeValue]
    IbisColumnExpr: TypeAlias = ir.Column
    IbisNumericColumnExpr: TypeAlias = ir.NumericColumn
    IbisBooleanColumnExpr: TypeAlias = ir.BooleanColumn
    IbisStringColumnExpr: TypeAlias = ir.StringColumn
    IbisValueExpr: TypeAlias = ir.Value
    IbisScalarExpr: TypeAlias = ir.Scalar


# ============================================================================
# Generic Type Variables
# ============================================================================

DataFrameT = TypeVar("DataFrameT", bound="SupportedDataFrames")
ExpressionT = TypeVar("ExpressionT", bound="SupportedExpressions")
SeriesT = TypeVar("SeriesT", bound="SupportedSeries")

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
# Column Type Mappings (stdlib only — no backend dependency)
# ============================================================================

ColumnTypes: TypeAlias = Union[type, str]

if TYPE_CHECKING:
    ColumnMapping: TypeAlias = Mapping[str, ColumnTypes]
else:
    ColumnMapping: TypeAlias = "Mapping[str, ColumnTypes]"

# ============================================================================
# Type Guards — DataFrame Detection
# ============================================================================

def is_pandas_dataframe(obj: Any) -> TypeGuard['PandasFrame']:
    """Type guard for pandas DataFrames."""
    return type(obj).__module__.startswith("pandas") and type(obj).__name__ == "DataFrame"

def is_polars_dataframe(obj: Any) -> TypeGuard['PolarsFrame']:
    """Type guard for polars DataFrames."""
    return type(obj).__module__.startswith("polars") and type(obj).__name__ == "DataFrame"

def is_polars_lazyframe(obj: Any) -> TypeGuard['PolarsLazyFrame']:
    """Type guard for polars LazyFrames."""
    return type(obj).__module__.startswith("polars") and type(obj).__name__ == "LazyFrame"

def is_pyarrow_table(obj: Any) -> TypeGuard['PyArrowTable']:
    """Type guard for PyArrow Tables."""
    return type(obj).__module__.startswith("pyarrow") and type(obj).__name__ == "Table"

def is_ibis_table(obj: Any) -> TypeGuard['IbisTable']:
    """Type guard for Ibis Tables."""
    module = type(obj).__module__
    return "ibis" in module and hasattr(obj, "execute")

def is_narwhals_dataframe(obj: Any) -> TypeGuard['NarwhalsFrame']:
    """Type guard for Narwhals DataFrames."""
    return type(obj).__module__.startswith("narwhals") and type(obj).__name__ == "DataFrame"

def is_narwhals_lazyframe(obj: Any) -> TypeGuard['NarwhalsLazyFrame']:
    """Type guard for Narwhals LazyFrames."""
    return type(obj).__module__.startswith("narwhals") and type(obj).__name__ == "LazyFrame"

def is_supported_dataframe(obj: Any) -> TypeGuard['SupportedDataFrames']:
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
# Type Guards — Expression Detection
# ============================================================================

def is_polars_expression(obj: Any) -> TypeGuard['PolarsExpr']:
    """Type guard for polars Expressions."""
    return type(obj).__module__.startswith("polars") and type(obj).__name__ == "Expr"

def is_ibis_expression(obj: Any) -> TypeGuard['IbisExpr']:
    """Type guard for Ibis Expressions."""
    module = type(obj).__module__
    return "ibis" in module and hasattr(obj, "execute")

def is_narwhals_expression(obj: Any) -> TypeGuard['NarwhalsExpr']:
    """Type guard for Narwhals Expressions."""
    return type(obj).__module__.startswith("narwhals") and type(obj).__name__ == "Expr"

# ============================================================================
# Type Guards — Series Detection
# ============================================================================

def is_pandas_series(obj: Any) -> TypeGuard['PandasSeries']:
    """Type guard for pandas Series."""
    return type(obj).__module__.startswith("pandas") and type(obj).__name__ == "Series"

def is_polars_series(obj: Any) -> TypeGuard['PolarsSeries']:
    """Type guard for polars Series."""
    return type(obj).__module__.startswith("polars") and type(obj).__name__ == "Series"

def is_narwhals_series(obj: Any) -> TypeGuard['NarwhalsSeries']:
    """Type guard for Narwhals Series."""
    return type(obj).__module__.startswith("narwhals") and type(obj).__name__ == "Series"

def is_pyarrow_array(obj: Any) -> TypeGuard['PyArrowArray']:
    """Type guard for PyArrow Arrays."""
    return type(obj).__module__.startswith("pyarrow") and type(obj).__name__ == "Array"
