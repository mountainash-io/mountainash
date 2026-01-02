"""Aggregate operations APIBuilder.

Substrait-aligned implementation using ScalarFunctionNode.
Implements ScalarAggregateBuilderProtocol for aggregate operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..api_builder_base import BaseExpressionAPIBuilder
from ....expression_nodes import ScalarFunctionNode

from mountainash_expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_AGGREGATE
from mountainash_expressions.core.expression_nodes import ScalarFunctionNode, ExpressionNode
from mountainash_expressions.core.expression_protocols.api_builders.extensions_mountainash import MountainAshScalarAggregateAPIBuilderProtocol


if TYPE_CHECKING:
    from ...api_base import BaseExpressionAPI


class MountainAshScalarAggregateAPIBuilder(BaseExpressionAPIBuilder, MountainAshScalarAggregateAPIBuilderProtocol):
    """
    Aggregate operations APIBuilder (Substrait-aligned).

    Provides aggregate operations that typically operate on grouped data.

    Methods:
        count: Count non-null values
        any_value: Select an arbitrary value from the group
    """

    def count(self) -> BaseExpressionAPI:
        """
        Count non-null values.

        Substrait: count

        Returns:
            New ExpressionAPI with count node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.COUNT,
            arguments=[self._node],
        )
        return self._build(node)

    def any_value(
        self,
        ignore_nulls: bool = True,
    ) -> BaseExpressionAPI:
        """
        Select an arbitrary value from the group.

        Substrait: any_value

        Args:
            ignore_nulls: Whether to ignore null values (default: True).

        Returns:
            New ExpressionAPI with any_value node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.ANY_VALUE,
            arguments=[self._node],
            options={"ignore_nulls": ignore_nulls},
        )
        return self._build(node)
