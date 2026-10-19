"""Polars CastExpressionProtocol implementation.

Implements type casting operations for the Polars backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import polars as pl

from ..base import PolarsBaseExpressionSystem
from ..temporal_cast import cast_temporal_compatible
from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitCastExpressionSystemProtocol
from mountainash.core.dtypes import (
    CastTarget, MountainashDtype, SchemaTypeStatus, TypeTarget,
    dtype_is_complete, registry, resolve_dtype_parameters,
)

if TYPE_CHECKING:
    from mountainash.expressions.types import PolarsExpr


class SubstraitPolarsCastExpressionSystem(PolarsBaseExpressionSystem, SubstraitCastExpressionSystemProtocol[pl.Expr]):
    """Polars implementation of CastExpressionProtocol."""

    _TARGET = TypeTarget.POLARS

    def cast(
        self,
        x: PolarsExpr,
        /,
        dtype: CastTarget,
        failure_behavior: Literal["throw", "null"] = "throw",
    ) -> PolarsExpr:
        """Cast an expression to a canonical or native-passthrough dtype.

        `failure_behavior="null"` maps to Polars' `strict=False`, which
        returns null for values that cannot convert instead of raising.
        """
        strict = failure_behavior != "null"
        if dtype is SchemaTypeStatus.UNKNOWN:
            return x
        from mountainash.core.dtypes.canonical import PARAMETERIZED_DTYPES
        if (
            dtype is MountainashDtype.TIMESTAMP
            or dtype is MountainashDtype.DURATION
            or (
                isinstance(dtype, PARAMETERIZED_DTYPES)
                and dtype.native is None and not dtype_is_complete(dtype)
            )
        ):
            return x.pipe_with_dtype(
                lambda expr, native: cast_temporal_compatible(
                    expr,
                    registry.to_native_cast(resolve_dtype_parameters(
                        dtype, registry.from_native(native, self._TARGET),
                    ), self._TARGET),
                    strict=strict,
                )
            )
        return cast_temporal_compatible(x, registry.to_native_cast(dtype, self._TARGET), strict=strict)
