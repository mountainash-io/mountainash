"""Core factory functions for creating ExpressionBuilder instances.

This module provides the fundamental entry points for building expressions:
- col(name): Create a column reference
- lit(value): Create a literal value

These are module-level functions, not methods on ExpressionBuilder.
"""

from __future__ import annotations
from typing import Any, TYPE_CHECKING

from .base_expression_builder import BaseExpressionBuilder

if TYPE_CHECKING:
    pass

from ..protocols import ENUM_CORE_OPERATORS, CoreBuilderProtocol
from ..expression_nodes import (
    ColumnExpressionNode,
    LiteralExpressionNode,
)


class CoreExpressionBuilder(BaseExpressionBuilder, CoreBuilderProtocol):
    """
    Mixin providing core operations for ExpressionBuilder.

    Currently a placeholder - col() and lit() are module-level functions.
    """

    @classmethod
    def create(cls, node: Any) -> CoreExpressionBuilder:
        return cls(node)


def col(name: str) -> BaseExpressionBuilder:
    """
    Create a column reference expression.

    This is the primary entry point for building expressions.
    Creates an ExpressionBuilder wrapping a ColumnExpressionNode.

    Args:
        name: Column name

    Returns:
        ExpressionBuilder for chaining operations

    Example:
        >>> expr = col("age").gt(30)
        >>> expr = col("name").eq("Alice")
        >>> expr = col("price").add(col("tax"))
    """
    # Import here to avoid circular dependency
    from ..expression_api import BooleanExpressionAPI

    node = ColumnExpressionNode(
        operator=ENUM_CORE_OPERATORS.COL,
        column=name
    )
    return BooleanExpressionAPI(node)


def lit(value: Any) -> BaseExpressionBuilder:
    """
    Create a literal value expression.

    Wraps a constant value (int, float, str, bool, etc.) in an
    ExpressionBuilder for use in expressions.

    Args:
        value: Literal value (int, float, str, bool, None, etc.)

    Returns:
        ExpressionBuilder for chaining operations

    Example:
        >>> expr = lit(42)
        >>> expr = lit("hello")
        >>> expr = col("age").gt(lit(30))
        >>> expr = col("name").eq(lit(None))  # NULL check
    """
    # Import here to avoid circular dependency
    from ..expression_api import BooleanExpressionAPI

    node = LiteralExpressionNode(
        operator=ENUM_CORE_OPERATORS.LIT,
        value=value
    )
    return BooleanExpressionAPI(node)


# Note: col() and lit() are NOT part of a mixin class
# They are module-level factory functions that CREATE ExpressionBuilder instances
