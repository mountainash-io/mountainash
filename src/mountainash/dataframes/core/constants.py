"""
Unified constants for mountainash-dataframes core framework.

Backend enums are imported from mountainash.core.constants.
This module adds dataframes-specific groupings and InputType.
"""

from __future__ import annotations

from enum import Enum, auto

from mountainash.core.constants import (
    CONST_BACKEND as Backend,
    CONST_BACKEND_SYSTEM as DataFrameSystemBackend,
    backend_to_system,
)


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


# =============================================================================
# Backend Groupings
# =============================================================================

NARWHALS_WRAPPABLE_BACKENDS: frozenset[Backend] = frozenset({
    Backend.POLARS,
    Backend.PANDAS,
    Backend.PYARROW,
})

LAZY_BACKENDS: frozenset[Backend] = frozenset({
    Backend.POLARS,
    Backend.IBIS,
    Backend.NARWHALS,
})

EXPRESSION_BACKENDS: frozenset[Backend] = frozenset({
    Backend.POLARS,
    Backend.NARWHALS,
    Backend.IBIS,
})


__all__ = [
    "Backend",
    "DataFrameSystemBackend",
    "backend_to_system",
    "InputType",
    "NARWHALS_WRAPPABLE_BACKENDS",
    "LAZY_BACKENDS",
    "EXPRESSION_BACKENDS",
]
