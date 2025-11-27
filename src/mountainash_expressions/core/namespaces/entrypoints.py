"""Public entry point functions for creating expressions.

This module contains all standalone factory functions that create expressions:
- col(name): Create a column reference
- lit(value): Create a literal value
- coalesce(*exprs): Return first non-null value
- greatest(*exprs): Return maximum value
- least(*exprs): Return minimum value
- when(condition): Start a conditional expression

These are the primary entry points for the expression API.
The api/ layer re-exports these for user convenience.
"""

from __future__ import annotations
from typing import Any, Union, TYPE_CHECKING

from ..protocols import ENUM_CORE_OPERATORS, ENUM_ITERABLE_OPERATORS
from ..expression_nodes import ColumnExpressionNode, LiteralExpressionNode
from ..expression_nodes.iterable_expression_nodes import IterableExpressionNode
from .conditional import WhenBuilder

if TYPE_CHECKING:
    from ..expression_api.base import BaseExpressionAPI
    from ..expression_nodes.base_expression_node import ExpressionNode


# ============================================================================
# Core Entry Points
# ============================================================================

def col(name: str) -> BaseExpressionAPI:
    """
    Create a column reference expression.

    This is the primary entry point for building expressions.
    Creates an ExpressionBuilder wrapping a ColumnExpressionNode.

    Args:
        name: Column name

    Returns:
        BooleanExpressionAPI for chaining operations

    Example:
        >>> expr = col("age").gt(30)
        >>> expr = col("name").eq("Alice")
        >>> expr = col("price").add(col("tax"))
    """
    from ..expression_api import BooleanExpressionAPI

    node = ColumnExpressionNode(
        operator=ENUM_CORE_OPERATORS.COL,
        column=name
    )
    return BooleanExpressionAPI(node)


def lit(value: Any) -> BaseExpressionAPI:
    """
    Create a literal value expression.

    Wraps a constant value (int, float, str, bool, etc.) in an
    ExpressionBuilder for use in expressions.

    Args:
        value: Literal value (int, float, str, bool, None, etc.)

    Returns:
        BooleanExpressionAPI for chaining operations

    Example:
        >>> expr = lit(42)
        >>> expr = lit("hello")
        >>> expr = col("age").gt(lit(30))
        >>> expr = col("name").eq(lit(None))  # NULL check
    """
    from ..expression_api import BooleanExpressionAPI

    node = LiteralExpressionNode(
        operator=ENUM_CORE_OPERATORS.LIT,
        value=value
    )
    return BooleanExpressionAPI(node)


# ============================================================================
# Iterable Entry Points
# ============================================================================

def _to_node(val: Any) -> Any:
    """Helper to convert a value to an expression node."""
    if hasattr(val, '_node'):
        return val._node
    else:
        return lit(val)._node


def coalesce(*exprs: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
    """
    Return the first non-null value from multiple expressions.

    Args:
        *exprs: Two or more expressions or values

    Returns:
        BooleanExpressionAPI with coalesce expression

    Raises:
        ValueError: If fewer than 2 arguments provided

    Example:
        >>> expr = coalesce(col("phone_mobile"), col("phone_home"), col("phone_work"))
        >>> expr = coalesce(col("nickname"), col("name"), lit("Anonymous"))
    """
    if len(exprs) < 2:
        raise ValueError("coalesce requires at least 2 arguments")

    from ..expression_api import BooleanExpressionAPI

    operands = [_to_node(e) for e in exprs]
    node = IterableExpressionNode(
        ENUM_ITERABLE_OPERATORS.COALESCE,
        *operands,
    )
    return BooleanExpressionAPI(node)


def greatest(*exprs: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
    """
    Return the maximum value across multiple expressions (element-wise).

    Args:
        *exprs: Two or more expressions or values

    Returns:
        BooleanExpressionAPI with greatest expression

    Raises:
        ValueError: If fewer than 2 arguments provided

    Example:
        >>> expr = greatest(col("a"), col("b"), col("c"))
        >>> expr = greatest(col("price"), lit(0))  # Ensure non-negative
    """
    if len(exprs) < 2:
        raise ValueError("greatest requires at least 2 arguments")

    from ..expression_api import BooleanExpressionAPI

    operands = [_to_node(e) for e in exprs]
    node = IterableExpressionNode(
        ENUM_ITERABLE_OPERATORS.GREATEST,
        *operands,
    )
    return BooleanExpressionAPI(node)


def least(*exprs: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
    """
    Return the minimum value across multiple expressions (element-wise).

    Args:
        *exprs: Two or more expressions or values

    Returns:
        BooleanExpressionAPI with least expression

    Raises:
        ValueError: If fewer than 2 arguments provided

    Example:
        >>> expr = least(col("a"), col("b"), col("c"))
        >>> expr = least(col("price"), lit(100))  # Cap at 100
    """
    if len(exprs) < 2:
        raise ValueError("least requires at least 2 arguments")

    from ..expression_api import BooleanExpressionAPI

    operands = [_to_node(e) for e in exprs]
    node = IterableExpressionNode(
        ENUM_ITERABLE_OPERATORS.LEAST,
        *operands,
    )
    return BooleanExpressionAPI(node)


# ============================================================================
# Conditional Entry Points
# ============================================================================

def when(condition: Union[BaseExpressionAPI, ExpressionNode, Any]) -> WhenBuilder:
    """
    Start a conditional when-then-otherwise expression.

    Args:
        condition: Boolean condition to evaluate

    Returns:
        WhenBuilder to continue chain with then()

    Example:
        >>> expr = when(col("age") > 65).then("senior").otherwise("non-senior")
        >>> expr = when(col("score") >= 90).then("A").otherwise("B")
    """
    return WhenBuilder(condition)


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Core
    "col",
    "lit",
    # Iterable
    "coalesce",
    "greatest",
    "least",
    # Conditional
    "when",
]
