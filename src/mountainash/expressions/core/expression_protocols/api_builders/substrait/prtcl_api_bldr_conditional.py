"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash.expressions.core.expression_api import BaseExpressionAPI
    from mountainash.expressions.core.expression_nodes import ExpressionNode



class SubstraitConditionalAPIBuilderProtocol(Protocol):
    """Builder protocol for conditional operations.

    Defines user-facing fluent API methods that create expression nodes.
    Supports the when/then/otherwise chaining pattern.
    """

    def when(
        self,
        condition: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> "SubstraitWhenAPIBuilderProtocol":
        """Start a conditional expression with a condition.

        Substrait: if_then
        """
        ...


class SubstraitWhenAPIBuilderProtocol(Protocol):
    """Protocol for the 'then' step of conditional building."""

    def then(
        self,
        value: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> "SubstraitThenAPIBuilderProtocol":
        """Specify the value when condition is true.

        Substrait: if_then
        """
        ...


class SubstraitThenAPIBuilderProtocol(Protocol):
    """Protocol for completing or continuing conditional building."""

    def when(
        self,
        condition: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> "SubstraitWhenAPIBuilderProtocol":
        """Add another condition (elif).

        Substrait: if_then
        """
        ...

    def otherwise(
        self,
        value: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """Specify the default value (else).

        Substrait: if_then
        """
        ...
