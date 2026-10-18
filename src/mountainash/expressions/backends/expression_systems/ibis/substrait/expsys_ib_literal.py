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
        from mountainash.core.dtypes import (
            SchemaTypeStatus, TypeTarget, dtype_is_complete, registry,
            resolve_dtype_parameters,
        )
        from mountainash.core.dtypes.canonical import PARAMETERIZED_DTYPES

        if dtype is None or dtype is SchemaTypeStatus.UNKNOWN:
            return ibis.literal(x)
        if isinstance(dtype, PARAMETERIZED_DTYPES) and dtype.native is None and not dtype_is_complete(dtype):
            source = registry.from_native(ibis.literal(x).type(), TypeTarget.IBIS)
            dtype = resolve_dtype_parameters(dtype, source)
        return ibis.literal(x, type=registry.to_native_cast(dtype, TypeTarget.IBIS))
