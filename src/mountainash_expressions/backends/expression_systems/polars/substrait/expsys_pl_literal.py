"""Polars LiteralExpressionProtocol implementation.

Implements literal/constant value operations for the Polars backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import polars as pl

from ..base import PolarsBaseExpressionSystem
from mountainash_expressions.core.expression_protocols.expression_systems.substrait import SubstraitCastExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash_expressions.types import PolarsExpr


class PolarsLiteralExpressionSystem(PolarsBaseExpressionSystem, LiteralExpressionProtocol):
    """Polars implementation of LiteralExpressionProtocol."""

    def lit(self, x: Any) -> PolarsExpr:
        """Create a literal value expression.

        Args:
            x: The constant value to wrap as an expression.

        Returns:
            A Polars expression containing the literal value.
        """
        return pl.lit(x)
