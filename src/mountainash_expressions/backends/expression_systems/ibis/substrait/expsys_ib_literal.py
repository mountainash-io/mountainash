"""Ibis LiteralExpressionProtocol implementation.

Implements literal/constant value operations for the Ibis backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import ibis

from ..base import IbisBaseExpressionSystem

from mountainash_expressions.core.expression_protocols.expression_systems.substrait import SubstraitLiteralExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash_expressions.types import IbisExpr


class SubstraitIbisLiteralExpressionSystem(IbisBaseExpressionSystem, SubstraitLiteralExpressionSystemProtocol):
    """Ibis implementation of LiteralExpressionProtocol."""

    def lit(self, x: Any, /) -> IbisExpr:
        """Create a literal value expression.

        Args:
            x: The constant value to wrap as an expression.

        Returns:
            An Ibis expression containing the literal value.
        """
        return ibis.literal(x)
