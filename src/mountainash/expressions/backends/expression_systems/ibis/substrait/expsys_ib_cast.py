"""Ibis CastExpressionProtocol implementation.

Implements type casting operations for the Ibis backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

from ..base import IbisBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitCastExpressionSystemProtocol
from mountainash.core.dtypes import (
    DtypeMappingError,
    MountainashDtype,
    NativeDtype,
    TypeTarget,
    registry,
)

if TYPE_CHECKING:
    from mountainash.core.types import IbisValueExpr


class SubstraitIbisCastExpressionSystem(IbisBaseExpressionSystem, SubstraitCastExpressionSystemProtocol["IbisValueExpr"]):
    """Ibis implementation of CastExpressionProtocol."""

    _TARGET = TypeTarget.IBIS

    def cast(self, x: IbisValueExpr, /, dtype: Union[MountainashDtype, NativeDtype]) -> IbisValueExpr:
        """Cast an expression to a canonical or native-passthrough dtype."""
        if isinstance(dtype, NativeDtype):
            if dtype.target is not self._TARGET:
                raise DtypeMappingError(
                    f"NativeDtype was built from a {dtype.target.value} dtype "
                    f"({dtype.value!r}) and cannot compile on {self._TARGET.value}. "
                    f"Use a canonical dtype for cross-backend expressions."
                )
            return x.cast(dtype.value)
        return x.cast(registry.to_native_cast(dtype, self._TARGET))
