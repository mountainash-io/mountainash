"""Null handling operations APIBuilder.

Substrait-aligned implementation using ScalarFunctionNode.
Provides null replacement and handling operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from ..api_builder_base import BaseExpressionAPIBuilder

from mountainash_expressions.core.expression_system.function_keys.enums import MOUNTAINASH_NULL
from mountainash_expressions.core.expression_nodes import ScalarFunctionNode, ExpressionNode
from mountainash_expressions.core.expression_protocols.api_builders.extensions_mountainash import SubstraitCastAPIBuilderProtocol


if TYPE_CHECKING:
    from ...api_base import BaseExpressionAPI
    from ....expression_nodes import ExpressionNode


class MountainAshNullAPIBuilder(BaseExpressionAPIBuilder):
    """
    Null handling operations APIBuilder.

    Note: is_null and is_not_null are in ScalarComparisonAPIBuilder.
    This APIBuilder provides additional null-related operations.

    Methods:
        fill_null: Replace null values with a specified value
        null_if: Replace values matching condition with null
    """

    def fill_null(
        self,
        value: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Replace null values with the specified value.

        Args:
            value: Value to use in place of nulls.

        Returns:
            New ExpressionAPI with fill_null node.

        Example:
            >>> expr = col("phone").fill_null("N/A")
        """
        value_node = self._to_substrait_node(value)
        node = ScalarFunctionNode(
            function_key=MOUNTAINASH_NULL.FILL_NULL,
            arguments=[self._node, value_node],
        )
        return self._build(node)

    def null_if(
        self,
        value: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Replace values equal to the specified value with null.

        Args:
            value: Value to replace with null.

        Returns:
            New ExpressionAPI with null_if node.

        Example:
            >>> expr = col("status").null_if("UNKNOWN")
        """
        value_node = self._to_substrait_node(value)
        node = ScalarFunctionNode(
            function_key=MOUNTAINASH_NULL.NULL_IF,
            arguments=[self._node, value_node],
        )
        return self._build(node)
