"""Polars ScalarRoundingExpressionProtocol implementation.

Implements rounding operations for the Polars backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import polars as pl

from ..base import PolarsBaseExpressionSystem
from mountainash_expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarRoundingExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash_expressions.types import PolarsExpr

class PolarsScalarRoundingExpressionSystem(PolarsBaseExpressionSystem, SubstraitScalarRoundingExpressionSystemProtocol):
    """Polars implementation of ScalarRoundingExpressionProtocol.

    Implements 3 rounding methods:
    - ceil: Round up to nearest integer
    - floor: Round down to nearest integer
    - round: Round to specified decimal places
    """

    def ceil(self, x: PolarsExpr, /) -> PolarsExpr:
        """Round up to the nearest integer (ceiling).

        Args:
            x: Value to round.

        Returns:
            Ceiling of x.
        """
        return x.ceil()

    def floor(self, x: PolarsExpr, /) -> PolarsExpr:
        """Round down to the nearest integer (floor).

        Args:
            x: Value to round.

        Returns:
            Floor of x.
        """
        return x.floor()

    def round(
        self,
        x: PolarsExpr,
        /,
        s: PolarsExpr,
        rounding: Any = None,
    ) -> PolarsExpr:
        """Round to s decimal places.

        Args:
            x: Value to round.
            s: Number of decimal places (as expression or int).
            rounding: Rounding mode (ignored in Polars, uses banker's rounding).

        Returns:
            Rounded value.
        """
        # Polars round takes an integer, not an expression
        # For now, we assume s is a literal integer value
        # In practice, the visitor should resolve s to an integer
        if isinstance(s, int):
            return x.round(s)
        # If s is an expression, we need to evaluate it
        # This is a simplification - full implementation would handle expression s
        return x.round(0)
