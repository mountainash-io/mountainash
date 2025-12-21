"""Ibis ConditionalExpressionProtocol implementation.

Implements if-then-else conditional operations for the Ibis backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import ibis
import ibis.expr.types as ir

from .base import IbisBaseExpressionSystem

if TYPE_CHECKING:
    from mountainash_expressions.core.expression_protocols.substrait.prtcl_conditional import (
        ConditionalExpressionProtocol,
    )

# Type alias for expression type
SupportedExpressions = ir.Column | ir.Scalar


class IbisConditionalSystem(IbisBaseExpressionSystem):
    """Ibis implementation of ConditionalExpressionProtocol."""

    def if_then_else(
        self,
        condition: SupportedExpressions,
        if_true: SupportedExpressions,
        if_false: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Create a conditional if-then-else expression.

        Args:
            condition: The boolean condition expression.
            if_true: Expression to use when condition is true.
            if_false: Expression to use when condition is false.

        Returns:
            An Ibis expression implementing the conditional logic.
        """
        return ibis.ifelse(condition, if_true, if_false)
