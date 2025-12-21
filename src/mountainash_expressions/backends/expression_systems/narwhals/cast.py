"""Narwhals CastExpressionProtocol implementation.

Implements type casting operations for the Narwhals backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import narwhals as nw

from .base import NarwhalsBaseExpressionSystem

if TYPE_CHECKING:
    from mountainash_expressions.core.expression_protocols.substrait.prtcl_cast import (
        CastExpressionProtocol,
    )


class NarwhalsCastSystem(NarwhalsBaseExpressionSystem):
    """Narwhals implementation of CastExpressionProtocol."""

    def cast(self, x: nw.Expr, /, dtype: Any) -> nw.Expr:
        """Cast an expression to a target data type.

        Args:
            x: The expression to cast.
            dtype: The target data type.

        Returns:
            A Narwhals expression cast to the specified type.
        """
        return x.cast(dtype)
