"""Polars conditional operations implementation."""

from typing import Any
import polars as pl

from .base import PolarsBaseExpressionSystem
from ....core.protocols.conditional_protocols import ConditionalExpressionProtocol


class PolarsConditionalExpressionSystem(PolarsBaseExpressionSystem, ConditionalExpressionProtocol):
    """Polars implementation of conditional operations."""

    def if_then_else(
        self,
        condition: Any,
        consequence: Any,
        alternative: Any,
    ) -> pl.Expr:
        """
        Create a conditional if-then-else expression.

        Uses Polars' when().then().otherwise() pattern.

        Args:
            condition: Boolean expression for the condition
            consequence: Value if condition is true
            alternative: Value if condition is false

        Returns:
            pl.Expr representing the conditional
        """
        return pl.when(condition).then(consequence).otherwise(alternative)
