"""
Expression type aliases and detection utilities.

Type aliases and basic guards are imported from mountainash.core.types.
This module adds dataframes-specific guards: is_mountainash_expression(),
is_native_expression(), is_supported_expression(), detect_expression_backend().
"""

from __future__ import annotations

from typing import Any
from typing_extensions import TypeAlias, TypeGuard

# Re-export type aliases and basic guards from core
from mountainash.core.types import (
    PolarsExpr,
    NarwhalsExpr,
    IbisExpr,
    SupportedExpressions,
    is_polars_expression,
    is_narwhals_expression,
)


# ============================================================================
# Ibis Expression Detection (more detailed than core version)
# ============================================================================

def is_ibis_expression(obj: Any) -> bool:
    """
    Check if object is an Ibis expression.

    Ibis has multiple expression types (Column, Scalar, etc.) so we check
    for common patterns rather than exact class name.
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
