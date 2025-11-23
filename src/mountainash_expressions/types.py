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
    import ibis.expr.types as ir
    import polars as pl
    import narwhals as nw
else:
    # Runtime fallback for optional imports
    # This enables runtime type introspection (e.g., Hamilton) while keeping dependencies optional
    import types


    # Polars
    try:
        import polars as pl
    except ImportError:
        pl = types.ModuleType('polars')
        pl.Expr = Any


    # Ibis
    try:
        import ibis as ibis
        import ibis.expr.types as ir
    except ImportError:
        ibis = types.ModuleType('ibis')
        ir = types.ModuleType('ibis.expr.types')
        ir.Expr = Any

    # Narwhals
    try:
        import narwhals as nw
    except ImportError:
        nw = types.ModuleType('narwhals')
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

# Polars types
PolarsExpr: TypeAlias = pl.Expr

# Ibis types
IbisExpr: TypeAlias = ir.Expr

# Narwhals types
NarwhalsExpr: TypeAlias = nw.Expr

# Expression types across backends
SupportedExpressions: TypeAlias = Union[PolarsExpr, IbisExpr, NarwhalsExpr]

# ============================================================================
# Type Guards for Runtime Type Checking
# ============================================================================


def is_polars_expression(obj: Any) -> TypeGuard[PolarsExpr]:
    """Type guard for polars DataFrames."""
    return type(obj).__module__.startswith("polars") and type(obj).__name__ == "Expr"


def is_ibis_expression(obj: Any) -> TypeGuard[IbisExpr]:
    """Type guard for Ibis Tables."""
    module = type(obj).__module__
    return "ibis" in module and hasattr(obj, "execute")

def is_narwhals_expression(obj: Any) -> TypeGuard[NarwhalsExpr]:
    """Type guard for Narwhals DataFrames."""
    return type(obj).__module__.startswith("narwhals") and type(obj).__name__ == "Expr"


def is_supported_dataframe(obj: Any) -> TypeGuard[SupportedDataFrames]:
    """Type guard for any supported dataframe type."""
    return any([
        is_polars_expression(obj),
        is_ibis_expression(obj),
        is_narwhals_expression(obj),
    ])

# ============================================================================
# Backend Detection Utilities
# ============================================================================

# def detect_dataframe_backend_type(obj: Any) -> str:
#     """
#     Detect the backend type of a dataframe object without importing libraries.

#     Returns:
#         Backend name: 'pandas', 'polars', 'pyarrow', 'ibis', 'narwhals'

#     Raises:
#         ValueError: If the object type is not recognized
#     """
#     if is_pandas_dataframe(obj):
#         return "pandas"
#     elif is_polars_dataframe(obj) or is_polars_lazyframe(obj):
#         return "polars"
#     elif is_pyarrow_table(obj):
#         return "pyarrow"
#     elif is_ibis_table(obj):
#         return "ibis"
#     elif is_narwhals_dataframe(obj) or is_narwhals_lazyframe(obj):
#         return "narwhals"
#     else:
#         raise ValueError(f"Unknown dataframe type: {type(obj).__module__}.{type(obj).__name__}")

# ============================================================================
# Column Type Mappings
# ============================================================================
