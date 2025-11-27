"""Iterable operations mixin for ExpressionBuilder."""

from __future__ import annotations
from typing import Any, Union, TYPE_CHECKING

from .base_expression_builder import BaseExpressionBuilder

if TYPE_CHECKING:
    from ..expression_nodes import ExpressionNode

from ..protocols import IterableBuilderProtocol, ENUM_ITERABLE_OPERATORS
from ..expression_nodes.iterable_expression_nodes import IterableExpressionNode


class IterableExpressionBuilder(BaseExpressionBuilder, IterableBuilderProtocol):
    """
    Mixin providing iterable operations for ExpressionBuilder.

    Implements methods that operate on multiple values:
    - coalesce(): Return first non-null value
    - greatest(): Return maximum value
    - least(): Return minimum value
    """


    def coalesce(self, *others: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """
        Return the first non-null value from multiple expressions.

        Args:
            *others: Additional expressions to check

        Returns:
            New ExpressionBuilder with coalesce node

        Example:
            >>> col("a").coalesce(col("b"), lit(0))  # Returns a if not null, else b if not null, else 0
        """

        operands = [self._node] + [self._to_node_or_value(other) for other in others]
        node = IterableExpressionNode(
            ENUM_ITERABLE_OPERATORS.COALESCE,
            *operands
        )
        return self.create(node)

    def greatest(self, *others: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """
        Return the maximum value across multiple expressions (element-wise).

        Args:
            *others: Additional expressions to compare

        Returns:
            New ExpressionBuilder with greatest node

        Example:
            >>> col("a").greatest(col("b"), col("c"))  # Max of a, b, c for each row
        """

        operands = [self._node] + [self._to_node_or_value(other) for other in others]
        node = IterableExpressionNode(
            ENUM_ITERABLE_OPERATORS.GREATEST,
            *operands
        )
        return self.create(node)

    def least(self, *others: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """
        Return the minimum value across multiple expressions (element-wise).

        Args:
            *others: Additional expressions to compare

        Returns:
            New ExpressionBuilder with least node

        Example:
            >>> col("a").least(col("b"), col("c"))  # Min of a, b, c for each row
        """

        operands = [self._node] + [self._to_node_or_value(other) for other in others]
        node = IterableExpressionNode(
            ENUM_ITERABLE_OPERATORS.LEAST,
            *operands
        )
        return self.create(node)
