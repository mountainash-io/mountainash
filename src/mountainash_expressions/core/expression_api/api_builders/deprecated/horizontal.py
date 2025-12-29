"""Horizontal operations namespace.

Substrait-aligned implementation using ScalarFunctionNode.

Horizontal operations work row-wise across multiple columns.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from .base import BaseExpressionNamespace
from ...expression_nodes import ScalarFunctionNode, SUBSTRAIT_COMPARISON

if TYPE_CHECKING:
    from ..expression_api.base import BaseExpressionAPI
    from ...expression_nodes import SubstraitNode


class HorizontalNamespace(BaseExpressionNamespace):
    """
    Horizontal operations namespace.

    Provides methods that operate across multiple columns row-wise.

    Methods:
        coalesce: Return first non-null value
        greatest: Return maximum value across columns
        least: Return minimum value across columns
    """

    def coalesce(
        self,
        *others: Union[BaseExpressionAPI, SubstraitNode, Any],
    ) -> BaseExpressionAPI:
        """
        Return the first non-null value from multiple expressions.

        Args:
            *others: Additional expressions to check.

        Returns:
            New ExpressionAPI with coalesce node.

        Example:
            >>> col("a").coalesce(col("b"), lit(0))
            # Returns a if not null, else b if not null, else 0
        """
        operands = [self._node] + [self._to_substrait_node(other) for other in others]
        node = ScalarFunctionNode(
            function_key=SUBSTRAIT_COMPARISON.COALESCE,
            arguments=operands,
        )
        return self._build(node)

    def greatest(
        self,
        *others: Union[BaseExpressionAPI, SubstraitNode, Any],
    ) -> BaseExpressionAPI:
        """
        Return the maximum value across multiple expressions (element-wise).

        Args:
            *others: Additional expressions to compare.

        Returns:
            New ExpressionAPI with greatest node.

        Example:
            >>> col("a").greatest(col("b"), col("c"))
            # Max of a, b, c for each row
        """
        operands = [self._node] + [self._to_substrait_node(other) for other in others]
        node = ScalarFunctionNode(
            function_key=SUBSTRAIT_COMPARISON.GREATEST,
            arguments=operands,
        )
        return self._build(node)

    def least(
        self,
        *others: Union[BaseExpressionAPI, SubstraitNode, Any],
    ) -> BaseExpressionAPI:
        """
        Return the minimum value across multiple expressions (element-wise).

        Args:
            *others: Additional expressions to compare.

        Returns:
            New ExpressionAPI with least node.

        Example:
            >>> col("a").least(col("b"), col("c"))
            # Min of a, b, c for each row
        """
        operands = [self._node] + [self._to_substrait_node(other) for other in others]
        node = ScalarFunctionNode(
            function_key=SUBSTRAIT_COMPARISON.LEAST,
            arguments=operands,
        )
        return self._build(node)
