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

    def lit(self, x: Any, /, *, dtype: Any = None) -> PolarsExpr:
        """Create a literal value expression with its declared native dtype."""
        if dtype is None:
            return pl.lit(x)
        from mountainash.core.dtypes import TypeTarget, registry

        return pl.lit(x, dtype=registry.to_native_cast(dtype, TypeTarget.POLARS))
