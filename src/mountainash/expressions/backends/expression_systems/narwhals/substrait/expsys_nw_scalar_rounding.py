"""Narwhals ScalarRoundingExpressionProtocol implementation.

Implements rounding operations for the Narwhals backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import narwhals as nw

from ..base import NarwhalsBaseExpressionSystem

from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarRoundingExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.expressions.types import NarwhalsExpr


class SubstraitNarwhalsScalarRoundingExpressionSystem(NarwhalsBaseExpressionSystem, SubstraitScalarRoundingExpressionSystemProtocol[nw.Expr]):
    """Narwhals implementation of ScalarRoundingExpressionProtocol.

    Implements 3 rounding methods:
    - ceil: Round up to nearest integer
    - floor: Round down to nearest integer
    - round: Round to specified decimal places
    """

    def ceil(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Round up to the nearest integer (ceiling).

        Args:
            x: Value to round.

        Returns:
            Ceiling of x.
        """
        # Narwhals uses floor + conditional logic for ceiling
        # since it doesn't have a direct ceil method
        floored = x.floor()
        return nw.when(x == floored).then(x).otherwise(floored + nw.lit(1))

    def floor(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Round down to the nearest integer (floor).

        Args:
            x: Value to round.

        Returns:
            Floor of x.
        """
        return x.floor()

    def round(
        self,
        x: NarwhalsExpr,
        /,
        s: int,
        rounding: Any = None,
    ) -> NarwhalsExpr:
        """Round to s decimal places.

        Args:
            x: Value to round.
            s: Number of decimal places (as expression or int).
            rounding: Rounding mode (ignored in Narwhals, uses backend default).

        Returns:
            Rounded value.
        """
        s_val = self._extract_literal_value(s)
        return x.round(int(s_val))
