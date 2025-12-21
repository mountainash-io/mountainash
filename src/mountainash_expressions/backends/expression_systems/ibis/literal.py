"""Ibis LiteralExpressionProtocol implementation.

Implements literal/constant value operations for the Ibis backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import ibis
import ibis.expr.types as ir

from .base import IbisBaseExpressionSystem

if TYPE_CHECKING:
    from mountainash_expressions.core.expression_protocols.substrait.prtcl_literal import (
        LiteralExpressionProtocol,
    )

# Type alias for expression type
SupportedExpressions = ir.Column | ir.Scalar


class IbisLiteralSystem(IbisBaseExpressionSystem):
    """Ibis implementation of LiteralExpressionProtocol."""

    def lit(self, x: Any) -> SupportedExpressions:
        """Create a literal value expression.

        Args:
            x: The constant value to wrap as an expression.

        Returns:
            An Ibis expression containing the literal value.
        """
        return ibis.literal(x)
