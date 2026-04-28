"""List operations API builder."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from ..api_builder_base import BaseExpressionAPIBuilder
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_LIST
from mountainash.expressions.core.expression_nodes import ScalarFunctionNode

if TYPE_CHECKING:
    from ...api_base import BaseExpressionAPI


class MountainAshScalarListAPIBuilder(BaseExpressionAPIBuilder):
    """API builder for the .list namespace."""

    def sum(self) -> BaseExpressionAPI:
        """Sum all elements in each list."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.SUM,
            arguments=[self._node],
        )
        return self._build(node)

    def min(self) -> BaseExpressionAPI:
        """Minimum element in each list."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.MIN,
            arguments=[self._node],
        )
        return self._build(node)

    def max(self) -> BaseExpressionAPI:
        """Maximum element in each list."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.MAX,
            arguments=[self._node],
        )
        return self._build(node)

    def mean(self) -> BaseExpressionAPI:
        """Mean of elements in each list."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.MEAN,
            arguments=[self._node],
        )
        return self._build(node)

    def len(self) -> BaseExpressionAPI:
        """Count of elements in each list."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.LEN,
            arguments=[self._node],
        )
        return self._build(node)

    def contains(self, item: Union[BaseExpressionAPI, Any]) -> BaseExpressionAPI:
        """Check if each list contains the given item.

        Args:
            item: Value or expression to search for.
        """
        item_node = self._to_substrait_node(item)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.CONTAINS,
            arguments=[self._node, item_node],
        )
        return self._build(node)

    def sort(self, *, descending: bool = False) -> BaseExpressionAPI:
        """Sort elements in each list.

        Args:
            descending: Sort in descending order. Not supported on Ibis.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.SORT,
            arguments=[self._node],
            options={"descending": descending},
        )
        return self._build(node)

    def unique(self) -> BaseExpressionAPI:
        """Distinct elements in each list."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.UNIQUE,
            arguments=[self._node],
        )
        return self._build(node)
