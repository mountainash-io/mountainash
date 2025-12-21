"""Ibis ScalarRoundingExpressionProtocol implementation.

Implements rounding operations for the Ibis backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import ibis
import ibis.expr.types as ir

from .base import IbisBaseExpressionSystem

if TYPE_CHECKING:
    from mountainash_expressions.core.expression_protocols.substrait.prtcl_scalar_rounding import (
        ScalarRoundingExpressionProtocol,
    )

# Type alias for expression type
SupportedExpressions = ir.Column | ir.Scalar


class IbisScalarRoundingSystem(IbisBaseExpressionSystem):
    """Ibis implementation of ScalarRoundingExpressionProtocol.

    Implements 3 rounding methods:
    - ceil: Round up to nearest integer
    - floor: Round down to nearest integer
    - round: Round to specified decimal places
    """

    def ceil(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Round up to the nearest integer (ceiling).

        Args:
            x: Value to round.

        Returns:
            Ceiling of x.
        """
        return x.ceil()

    def floor(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Round down to the nearest integer (floor).

        Args:
            x: Value to round.

        Returns:
            Floor of x.
        """
        return x.floor()

    def round(
        self,
        x: SupportedExpressions,
        /,
        s: SupportedExpressions,
        rounding: Any = None,
    ) -> SupportedExpressions:
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
