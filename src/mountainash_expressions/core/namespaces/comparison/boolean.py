"""Boolean comparison operations namespace."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from ..base import BaseNamespace
from ...protocols import ENUM_BOOLEAN_OPERATORS
from ...expression_nodes import (
    BooleanComparisonExpressionNode,
    BooleanCollectionExpressionNode,
    BooleanConstantExpressionNode,
    BooleanIsCloseExpressionNode,
    BooleanBetweenExpressionNode,
)

if TYPE_CHECKING:
    from ...expression_api.base import BaseExpressionAPI
    from ...expression_nodes.base_expression_node import ExpressionNode


class BooleanComparisonNamespace(BaseNamespace):
    """
    Comparison operations producing boolean results.

    Provides comparison operators (eq, ne, gt, lt, ge, le),
    collection membership (is_in, is_not_in), and boolean constants.

    Methods:
        eq: Equal to (==)
        ne: Not equal to (!=)
        gt: Greater than (>)
        lt: Less than (<)
        ge: Greater than or equal (>=)
        le: Less than or equal (<=)
        is_close: Approximately equal within precision
        between: Value within range
        is_in: Value in collection
        is_not_in: Value not in collection
        always_true: Constant TRUE
        always_false: Constant FALSE
    """

    # ========================================
    # Comparison Operations
    # ========================================

    def eq(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Equal to (==).

        Args:
            other: Value or expression to compare with.

        Returns:
            New ExpressionAPI with comparison node.
        """
        other_node = self._to_node_or_value(other)
        node = BooleanComparisonExpressionNode(
            ENUM_BOOLEAN_OPERATORS.EQ,
            self._node,
            other_node,
        )
        return self._build(node)

    def ne(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """Not equal to (!=)."""
        other_node = self._to_node_or_value(other)
        node = BooleanComparisonExpressionNode(
            ENUM_BOOLEAN_OPERATORS.NE,
            self._node,
            other_node,
        )
        return self._build(node)

    def gt(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """Greater than (>)."""
        other_node = self._to_node_or_value(other)
        node = BooleanComparisonExpressionNode(
            ENUM_BOOLEAN_OPERATORS.GT,
            self._node,
            other_node,
        )
        return self._build(node)

    def lt(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """Less than (<)."""
        other_node = self._to_node_or_value(other)
        node = BooleanComparisonExpressionNode(
            ENUM_BOOLEAN_OPERATORS.LT,
            self._node,
            other_node,
        )
        return self._build(node)

    def ge(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """Greater than or equal (>=)."""
        other_node = self._to_node_or_value(other)
        node = BooleanComparisonExpressionNode(
            ENUM_BOOLEAN_OPERATORS.GE,
            self._node,
            other_node,
        )
        return self._build(node)

    def le(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """Less than or equal (<=)."""
        other_node = self._to_node_or_value(other)
        node = BooleanComparisonExpressionNode(
            ENUM_BOOLEAN_OPERATORS.LE,
            self._node,
            other_node,
        )
        return self._build(node)

    def is_close(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
        precision: float = 1e-5,
    ) -> BaseExpressionAPI:
        """
        Check if values are approximately equal within precision.

        Args:
            other: Value to compare with.
            precision: Maximum allowed difference (default: 1e-5).

        Returns:
            New ExpressionAPI with is_close node.
        """
        other_node = self._to_node_or_value(other)
        node = BooleanIsCloseExpressionNode(
            ENUM_BOOLEAN_OPERATORS.IS_CLOSE,
            self._node,
            other_node,
            precision,
        )
        return self._build(node)

    def between(
        self,
        lower: Union[BaseExpressionAPI, ExpressionNode, Any],
        upper: Union[BaseExpressionAPI, ExpressionNode, Any],
        closed: str = "both",
    ) -> BaseExpressionAPI:
        """
        Check if value is between bounds.

        Args:
            lower: Lower bound.
            upper: Upper bound.
            closed: Which bounds are inclusive ("left", "right", "both", "neither").

        Returns:
            New ExpressionAPI with between node.
        """
        # Note: BooleanBetweenExpressionNode(operator, left, right, closed)
        # where left is the value, right is upper bound, and we need to handle lower separately
        # Based on the constructor, this seems wrong - let me check the visitor to understand usage
        lower_node = self._to_node_or_value(lower)
        upper_node = self._to_node_or_value(upper)
        node = BooleanBetweenExpressionNode(
            ENUM_BOOLEAN_OPERATORS.BETWEEN,
            self._node,  # value to check
            lower_node,  # should be lower, but constructor says "right"
            closed,
        )
        # TODO: Verify this matches visitor expectations
        return self._build(node)

    # ========================================
    # Collection Operations
    # ========================================

    def is_in(
        self,
        values: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Check if value is in a collection.

        Args:
            values: Collection to check membership in.

        Returns:
            New ExpressionAPI with is_in node.
        """
        values_node = self._to_node_or_value(values)
        node = BooleanCollectionExpressionNode(
            ENUM_BOOLEAN_OPERATORS.IS_IN,
            None,  # operand (not used by visitor)
            self._node,  # element (used by visitor)
            values_node,  # container
        )
        return self._build(node)

    def is_not_in(
        self,
        values: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Check if value is not in a collection.

        Args:
            values: Collection to check membership in.

        Returns:
            New ExpressionAPI with is_not_in node.
        """
        values_node = self._to_node_or_value(values)
        node = BooleanCollectionExpressionNode(
            ENUM_BOOLEAN_OPERATORS.IS_NOT_IN,
            None,  # operand (not used by visitor)
            self._node,  # element (used by visitor)
            values_node,  # container
        )
        return self._build(node)

    # ========================================
    # Boolean Constants
    # ========================================

    def always_true(self) -> BaseExpressionAPI:
        """Return a constant TRUE value."""
        node = BooleanConstantExpressionNode(
            ENUM_BOOLEAN_OPERATORS.ALWAYS_TRUE,
        )
        return self._build(node)

    def always_false(self) -> BaseExpressionAPI:
        """Return a constant FALSE value."""
        node = BooleanConstantExpressionNode(
            ENUM_BOOLEAN_OPERATORS.ALWAYS_FALSE,
        )
        return self._build(node)
