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



class SubstraitScalarBooleanAPIBuilderProtocol(Protocol):
    """Builder protocol for boolean operations.

    Defines user-facing fluent API methods that create expression nodes.
    These methods accept flexible inputs and return BaseExpressionAPI for chaining.
    """

    def and_(self, *others: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Boolean AND using Kleene logic.

        Substrait: and
        """
        ...


    def or_(self, *others: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Boolean OR using Kleene logic.

        Substrait: or
        """
        ...



    def not_(self) -> BaseExpressionAPI:
        """Boolean NOT.

        Substrait: not
        """
        ...

    def xor(self, other: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Boolean XOR using Kleene logic.

        Substrait: xor
        """
        ...

    def and_not(self, other: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Boolean AND of this value and the negation of other.

        Substrait: and_not
        """
        ...
