"""Ibis ConditionalExpressionProtocol implementation.

Implements if-then-else conditional operations for the Ibis backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import ibis

from ..base import IbisBaseExpressionSystem
from mountainash_expressions.core.expression_protocols.expression_systems.substrait import SubstraitConditionalExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash_expressions.types import IbisExpr


class SubstraitIbisConditionalExpressionSystem(IbisBaseExpressionSystem, SubstraitConditionalExpressionSystemProtocol):
    """Ibis implementation of ConditionalExpressionProtocol."""

    def if_then_else(
        self,
        condition: IbisExpr,
        if_true: IbisExpr,
        if_false: IbisExpr,
        /,
    ) -> IbisExpr:
        """Create a conditional if-then-else expression.

        Args:
            condition: The boolean condition expression.
            if_true: Expression to use when condition is true.
            if_false: Expression to use when condition is false.

        Returns:
            An Ibis expression implementing the conditional logic.
        """
        return ibis.ifelse(condition, if_true, if_false)
