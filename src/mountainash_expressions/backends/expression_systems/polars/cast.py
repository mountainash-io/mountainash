"""Polars CastExpressionProtocol implementation.

Implements type casting operations for the Polars backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import polars as pl

from .base import PolarsBaseExpressionSystem

if TYPE_CHECKING:
    from mountainash_expressions.core.expression_protocols.substrait.prtcl_cast import (
        CastExpressionProtocol,
    )


class PolarsCastSystem(PolarsBaseExpressionSystem):
    """Polars implementation of CastExpressionProtocol."""

    def cast(self, x: pl.Expr, /, dtype: Any) -> pl.Expr:
        """Cast an expression to a target data type.

        Args:
            x: The expression to cast.
            dtype: The target data type.

        Returns:
            A Polars expression cast to the specified type.
        """
        return x.cast(dtype)
