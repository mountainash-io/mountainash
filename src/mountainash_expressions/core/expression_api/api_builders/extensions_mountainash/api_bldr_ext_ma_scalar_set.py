"""Set operations APIBuilder.

Substrait-aligned implementation using ScalarFunctionNode.
Implements ScalarSetBuilderProtocol for set membership operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from ..api_builder_base import BaseExpressionAPIBuilder

from mountainash_expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_SET, FKEY_MOUNTAINASH_SCALAR_SET
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

    def _flatten_values(self, values):
        """Flatten values — handle both is_in([a,b,c]) and is_in(a,b,c)."""
        if len(values) == 1 and isinstance(values[0], (list, tuple, set, frozenset)):
            return list(values[0])
        return list(values)

    def is_in(
        self,
        *values: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Check if value is in the given set of values.

        Args:
            *values: Values to check membership against. Can be individual
                     values or a single list/tuple/set.

        Returns:
            New ExpressionAPI with is_in node.
        """
        flat_values = self._flatten_values(values)
        value_nodes = [self._to_substrait_node(v) for v in flat_values]
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_SET.IS_IN,
            arguments=[self._node] + value_nodes,
        )
        return self._build(node)

    def is_not_in(
        self,
        *values: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Check if value is not in the given set of values.

        Args:
            *values: Values to check membership against. Can be individual
                     values or a single list/tuple/set.

        Returns:
            New ExpressionAPI with is_not_in node.
        """
        flat_values = self._flatten_values(values)
        value_nodes = [self._to_substrait_node(v) for v in flat_values]
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_SET.IS_NOT_IN,
            arguments=[self._node] + value_nodes,
        )
        return self._build(node)
