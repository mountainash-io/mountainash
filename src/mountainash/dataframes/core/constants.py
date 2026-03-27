"""
Unified constants for mountainash-dataframes core framework.

This module provides the canonical enums for:
- Backend: The DataFrame/Series/Expression backend (Polars, pandas, etc.)
- InputType: The category of input (DataFrame, Expression, Series)

All backend detection and resolution should use these enums for type safety.
Using Enum with auto() ensures identity-based comparison rather than string-based.
"""

from __future__ import annotations

from enum import Enum, auto


class Backend(Enum):
    """
    Unified backend enumeration for DataFrames, Series, and Expressions.

    This enum represents the actual library backend, not just the routing target.
    For example, pandas DataFrames are detected as PANDAS even though they may
    be routed through Narwhals for operations.

    Members:
        POLARS: Polars library (DataFrame, LazyFrame, Series, Expr)
        PANDAS: pandas library (DataFrame, Series)
        PYARROW: PyArrow library (Table, Array, ChunkedArray)
        IBIS: Ibis library (Table, expressions)
        NARWHALS: Narwhals wrapper library (DataFrame, LazyFrame, Series, Expr)
    """

    POLARS = auto()
    PANDAS = auto()
    PYARROW = auto()
    IBIS = auto()
    NARWHALS = auto()


class InputType(Enum):
    """
    Category of input object.

    Used to determine which resolution strategy to apply.

    Members:
        DATAFRAME: Tabular data (pl.DataFrame, pd.DataFrame, pa.Table, etc.)
        EXPRESSION: Lazy column expression (pl.Expr, nw.Expr, ir.BooleanColumn, etc.)
        SERIES: Physical column data (pl.Series, pd.Series, pa.Array, etc.)
    """

    DATAFRAME = auto()
    EXPRESSION = auto()
    SERIES = auto()


class DataFrameSystemBackend(Enum):
    """
    Backend routing targets for DataFrameSystem.

    This is a coarser grouping than Backend - it represents which
    DataFrameSystem implementation handles the type:

    - POLARS: Native Polars operations
    - NARWHALS: pandas, PyArrow, cuDF routed through Narwhals adapter
    - IBIS: Ibis SQL backends

    Note: Use Backend enum for detection, this enum for routing.
    """

    POLARS = auto()
    NARWHALS = auto()
    IBIS = auto()


# =============================================================================
# Backend Groupings
# =============================================================================

# Backends that can be wrapped by Narwhals
NARWHALS_WRAPPABLE_BACKENDS: frozenset[Backend] = frozenset({
    Backend.POLARS,
    Backend.PANDAS,
    Backend.PYARROW,
})

# Backends that support lazy evaluation
LAZY_BACKENDS: frozenset[Backend] = frozenset({
    Backend.POLARS,  # LazyFrame
    Backend.IBIS,    # Always lazy until .execute()
    Backend.NARWHALS,  # LazyFrame wrapper
})

# Backends that support native expressions (not just series filtering)
EXPRESSION_BACKENDS: frozenset[Backend] = frozenset({
    Backend.POLARS,
    Backend.NARWHALS,
    Backend.IBIS,
})


# =============================================================================
# Backend Mapping
# =============================================================================

def backend_to_system(backend: Backend) -> DataFrameSystemBackend:
    """
    Map a detected Backend to its DataFrameSystemBackend routing target.

    Args:
        backend: The detected backend

    Returns:
        The DataFrameSystemBackend to route operations through

    Examples:
        >>> backend_to_system(Backend.POLARS)
        DataFrameSystemBackend.POLARS
        >>> backend_to_system(Backend.PANDAS)
        DataFrameSystemBackend.NARWHALS
    """
    mapping = {
        Backend.POLARS: DataFrameSystemBackend.POLARS,
        Backend.PANDAS: DataFrameSystemBackend.NARWHALS,
        Backend.PYARROW: DataFrameSystemBackend.NARWHALS,
        Backend.IBIS: DataFrameSystemBackend.IBIS,
        Backend.NARWHALS: DataFrameSystemBackend.NARWHALS,
    }
    return mapping[backend]


__all__ = [
    # Core enums
    "Backend",
    "InputType",
    "DataFrameSystemBackend",
    # Backend groupings
    "NARWHALS_WRAPPABLE_BACKENDS",
    "LAZY_BACKENDS",
    "EXPRESSION_BACKENDS",
    # Mapping functions
    "backend_to_system",
]
