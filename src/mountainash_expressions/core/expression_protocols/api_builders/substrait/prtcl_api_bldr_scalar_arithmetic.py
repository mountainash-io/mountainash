"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol, Union, TYPE_CHECKING

from mountainash_expressions.types import SupportedExpressions


if TYPE_CHECKING:
    from mountainash_expressions.core.expression_api import BaseExpressionAPI
    from mountainash_expressions.core.expression_nodes import ExpressionNode


class SubstraitScalarArithmeticAPIBuilderProtocol(Protocol):
    """Builder protocol for arithmetic operations.

    Defines user-facing fluent API methods that create expression nodes.
    These methods accept flexible inputs and return BaseExpressionAPI for chaining.
    """

    def add(self, other: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Add two values.

        Substrait: add
        """
        ...

    def subtract(self, other: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Subtract one value from another.

        Substrait: subtract
        """
        ...

    def multiply(self, other: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Multiply two values.

        Substrait: multiply
        """
        ...

    def divide(self, other: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Divide x by y.

        Substrait: divide
        """
        ...

    def negate(self) -> BaseExpressionAPI:
        """Negate the value.

        Substrait: negate
        """
        ...

    def modulus(self, other: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Calculate the remainder when dividing by other.

        Substrait: modulus
        """
        ...

    def power(self, other: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Raise to the power of other.

        Substrait: power
        """
        ...
