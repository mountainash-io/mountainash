"""Ibis conditional operations implementation."""

from typing import Any
import ibis

from .base import IbisBaseExpressionSystem
from ....core.protocols.conditional_protocols import ConditionalExpressionProtocol


class IbisConditionalExpressionSystem(IbisBaseExpressionSystem, ConditionalExpressionProtocol):
    """Ibis implementation of conditional operations."""

    def if_then_else(
        self,
        condition: Any,
        consequence: Any,
        alternative: Any,
    ) -> Any:
        """
        Create a conditional if-then-else expression.

        Uses Ibis' ifelse() method on the condition.

        Args:
            condition: Boolean expression for the condition
            consequence: Value if condition is true
            alternative: Value if condition is false

        Returns:
            Ibis expression representing the conditional
        """
        return ibis.ifelse(condition, consequence, alternative)
