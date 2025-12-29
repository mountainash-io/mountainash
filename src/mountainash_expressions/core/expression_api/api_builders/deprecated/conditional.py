"""Conditional operations namespace.

Substrait-aligned implementation using IfThenNode.

Contains:
- WhenBuilder: Intermediate builder for when().then()
- WhenThenBuilder: Intermediate builder for when().then().otherwise()
- ConditionalNamespace: Method-based conditional operations (if needed)
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Union

from .base import BaseExpressionNamespace
from ...expression_nodes import IfThenNode, LiteralNode

if TYPE_CHECKING:
    from ..expression_api.base import BaseExpressionAPI
    from ...expression_nodes import SubstraitNode


def _to_substrait_node(val: Any) -> SubstraitNode:
    """Helper to convert a value to a SubstraitNode."""
    from ..substrait_nodes import SubstraitNode, LiteralNode

    # Extract node from API instance
    if hasattr(val, '_node'):
        node = val._node
        if isinstance(node, SubstraitNode):
            return node
        # Fallback: wrap in literal (shouldn't happen with new API)
        return LiteralNode(value=val)

    # Already a SubstraitNode
    if isinstance(val, SubstraitNode):
        return val

    # Raw value - wrap in LiteralNode
    return LiteralNode(value=val)


class WhenBuilder:
    """
    Intermediate builder for fluent when().then().otherwise() expressions.

    Returned by the when() entry point function.

    Example:
        >>> expr = when(col("age") > 65).then("senior").otherwise("non-senior")
    """

    def __init__(self, condition: Union[BaseExpressionAPI, SubstraitNode, Any]):
        self._condition = condition

    def then(
        self, consequence: Union[BaseExpressionAPI, SubstraitNode, Any]
    ) -> WhenThenBuilder:
        """
        Specify the value to return if condition is true.

        Args:
            consequence: Value if condition is true

        Returns:
            WhenThenBuilder to continue chain with otherwise()
        """
        return WhenThenBuilder(self._condition, consequence)


class WhenThenBuilder:
    """
    Intermediate builder after then(), requires otherwise() to complete.

    Example:
        >>> expr = when(col("age") > 65).then("senior").otherwise("non-senior")
    """

    def __init__(
        self,
        condition: Union[BaseExpressionAPI, SubstraitNode, Any],
        consequence: Union[BaseExpressionAPI, SubstraitNode, Any],
    ):
        self._condition = condition
        self._consequence = consequence

    def otherwise(
        self, alternative: Union[BaseExpressionAPI, SubstraitNode, Any]
    ) -> BaseExpressionAPI:
        """
        Specify the value to return if condition is false.

        Args:
            alternative: Value if condition is false

        Returns:
            BooleanExpressionAPI with complete conditional expression
        """
        from ..expression_api import BooleanExpressionAPI

        condition_node = _to_substrait_node(self._condition)
        consequence_node = _to_substrait_node(self._consequence)
        alternative_node = _to_substrait_node(alternative)

        node = IfThenNode(
            conditions=[(condition_node, consequence_node)],
            else_clause=alternative_node,
        )
        return BooleanExpressionAPI(node)


class ConditionalNamespace(BaseExpressionNamespace):
    """
    Conditional operations namespace.

    Provides method-based conditional operations on expressions.

    Note: Most conditional operations use the when().then().otherwise()
    pattern via the standalone when() function. This namespace is for
    potential future method-based conditionals.
    """

    pass  # Reserved for future method-based conditionals
