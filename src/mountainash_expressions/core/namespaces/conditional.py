"""Conditional operations namespace.

Contains:
- WhenBuilder: Intermediate builder for when().then()
- WhenThenBuilder: Intermediate builder for when().then().otherwise()
- ConditionalNamespace: Method-based conditional operations (if needed)
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Union

from .base import BaseNamespace
from ..protocols.conditional_protocols import ENUM_CONDITIONAL_OPERATORS
from ..expression_nodes.conditional_expression_nodes import ConditionalExpressionNode

if TYPE_CHECKING:
    from ..expression_api.base import BaseExpressionAPI
    from ..expression_nodes.base_expression_node import ExpressionNode


class WhenBuilder:
    """
    Intermediate builder for fluent when().then().otherwise() expressions.

    Returned by the when() entry point function.

    Example:
        >>> expr = when(col("age") > 65).then("senior").otherwise("non-senior")
    """

    def __init__(self, condition: Union[BaseExpressionAPI, ExpressionNode, Any]):
        self._condition = condition

    def then(
        self, consequence: Union[BaseExpressionAPI, ExpressionNode, Any]
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
        condition: Union[BaseExpressionAPI, ExpressionNode, Any],
        consequence: Union[BaseExpressionAPI, ExpressionNode, Any],
    ):
        self._condition = condition
        self._consequence = consequence

    def otherwise(
        self, alternative: Union[BaseExpressionAPI, ExpressionNode, Any]
    ) -> BaseExpressionAPI:
        """
        Specify the value to return if condition is false.

        Args:
            alternative: Value if condition is false

        Returns:
            BooleanExpressionAPI with complete conditional expression
        """
        from ..expression_api import BooleanExpressionAPI

        # Helper to convert value to node
        def to_node(val: Any) -> Any:
            if hasattr(val, '_node'):
                return val._node
            else:
                # Wrap literals
                from .entrypoints import lit
                return lit(val)._node

        condition_node = to_node(self._condition)
        consequence_node = to_node(self._consequence)
        alternative_node = to_node(alternative)

        node = ConditionalExpressionNode(
            ENUM_CONDITIONAL_OPERATORS.IF_THEN_ELSE,
            condition=condition_node,
            consequence=consequence_node,
            alternative=alternative_node,
        )
        return BooleanExpressionAPI(node)


class ConditionalNamespace(BaseNamespace):
    """
    Conditional operations namespace.

    Provides method-based conditional operations on expressions.

    Note: Most conditional operations use the when().then().otherwise()
    pattern via the standalone when() function. This namespace is for
    potential future method-based conditionals.
    """

    pass  # Reserved for future method-based conditionals
