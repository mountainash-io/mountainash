"""Ibis ScalarRoundingExpressionProtocol implementation.

Implements rounding operations for the Ibis backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import ibis

from ..base import IbisBaseExpressionSystem

from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarRoundingExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.expressions.types import IbisExpr


class SubstraitIbisScalarRoundingExpressionSystem(IbisBaseExpressionSystem, SubstraitScalarRoundingExpressionSystemProtocol):
    """Ibis implementation of ScalarRoundingExpressionProtocol.

    Implements 3 rounding methods:
    - ceil: Round up to nearest integer
    - floor: Round down to nearest integer
    - round: Round to specified decimal places
    """

    def ceil(self, x: IbisExpr, /) -> IbisExpr:
        """Round up to the nearest integer (ceiling).

        Args:
            x: Value to round.

        Returns:
            Ceiling of x.
        """
        return x.ceil()

    def floor(self, x: IbisExpr, /) -> IbisExpr:
        """Round down to the nearest integer (floor).

        Args:
            x: Value to round.

        Returns:
            Floor of x.
        """
        return x.floor()

    def round(
        self,
        x: IbisExpr,
        /,
        s: int,
        rounding: Any = None,
    ) -> IbisExpr:
        """Round to s decimal places.

        Args:
            x: Value to round.
            s: Number of decimal places (as expression or int).
            rounding: Rounding mode (ignored in Ibis, uses backend default).

        Returns:
            Rounded value.
        """
        s_val = self._extract_literal_value(s)
        return x.round(int(s_val))
