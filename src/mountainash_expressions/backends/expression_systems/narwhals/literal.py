"""Narwhals LiteralExpressionProtocol implementation.

Implements literal/constant value operations for the Narwhals backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import narwhals as nw

from .base import NarwhalsBaseExpressionSystem

if TYPE_CHECKING:
    from mountainash_expressions.core.expression_protocols.substrait.prtcl_literal import (
        LiteralExpressionProtocol,
    )


class NarwhalsLiteralSystem(NarwhalsBaseExpressionSystem):
    """Narwhals implementation of LiteralExpressionProtocol."""

    def lit(self, x: Any) -> nw.Expr:
        """Create a literal value expression.

        Args:
            x: The constant value to wrap as an expression.

        Returns:
            A Narwhals expression containing the literal value.
        """
        return nw.lit(x)
