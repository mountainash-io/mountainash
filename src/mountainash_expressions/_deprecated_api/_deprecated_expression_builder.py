"""
Public API for building expressions with a fluent interface.

This module provides a Polars/Narwhals-style API for building expressions
that compile to backend-native expressions.

The architecture is transitioning from mixin-based to namespace-based.
See docs/Facade Refactor/ for the refactoring plan.

Example:
    >>> import mountainash_expressions as ma
    >>>
    >>> # Build expression (backend-agnostic AST)
    >>> expr = ma.col("age").gt(30).and_(ma.col("score").ge(85))
    >>>
    >>> # Compile to backend-native expression
    >>> backend_expr = expr.compile(df)
    >>>
    >>> # Use with DataFrame
    >>> result = df.filter(backend_expr)
"""

from __future__ import annotations

from typing import Any, Union

# Re-export from new namespace-based architecture
from ..core.expression_api import (
    BaseExpressionAPI,
    BooleanExpressionAPI,
)
from ..core.expression_builders.core_expression_builder import col, lit
from ..core.expression_nodes import HorizontalExpressionNode
from ..core.protocols import ENUM_HORIZONTAL_OPERATORS

# Backwards compatibility aliases
ExpressionBuilder = BooleanExpressionAPI


# ========================================
# Standalone Functions
# ========================================

def coalesce(*values: Union[BooleanExpressionAPI, Any]) -> BooleanExpressionAPI:
    """
    Return first non-null value from a list.

    Args:
        *values: Two or more expressions or values

    Returns:
        BooleanExpressionAPI with coalesce expression

    Example:
        >>> expr = coalesce(col("phone_mobile"), col("phone_home"), col("phone_work"))
    """
    if len(values) < 2:
        raise ValueError("coalesce requires at least 2 arguments")

    # Convert all values to nodes
    def to_node(val):
        if isinstance(val, BooleanExpressionAPI):
            return val._node
        elif hasattr(val, '_node'):
            return val._node
        else:
            return lit(val)._node

    operands = [to_node(v) for v in values]
    node = HorizontalExpressionNode(
        ENUM_HORIZONTAL_OPERATORS.COALESCE,
        *operands,
    )
    return BooleanExpressionAPI(node)


class WhenBuilder:
    """
    Builder for fluent when().then().otherwise() conditional expressions.

    Example:
        >>> expr = when(col("age") > 65).then("senior").otherwise("non-senior")
    """

    def __init__(self, condition: BooleanExpressionAPI):
        self._condition = condition

    def then(self, consequence: Union[BooleanExpressionAPI, Any]) -> "WhenThenBuilder":
        """
        Specify the value to return if condition is true.

        Args:
            consequence: Value if condition is true

        Returns:
            WhenThenBuilder to continue chain with otherwise()
        """
        return WhenThenBuilder(self._condition, consequence)


class WhenThenBuilder:
    """
    Intermediate builder after then(), requires otherwise() to complete.

    Example:
        >>> expr = when(col("age") > 65).then("senior").otherwise("non-senior")
    """

    def __init__(self, condition: BooleanExpressionAPI, consequence: Any):
        self._condition = condition
        self._consequence = consequence

    def otherwise(self, alternative: Union[BooleanExpressionAPI, Any]) -> BooleanExpressionAPI:
        """
        Specify the value to return if condition is false.

        Args:
            alternative: Value if condition is false

        Returns:
            BooleanExpressionAPI with complete conditional expression
        """
        from ..core.expression_nodes._deprecated.expression_nodes import ConditionalIfElseExpressionNode
        from ..core.protocols._deprecated.conditional.conditional import ENUM_CONDITIONAL_OPERATORS

        # Helper to convert value to node
        def to_node(val):
            if isinstance(val, BooleanExpressionAPI):
                return val._node
            elif hasattr(val, '_node'):
                return val._node
            else:
                return lit(val)._node

        condition_node = to_node(self._condition)
        consequence_node = to_node(self._consequence)
        alternative_node = to_node(alternative)

        node = ConditionalIfElseExpressionNode(
            ENUM_CONDITIONAL_OPERATORS.IF_THEN_ELSE,
            condition=condition_node,
            consequence=consequence_node,
            alternative=alternative_node,
        )
        return BooleanExpressionAPI(node)


def when(condition: BooleanExpressionAPI) -> WhenBuilder:
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


__all__ = [
    "BaseExpressionAPI",
    "BooleanExpressionAPI",
    "ExpressionBuilder",  # Deprecated alias
    "coalesce",
    "when",
    "WhenBuilder",
    "WhenThenBuilder",
]
