"""NULL operations namespace.

Substrait-aligned implementation using ScalarFunctionNode.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from .base import BaseExpressionNamespace
from ...expression_nodes import (
    ScalarFunctionNode,
    LiteralNode,
    SUBSTRAIT_COMPARISON,
    MOUNTAINASH_NULL,
)

if TYPE_CHECKING:
    from ..expression_api.base import BaseExpressionAPI
    from ...expression_nodes import SubstraitNode


class NullNamespace(BaseExpressionNamespace):
    """
    NULL operations namespace (Substrait-aligned).

    Provides methods for NULL handling.

    Methods:
        is_null: Check if value is NULL
        is_not_null: Check if value is not NULL
        fill_null: Replace NULL with a value
        null_if: Return NULL if condition is met
        always_null: Return a constant NULL
    """

    # def is_null(self) -> BaseExpressionAPI:
    #     """
    #     Check if expression evaluates to NULL.

    #     Returns:
    #         New ExpressionAPI with is_null node.
    #     """
    #     node = ScalarFunctionNode(
    #         function_key=SUBSTRAIT_COMPARISON.IS_NULL,
    #         arguments=[self._node],
    #     )
    #     return self._build(node)

    # def is_not_null(self) -> BaseExpressionAPI:
    #     """
    #     Check if expression evaluates to NOT NULL.

    #     Returns:
    #         New ExpressionAPI with is_not_null node.
    #     """
    #     node = ScalarFunctionNode(
    #         function_key=SUBSTRAIT_COMPARISON.IS_NOT_NULL,
    #         arguments=[self._node],
    #     )
    #     return self._build(node)

    # # Alias for backwards compatibility
    # def not_null(self) -> BaseExpressionAPI:
    #     """
    #     Check if expression evaluates to NOT NULL.

    #     Alias for is_not_null() for backwards compatibility.

    #     Returns:
    #         New ExpressionAPI with is_not_null node.
    #     """
    #     return self.is_not_null()

    def fill_null(
        self,
        value: Union[BaseExpressionAPI, SubstraitNode, Any],
    ) -> BaseExpressionAPI:
        """
        Replace NULL values with a specified value.

        Args:
            value: Value to use in place of NULL.

        Returns:
            New ExpressionAPI with fill_null node.
        """
        value_node = self._to_substrait_node(value)
        node = ScalarFunctionNode(
            function_key=MOUNTAINASH_NULL.FILL_NULL,
            arguments=[self._node, value_node],
        )
        return self._build(node)

    def null_if(
        self,
        condition: Union[BaseExpressionAPI, SubstraitNode, Any],
    ) -> BaseExpressionAPI:
        """
        Return NULL if condition is true, otherwise return the value.

        Args:
            condition: Condition to check.

        Returns:
            New ExpressionAPI with null_if node.
        """
        condition_node = self._to_substrait_node(condition)
        node = ScalarFunctionNode(
            function_key=MOUNTAINASH_NULL.NULL_IF,
            arguments=[self._node, condition_node],
        )
        return self._build(node)

    def always_null(self) -> BaseExpressionAPI:
        """
        Return a constant NULL value.

        Returns:
            New ExpressionAPI with NULL literal node.
        """
        node = LiteralNode(value=None)
        return self._build(node)
