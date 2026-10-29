"""Ibis CastExpressionProtocol implementation.

Implements type casting operations for the Ibis backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from ..base import IbisBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitCastExpressionSystemProtocol
from mountainash.core.dtypes import (
    CastTarget, MountainashDtype, SchemaTypeStatus, TypeTarget, dtype_is_complete, registry,
    resolve_dtype_parameters,
)

if TYPE_CHECKING:
    from mountainash.core.types import IbisValueExpr


class SubstraitIbisCastExpressionSystem(IbisBaseExpressionSystem, SubstraitCastExpressionSystemProtocol["IbisValueExpr"]):
    """Ibis implementation of CastExpressionProtocol."""

    _TARGET = TypeTarget.IBIS

    def cast(
        self,
        x: IbisValueExpr,
        /,
        dtype: CastTarget,
        failure_behavior: Literal["throw", "null"] = "throw",
    ) -> IbisValueExpr:
        """Cast an expression to a canonical or native-passthrough dtype.

        `failure_behavior="null"` routes through Ibis' `try_cast`, which
        returns null for values that cannot convert instead of raising.
        """
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
            from ibis.common.deferred import Deferred, deferrable
            if isinstance(x, Deferred):
                return deferrable(
                    lambda bound: self.cast(bound, dtype=dtype, failure_behavior=failure_behavior)
                )(x)
            dtype = resolve_dtype_parameters(
                dtype, registry.from_native(x.type(), self._TARGET),
            )
        native_target = registry.to_native_cast(dtype, self._TARGET)
        if failure_behavior == "null":
            return x.try_cast(native_target)
        return x.cast(native_target)
