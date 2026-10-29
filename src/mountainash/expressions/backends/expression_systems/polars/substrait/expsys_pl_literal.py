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
        from mountainash.core.dtypes import (
            SchemaTypeStatus, TypeTarget, dtype_is_complete, registry,
            resolve_dtype_parameters,
        )
        from mountainash.core.dtypes.canonical import PARAMETERIZED_DTYPES

        if dtype is None or dtype is SchemaTypeStatus.UNKNOWN:
            return pl.lit(x)
        if isinstance(dtype, PARAMETERIZED_DTYPES) and dtype.native is None and not dtype_is_complete(dtype):
            return pl.lit(x).pipe_with_dtype(
                lambda expr, native: expr.cast(registry.to_native_cast(
                    resolve_dtype_parameters(dtype, registry.from_native(native, TypeTarget.POLARS)),
                    TypeTarget.POLARS,
                ))
            )
        return pl.lit(x, dtype=registry.to_native_cast(dtype, TypeTarget.POLARS))
