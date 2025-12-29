"""Set operations APIBuilder.

Substrait-aligned implementation using ScalarFunctionNode.
Implements ScalarSetBuilderProtocol for set membership operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from ..api_builder_base import BaseExpressionAPIBuilder

from mountainash_expressions.core.expression_system.function_keys.enums import KEY_SCALAR_SET
from mountainash_expressions.core.expression_nodes import ScalarFunctionNode, ExpressionNode, LiteralNode, SingularOrListNode
from mountainash_expressions.core.expression_protocols.api_builders.substrait import SubstraitScalarSetAPIBuilderProtocol


if TYPE_CHECKING:
    from mountainash_expressions.core.expression_nodes import ExpressionNode, ScalarFunctionNode

    from ...api_base import BaseExpressionAPI
    from ....expression_nodes import ExpressionNode


class SubstraitScalarSetAPIBuilder(BaseExpressionAPIBuilder, SubstraitScalarSetAPIBuilderProtocol):
    """
    Set operations APIBuilder (Substrait-aligned).

    Provides set membership operations.

    Methods:
        is_in: Check if value is in a set of values
        is_not_in: Check if value is not in a set of values
        index_in: Get 0-indexed position in set (-1 if not found)
    """

    def is_in(
        self,
        *values: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Check if value is in the given set of values.

        Substrait: index_in (returns bool based on >= 0)

        Args:
            *values: Values to check membership against.

        Returns:
            New ExpressionAPI with is_in node.
        """
        # Convert values to LiteralNodes if they're plain values
        options = []
        for v in values:
            if hasattr(v, "_node"):
                options.append(v._node)
            elif hasattr(v, "operator"):  # ExpressionNode
                options.append(v)
            else:
                options.append(LiteralNode(value=v))

        node = SingularOrListNode(
            value=self._node,
            options=options,
        )
        return self._build(node)

    def is_not_in(
        self,
        *values: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Check if value is not in the given set of values.

        Substrait: index_in (returns bool based on < 0)

        Args:
            *values: Values to check membership against.

        Returns:
            New ExpressionAPI with is_not_in node.
        """
        # is_not_in is NOT(is_in(...))
        is_in_result = self.is_in(*values)
        return is_in_result.not_()

    def index_in(
        self,
        *values: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Return 0-indexed position in values, or -1 if not found.

        Substrait: index_in

        Args:
            *values: Values to search in.

        Returns:
            New ExpressionAPI with index_in node.
        """
        value_nodes = [self._to_substrait_node(v) for v in values]
        node = ScalarFunctionNode(
            function_key=KEY_SCALAR_SET.INDEX_IN,
            arguments=[self._node] + value_nodes,
        )
        return self._build(node)
