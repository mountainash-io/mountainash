"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol, Union, TYPE_CHECKING


if TYPE_CHECKING:
    from mountainash_expressions.core.expression_api import BaseExpressionAPI
    from mountainash_expressions.core.expression_nodes import ExpressionNode



class SubstraitScalarLogarithmicAPIBuilderProtocol(Protocol):
    """Builder protocol for logarithmic operations.

    Defines user-facing fluent API methods that create expression nodes.
    These methods accept flexible inputs and return BaseExpressionAPI for chaining.
    """

    def ln(self) -> BaseExpressionAPI:
        """Natural logarithm (base e).

        Substrait: ln
        """
        ...

    def log10(self) -> BaseExpressionAPI:
        """Logarithm base 10.

        Substrait: log10
        """
        ...

    def log2(self) -> BaseExpressionAPI:
        """Logarithm base 2.

        Substrait: log2
        """
        ...

    def log(
        self,
        base: Union[BaseExpressionAPI, ExpressionNode, Any, float],
    ) -> BaseExpressionAPI:
        """Logarithm with custom base.

        Substrait: logb
        """
        ...
