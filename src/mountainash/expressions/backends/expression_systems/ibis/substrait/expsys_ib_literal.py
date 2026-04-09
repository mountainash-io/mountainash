"""Ibis LiteralExpressionProtocol implementation.

Implements literal/constant value operations for the Ibis backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import ibis

from ..base import IbisBaseExpressionSystem

from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitLiteralExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.core.types import IbisScalarExpr


class SubstraitIbisLiteralExpressionSystem(IbisBaseExpressionSystem, SubstraitLiteralExpressionSystemProtocol["IbisScalarExpr"]):
    """Ibis implementation of LiteralExpressionProtocol."""

    def lit(self, x: Any, /) -> IbisScalarExpr:
        """Create a literal value expression.

        Args:
            x: The constant value to wrap as an expression.

        Returns:
            An Ibis expression containing the literal value.
        """
        return ibis.literal(x)
