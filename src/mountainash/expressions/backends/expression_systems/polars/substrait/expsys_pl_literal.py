"""Polars LiteralExpressionProtocol implementation.

Implements literal/constant value operations for the Polars backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import polars as pl

from ..base import PolarsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitLiteralExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.expressions.types import PolarsExpr


class SubstraitPolarsLiteralExpressionSystem(PolarsBaseExpressionSystem, SubstraitLiteralExpressionSystemProtocol[pl.Expr]):
    """Polars implementation of LiteralExpressionProtocol."""

    def lit(self, x: Any, /) -> PolarsExpr:
        """Create a literal value expression.

        Args:
            x: The constant value to wrap as an expression.

        Returns:
            A Polars expression containing the literal value.
        """
        return pl.lit(x)
