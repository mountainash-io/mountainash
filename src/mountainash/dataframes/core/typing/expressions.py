"""
Expression type aliases and detection utilities.

This module provides type definitions and runtime detection for expression types
across all supported backends (Polars, Narwhals, Ibis, mountainash-expressions).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union
from typing_extensions import TypeAlias, TypeGuard

if TYPE_CHECKING:
    import polars as pl
    import narwhals as nw
    import ibis.expr.types as ir
else:
    import types

    # Polars
    try:
        import polars as pl
    except ImportError:
        pl = types.ModuleType("polars")
        pl.Expr = Any

    # Narwhals
    try:
        import narwhals as nw
    except ImportError:
        nw = types.ModuleType("narwhals")
        nw.Expr = Any

    # Ibis
    try:
        import ibis.expr.types as ir
    except ImportError:
        ir = types.ModuleType("ibis.expr.types")
        ir.Expr = Any


# ============================================================================
# Type Aliases
# ============================================================================

PolarsExpr: TypeAlias = pl.Expr
NarwhalsExpr: TypeAlias = nw.Expr
IbisExpr: TypeAlias = ir.Expr

# Union of all supported expression types
SupportedExpressions: TypeAlias = Union[PolarsExpr, NarwhalsExpr, IbisExpr]


# ============================================================================
# Type Guards - Expression Detection
# ============================================================================


def is_polars_expression(obj: Any) -> TypeGuard[PolarsExpr]:
    """
    Check if object is a Polars Expr (lazy expression).

    Args:
        obj: Object to check

    Returns:
        True if object is a pl.Expr
    """
    obj_type = type(obj)
    module = obj_type.__module__
    return module.startswith("polars") and obj_type.__name__ == "Expr"


def is_narwhals_expression(obj: Any) -> TypeGuard[NarwhalsExpr]:
    """
    Check if object is a Narwhals Expr (lazy expression).

    Args:
        obj: Object to check

    Returns:
        True if object is a nw.Expr
    """
    obj_type = type(obj)
    module = obj_type.__module__
    return module.startswith("narwhals") and obj_type.__name__ == "Expr"


def is_ibis_expression(obj: Any) -> bool:
    """
    Check if object is an Ibis expression.

    Ibis has multiple expression types (Column, Scalar, etc.) so we check
    for common patterns rather than exact class name.

    Args:
        obj: Object to check

    Returns:
        True if object is an Ibis expression
    """
    obj_type = type(obj)
    module = obj_type.__module__
    class_name = obj_type.__name__
    if module.startswith("ibis"):
        return "Column" in class_name or "Expr" in class_name or "Scalar" in class_name
    return False


def is_mountainash_expression(obj: Any) -> bool:
    """
    Check if object is a mountainash expression.

    Detects both BaseExpressionAPI (fluent API) and ExpressionNode (AST node).
    Uses string-based detection to avoid hard dependency on mountainash-expressions.

    Args:
        obj: Object to check

    Returns:
        True if object is a mountainash expression
    """
    obj_type = type(obj)
    module = obj_type.__module__
    class_name = obj_type.__name__

    # Check for mountainash-expressions types
    if module.startswith(("mountainash_expressions", "mountainash.expressions")):
        return True

    # Check for known expression API/node class names
    if class_name in ("BooleanExpressionAPI", "BaseExpressionAPI") or class_name.endswith(
        "ExpressionNode"
    ):
        return True

    # Check for _node attribute (ExpressionAPI pattern)
    if hasattr(obj, "_node") and hasattr(obj, "compile"):
        return True

    return False


def is_native_expression(obj: Any) -> bool:
    """
    Check if object is a native backend expression (not mountainash).

    This includes:
    - Polars Expr (pl.Expr)
    - Narwhals Expr (nw.Expr)
    - Ibis expressions (ir.Expr, ir.BooleanColumn, etc.)

    Note: This does NOT include Series types - use is_native_series() for those.

    Args:
        obj: Object to check

    Returns:
        True if object is a native backend expression
    """
    return is_polars_expression(obj) or is_narwhals_expression(obj) or is_ibis_expression(obj)


def is_supported_expression(obj: Any) -> bool:
    """
    Check if object is any supported expression type.

    Includes both native backend expressions and mountainash expressions.

    Args:
        obj: Object to check

    Returns:
        True if object is a supported expression type
    """
    return is_native_expression(obj) or is_mountainash_expression(obj)


# ============================================================================
# Expression Backend Detection
# ============================================================================


def detect_expression_backend(obj: Any) -> str | None:
    """
    Detect the backend type of an expression object.

    Args:
        obj: Expression object to check

    Returns:
        Backend name ('polars', 'narwhals', 'ibis', 'mountainash') or None if not recognized
    """
    if is_polars_expression(obj):
        return "polars"
    elif is_narwhals_expression(obj):
        return "narwhals"
    elif is_ibis_expression(obj):
        return "ibis"
    elif is_mountainash_expression(obj):
        return "mountainash"
    return None


# ============================================================================
# Export List
# ============================================================================

__all__ = [
    # Type aliases
    "PolarsExpr",
    "NarwhalsExpr",
    "IbisExpr",
    "SupportedExpressions",
    # Type guards
    "is_polars_expression",
    "is_narwhals_expression",
    "is_ibis_expression",
    "is_mountainash_expression",
    "is_native_expression",
    "is_supported_expression",
    # Detection utilities
    "detect_expression_backend",
]
