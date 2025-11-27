"""Narwhals conditional operations implementation."""

from typing import Any
import narwhals as nw

from .base import NarwhalsBaseExpressionSystem
from ....core.protocols.conditional_protocols import ConditionalExpressionProtocol


class NarwhalsConditionalExpressionSystem(NarwhalsBaseExpressionSystem, ConditionalExpressionProtocol):
    """Narwhals implementation of conditional operations."""

    def if_then_else(
        self,
        condition: Any,
        consequence: Any,
        alternative: Any,
    ) -> nw.Expr:
        """
        Create a conditional if-then-else expression.

        Uses Narwhals' when().then().otherwise() pattern.

        Args:
            condition: Boolean expression for the condition
            consequence: Value if condition is true
            alternative: Value if condition is false

        Returns:
            nw.Expr representing the conditional
        """
        return nw.when(condition).then(consequence).otherwise(alternative)
