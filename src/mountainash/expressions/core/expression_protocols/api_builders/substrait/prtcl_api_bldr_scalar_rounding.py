"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Optional, Protocol, Union, TYPE_CHECKING


if TYPE_CHECKING:
    from mountainash.expressions.core.expression_api import BaseExpressionAPI
    from mountainash.expressions.core.expression_nodes import ExpressionNode



class SubstraitScalarRoundingAPIBuilderProtocol(Protocol):
    """Builder protocol for rounding operations.

    Defines user-facing fluent API methods that create expression nodes.
    These methods accept flexible inputs and return BaseExpressionAPI for chaining.
    """

    def ceil(self) -> BaseExpressionAPI:
        """Round up to the nearest integer.

        Substrait: ceil
        """
        ...

    def floor(self) -> BaseExpressionAPI:
        """Round down to the nearest integer.

        Substrait: floor
        """
        ...

    def round(
        self,
        decimals: Optional[Union[BaseExpressionAPI, ExpressionNode, Any, int]] = None,
    ) -> BaseExpressionAPI:
        """Round to the specified number of decimal places.

        Substrait: round
        """
        ...
