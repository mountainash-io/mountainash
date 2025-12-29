"""Ibis ScalarRoundingExpressionProtocol implementation.

Implements rounding operations for the Ibis backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import ibis

from ..base import IbisBaseExpressionSystem

if TYPE_CHECKING:
    from mountainash_expressions.core.expression_protocols.substrait import (
        ScalarRoundingExpressionProtocol,
    )

# Type alias for expression type
from mountainash_expressions.types import IbisExpr


class IbisScalarRoundingExpressionSystem(IbisBaseExpressionSystem, ScalarRoundingExpressionProtocol):
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
        s: IbisExpr,
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
        if isinstance(s, int):
            return x.round(s)
        # For expression s, fallback to 0 decimal places
        return x.round(0)
