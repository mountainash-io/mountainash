"""Narwhals LiteralExpressionProtocol implementation.

Implements literal/constant value operations for the Narwhals backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import narwhals as nw

from ..base import NarwhalsBaseExpressionSystem

from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitLiteralExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.expressions.types import NarwhalsExpr




class SubstraitNarwhalsLiteralExpressionSystem(NarwhalsBaseExpressionSystem, SubstraitLiteralExpressionSystemProtocol[nw.Expr]):
    """Narwhals implementation of LiteralExpressionProtocol."""

    def lit(self, x: Any, /) -> NarwhalsExpr:
        """Create a literal value expression.

        Args:
            x: The constant value to wrap as an expression.

        Returns:
            A Narwhals expression containing the literal value.
        """
        return nw.lit(x)
