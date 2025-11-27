"""NULL operations namespace."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from .base import BaseNamespace
from ..protocols import ENUM_NULL_OPERATORS
from ..expression_nodes import (
    NullExpressionNode,
    NullConditionalExpressionNode,
    NullConstantExpressionNode,
    NullLogicalExpressionNode,
)

if TYPE_CHECKING:
    from ..expression_api.base import BaseExpressionAPI
    from ..expression_nodes.base_expression_node import ExpressionNode


class NullNamespace(BaseNamespace):
    """
    NULL operations namespace.

    Provides methods for NULL handling.

    Methods:
        is_null: Check if value is NULL
        not_null: Check if value is not NULL
        fill_null: Replace NULL with a value
        null_if: Return NULL if condition is met
        always_null: Return a constant NULL
    """

    def is_null(self) -> BaseExpressionAPI:
        """
        Check if expression evaluates to NULL.

        Returns:
            New ExpressionAPI with is_null node.
        """
        node = NullLogicalExpressionNode(
            ENUM_NULL_OPERATORS.IS_NULL,
            self._node,
        )
        return self._build(node)

    def not_null(self) -> BaseExpressionAPI:
        """
        Check if expression evaluates to NOT NULL.

        Returns:
            New ExpressionAPI with not_null node.
        """
        node = NullLogicalExpressionNode(
            ENUM_NULL_OPERATORS.NOT_NULL,
            self._node,
        )
        return self._build(node)

    def fill_null(
        self,
        value: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Replace NULL values with a specified value.

        Args:
            value: Value to use in place of NULL.

        Returns:
            New ExpressionAPI with fill_null node.
        """
        value_node = self._to_node_or_value(value)
        node = NullExpressionNode(
            ENUM_NULL_OPERATORS.FILL_NULL,
            self._node,
            value_node,
        )
        return self._build(node)

    def null_if(
        self,
        condition: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Return NULL if condition is true, otherwise return the value.

        Args:
            condition: Condition to check.

        Returns:
            New ExpressionAPI with null_if node.
        """
        condition_node = self._to_node_or_value(condition)
        node = NullConditionalExpressionNode(
            ENUM_NULL_OPERATORS.NULL_IF,
            self._node,
            condition_node,
        )
        return self._build(node)

    def always_null(self) -> BaseExpressionAPI:
        """
        Return a constant NULL value.

        Returns:
            New ExpressionAPI with always_null node.
        """
        node = NullConstantExpressionNode(
            ENUM_NULL_OPERATORS.ALWAYS_NULL,
        )
        return self._build(node)
