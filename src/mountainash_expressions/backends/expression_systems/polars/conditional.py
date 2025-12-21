"""Polars ConditionalExpressionProtocol implementation.

Implements if-then-else conditional operations for the Polars backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import polars as pl

from .base import PolarsBaseExpressionSystem

if TYPE_CHECKING:
    from mountainash_expressions.core.expression_protocols.substrait.prtcl_conditional import (
        ConditionalExpressionProtocol,
    )


class PolarsConditionalSystem(PolarsBaseExpressionSystem):
    """Polars implementation of ConditionalExpressionProtocol."""

    def if_then_else(
        self,
        condition: pl.Expr,
        if_true: pl.Expr,
        if_false: pl.Expr,
        /,
    ) -> pl.Expr:
        """Create a conditional if-then-else expression.

        Args:
            condition: The boolean condition expression.
            if_true: Expression to use when condition is true.
            if_false: Expression to use when condition is false.

        Returns:
            A Polars expression implementing the conditional logic.
        """
        return pl.when(condition).then(if_true).otherwise(if_false)
