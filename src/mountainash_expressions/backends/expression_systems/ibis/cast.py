"""Ibis CastExpressionProtocol implementation.

Implements type casting operations for the Ibis backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import ibis
import ibis.expr.types as ir

from .base import IbisBaseExpressionSystem

if TYPE_CHECKING:
    from mountainash_expressions.core.expression_protocols.substrait.prtcl_cast import (
        CastExpressionProtocol,
    )

# Type alias for expression type
SupportedExpressions = ir.Column | ir.Scalar


class IbisCastSystem(IbisBaseExpressionSystem):
    """Ibis implementation of CastExpressionProtocol."""

    def cast(self, x: SupportedExpressions, /, dtype: Any) -> SupportedExpressions:
        """Cast an expression to a target data type.

        Args:
            x: The expression to cast.
            dtype: The target data type.

        Returns:
            An Ibis expression cast to the specified type.
        """
        return x.cast(dtype)
