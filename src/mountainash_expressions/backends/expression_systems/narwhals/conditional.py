"""Narwhals ConditionalExpressionProtocol implementation.

Implements if-then-else conditional operations for the Narwhals backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import narwhals as nw

from .base import NarwhalsBaseExpressionSystem

if TYPE_CHECKING:
    from mountainash_expressions.core.expression_protocols.substrait.prtcl_conditional import (
        ConditionalExpressionProtocol,
    )


class NarwhalsConditionalSystem(NarwhalsBaseExpressionSystem):
    """Narwhals implementation of ConditionalExpressionProtocol."""

    def if_then_else(
        self,
        condition: nw.Expr,
        if_true: nw.Expr,
        if_false: nw.Expr,
        /,
    ) -> nw.Expr:
        """Create a conditional if-then-else expression.

        Args:
            condition: The boolean condition expression.
            if_true: Expression to use when condition is true.
            if_false: Expression to use when condition is false.

        Returns:
            A Narwhals expression implementing the conditional logic.
        """
        return nw.when(condition).then(if_true).otherwise(if_false)
