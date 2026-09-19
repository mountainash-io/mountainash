"""Narwhals LiteralExpressionProtocol implementation.

Implements literal/constant value operations for the Narwhals backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import narwhals as nw

from ..base import NarwhalsBaseExpressionSystem

from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitLiteralExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.expressions.types import NarwhalsExpr




class SubstraitNarwhalsLiteralExpressionSystem(NarwhalsBaseExpressionSystem, SubstraitLiteralExpressionSystemProtocol[nw.Expr]):
    """Narwhals implementation of LiteralExpressionProtocol."""

    def lit(self, x: Any, /, *, dtype: Any = None) -> NarwhalsExpr:
        """Create a literal value expression with its declared native dtype."""
        if dtype is None:
            return nw.lit(x)
        from mountainash.core.dtypes import TypeTarget, registry

        native_dtype = registry.to_native_cast(dtype, TypeTarget.NARWHALS)
        if x is None and self.dialect == "narwhals-pandas":
            resolved = self.literal_operand_type(x, dtype)
            if resolved.descriptor.storage_kind == "pandas_nullable":
                return self._pandas_typed_expression(
                    nw.lit(None), resolved.native_dtype
                )
        return nw.lit(x, dtype=native_dtype)
