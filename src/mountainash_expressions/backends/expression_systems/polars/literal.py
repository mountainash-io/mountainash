"""Polars LiteralExpressionProtocol implementation.

Implements literal/constant value operations for the Polars backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import polars as pl

from .base import PolarsBaseExpressionSystem

if TYPE_CHECKING:
    from mountainash_expressions.core.expression_protocols.substrait.prtcl_literal import (
        LiteralExpressionProtocol,
    )


class PolarsLiteralSystem(PolarsBaseExpressionSystem):
    """Polars implementation of LiteralExpressionProtocol."""

    def lit(self, x: Any) -> pl.Expr:
        """Create a literal value expression.

        Args:
            x: The constant value to wrap as an expression.

        Returns:
            A Polars expression containing the literal value.
        """
        return pl.lit(x)
