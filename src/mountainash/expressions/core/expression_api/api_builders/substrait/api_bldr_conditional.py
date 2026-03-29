"""Conditional operations APIBuilder.

Substrait-aligned implementation using IfThenNode.
Implements ConditionalBuilderProtocol for conditional expressions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Tuple, Union

from ..api_builder_base import BaseExpressionAPIBuilder

from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_CONDITIONAL
from mountainash.expressions.core.expression_nodes import IfThenNode, LiteralNode, ExpressionNode
from mountainash.expressions.core.expression_protocols.api_builders.substrait import SubstraitConditionalAPIBuilderProtocol, SubstraitWhenAPIBuilderProtocol, SubstraitThenAPIBuilderProtocol


if TYPE_CHECKING:
    from ...api_base import BaseExpressionAPI
    from ....expression_nodes import ExpressionNode


class SubstraitWhenAPIBuilder(BaseExpressionAPIBuilder, SubstraitWhenAPIBuilderProtocol):
    """
    Builder for the 'then' step of conditional building.

    Created by ConditionalAPIBuilder.when() or ThenBuilder.when().
    """

    def __init__(
        self,
        condition: "ExpressionNode",
        prior_conditions: List[Tuple["ExpressionNode", "ExpressionNode"]],
        expression_api_class: type,
    ):
        """
        Initialize WhenBuilder.

        Args:
            condition: The current condition node.
            prior_conditions: List of (condition, result) pairs from previous when/then.
            expression_api_class: The ExpressionAPI class to use for building results.
        """
        self._condition = condition
        self._prior_conditions = prior_conditions
        self._expression_api_class = expression_api_class

    def then(
        self,
        value: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> "SubstraitThenAPIBuilder":
        """
        Specify the value when condition is true.

        Substrait: if_then

        Args:
            value: The value to return when condition is true.
                Can be an ExpressionAPI, ExpressionNode, or literal value.

        Returns:
            ThenBuilder for continuing the conditional chain.
        """
        # Convert value to node
        value_node = _to_node(value)

        # Add this condition/value pair to the list
        conditions = self._prior_conditions + [(self._condition, value_node)]

        return SubstraitThenAPIBuilder(
            conditions=conditions,
            expression_api_class=self._expression_api_class,
        )


class SubstraitThenAPIBuilder(BaseExpressionAPIBuilder, SubstraitThenAPIBuilderProtocol):
    """
    Builder for completing or continuing conditional building.

    Created by WhenBuilder.then().
    """

    def __init__(
        self,
        conditions: List[Tuple["ExpressionNode", "ExpressionNode"]],
        expression_api_class: type,
    ):
        """
        Initialize ThenBuilder.

        Args:
            conditions: List of (condition, result) pairs accumulated so far.
            expression_api_class: The ExpressionAPI class to use for building results.
        """
        self._conditions = conditions
        self._expression_api_class = expression_api_class

    def when(
        self,
        condition: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> "SubstraitWhenAPIBuilder":
        """
        Add another condition (elif).

        Substrait: if_then

        Args:
            condition: The next condition to check.
                Can be an ExpressionAPI, ExpressionNode, or literal value.

        Returns:
            WhenBuilder for specifying the value for this condition.
        """
        condition_node = _to_node(condition)

        return SubstraitWhenAPIBuilder(
            condition=condition_node,
            prior_conditions=self._conditions,
            expression_api_class=self._expression_api_class,
        )

    def otherwise(
        self,
        value: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Specify the default value (else).

        Substrait: if_then

        Args:
            value: The value to return when no conditions match.
                Can be an ExpressionAPI, ExpressionNode, or literal value.

        Returns:
            New ExpressionAPI with the complete conditional expression.
        """
        else_node = _to_node(value)

        node = IfThenNode(
            conditions=self._conditions,
            else_clause=else_node,
        )

        return self._expression_api_class(node)


class SubstraitConditionalAPIBuilder(BaseExpressionAPIBuilder, SubstraitConditionalAPIBuilderProtocol):
    """
    Conditional operations APIBuilder (Substrait-aligned).

    Provides conditional when/then/otherwise expressions.

    Methods:
        when: Start a conditional expression with a condition

    Example:
        >>> col("age").when(col("age").lt(18)).then("minor").otherwise("adult")
    """

    def when(
        self,
        condition: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> "SubstraitWhenAPIBuilder":
        """
        Start a conditional expression with a condition.

        Substrait: if_then

        This begins a when/then/otherwise chain. You can chain multiple
        when/then pairs before the final otherwise.

        Args:
            condition: The condition to check.
                Can be an ExpressionAPI, ExpressionNode, or literal value.

        Returns:
            WhenBuilder for specifying the value when condition is true.

        Examples:
            >>> # Simple if-then-else
            >>> col("score").when(col("score").gt(90)).then("A").otherwise("B")

            >>> # Chained conditions (elif)
            >>> col("score").when(col("score").gt(90)).then("A") \\
            ...     .when(col("score").gt(80)).then("B") \\
            ...     .when(col("score").gt(70)).then("C") \\
            ...     .otherwise("F")
        """
        condition_node = _to_node(condition)

        # Get the ExpressionAPI class from the current instance
        expression_api_class = type(self._api)

        return SubstraitWhenAPIBuilder(
            condition=condition_node,
            prior_conditions=[],
            expression_api_class=expression_api_class,
        )


def _to_node(value: Union[BaseExpressionAPI, "ExpressionNode", Any]) -> "ExpressionNode":
    """
    Convert a value to an ExpressionNode.

    Args:
        value: Can be an ExpressionAPI, ExpressionNode, or literal value.

    Returns:
        ExpressionNode representation of the value.
    """
    if hasattr(value, "_node"):
        # It's an ExpressionAPI - extract the node
        return value._node
    elif hasattr(value, "accept"):
        # It's already an ExpressionNode (has visitor pattern method)
        return value
    else:
        # It's a literal value - wrap in LiteralNode
        return LiteralNode(value=value)
