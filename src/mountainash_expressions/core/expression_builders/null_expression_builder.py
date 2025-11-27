"""NULL operations mixin for ExpressionBuilder."""

from __future__ import annotations
from typing import Any, Union, TYPE_CHECKING

from .base_expression_builder import BaseExpressionBuilder

if TYPE_CHECKING:
    from ..expression_nodes import ExpressionNode

from ..protocols import NullBuilderProtocol, ENUM_NULL_OPERATORS
from ..expression_nodes import (
    NullExpressionNode,
    NullConditionalExpressionNode,
    NullConstantExpressionNode,
    NullLogicalExpressionNode,
)


class NullExpressionBuilder(BaseExpressionBuilder, NullBuilderProtocol):
    """
    Mixin providing NULL operations for ExpressionBuilder.

    Implements methods for NULL handling:
    - is_null(): Check if value is NULL
    - not_null(): Check if value is not NULL
    - fill_null(): Replace NULL with a value
    - null_if(): Return NULL if condition is met
    - always_null(): Return a constant NULL
    """

    def is_null(self) -> BaseExpressionBuilder:
        """
        Check if expression evaluates to NULL.

        Returns:
            New ExpressionBuilder with is_null node

        Example:
            >>> col("age").is_null()
        """

        node = NullLogicalExpressionNode(
            ENUM_NULL_OPERATORS.IS_NULL,
            self._node
        )
        return self.create(node)

    def not_null(self) -> BaseExpressionBuilder:
        """
        Check if expression evaluates to NOT NULL.

        Returns:
            New ExpressionBuilder with not_null node

        Example:
            >>> col("name").not_null()
        """

        node = NullLogicalExpressionNode(
            ENUM_NULL_OPERATORS.NOT_NULL,
            self._node
        )
        return self.create(node)

    def fill_null(self, value: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """
        Replace NULL values with a specified value.

        Args:
            value: Value to use in place of NULL

        Returns:
            New ExpressionBuilder with fill_null node

        Example:
            >>> col("age").fill_null(0)
            >>> col("name").fill_null("Unknown")
        """

        value_node = self._to_node_or_value(value)
        node = NullExpressionNode(
            ENUM_NULL_OPERATORS.FILL_NULL,
            self._node,
            value_node
        )
        return self.create(node)

    def null_if(self, condition: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """
        Return NULL if condition is true, otherwise return the value.

        Args:
            condition: Condition to check

        Returns:
            New ExpressionBuilder with null_if node

        Example:
            >>> col("age").null_if(col("age").lt(0))  # NULL if age < 0
        """

        condition_node = self._to_node_or_value(condition)
        node = NullConditionalExpressionNode(
            ENUM_NULL_OPERATORS.NULL_IF,
            self._node,
            condition_node
        )
        return self.create(node)

    def always_null(self) -> BaseExpressionBuilder:
        """
        Return a constant NULL value.

        Returns:
            New ExpressionBuilder with always_null node

        Example:
            >>> ExpressionBuilder.always_null()  # Static method usage
        """

        node = NullConstantExpressionNode(
            ENUM_NULL_OPERATORS.ALWAYS_NULL
        )
        return self.create(node)
