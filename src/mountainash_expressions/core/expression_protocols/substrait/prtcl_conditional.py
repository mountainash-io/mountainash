"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol, Union, TYPE_CHECKING

# Placeholder - use your actual type
SupportedExpressions = Any

if TYPE_CHECKING:
    from ...expression_nodes import ExpressionNode
    from ...expression_api.api_namespaces import BaseExpressionNamespace as BaseNamespace


class ConditionalExpressionProtocol(Protocol):
    """Protocol for conditional operations.

    Auto-generated from Substrait conditional extension.
    """

    def if_then_else(
        self,
        condition: SupportedExpressions,
        if_true: SupportedExpressions,
        if_false: SupportedExpressions, /
    ) -> SupportedExpressions:
        """Create a conditional if-then-else expression.

        Substrait: if_then
        """
        ...


class ConditionalBuilderProtocol(Protocol):
    """Builder protocol for conditional operations.

    Defines user-facing fluent API methods that create expression nodes.
    Supports the when/then/otherwise chaining pattern.
    """

    def when(
        self,
        condition: Union["BaseNamespace", "ExpressionNode", Any],
    ) -> "WhenBuilderProtocol":
        """Start a conditional expression with a condition.

        Substrait: if_then
        """
        ...


class WhenBuilderProtocol(Protocol):
    """Protocol for the 'then' step of conditional building."""

    def then(
        self,
        value: Union["BaseNamespace", "ExpressionNode", Any],
    ) -> "ThenBuilderProtocol":
        """Specify the value when condition is true.

        Substrait: if_then
        """
        ...


class ThenBuilderProtocol(Protocol):
    """Protocol for completing or continuing conditional building."""

    def when(
        self,
        condition: Union["BaseNamespace", "ExpressionNode", Any],
    ) -> "WhenBuilderProtocol":
        """Add another condition (elif).

        Substrait: if_then
        """
        ...

    def otherwise(
        self,
        value: Union["BaseNamespace", "ExpressionNode", Any],
    ) -> "BaseNamespace":
        """Specify the default value (else).

        Substrait: if_then
        """
        ...
