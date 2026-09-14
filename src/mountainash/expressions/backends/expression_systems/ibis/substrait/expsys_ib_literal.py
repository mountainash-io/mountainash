"""Ibis LiteralExpressionProtocol implementation.

Implements literal/constant value operations for the Ibis backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import ibis

from ..base import IbisBaseExpressionSystem

from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitLiteralExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.core.types import IbisScalarExpr


class SubstraitIbisLiteralExpressionSystem(IbisBaseExpressionSystem, SubstraitLiteralExpressionSystemProtocol["IbisScalarExpr"]):
    """Ibis implementation of LiteralExpressionProtocol."""

    def lit(self, x: Any, /, *, dtype: Any = None) -> IbisScalarExpr:
        """Create a literal value expression with its declared native dtype."""
        if dtype is None:
            return ibis.literal(x)
        from mountainash.core.dtypes import TypeTarget, registry

        return ibis.literal(
            x, type=registry.to_native_cast(dtype, TypeTarget.IBIS)
        )
