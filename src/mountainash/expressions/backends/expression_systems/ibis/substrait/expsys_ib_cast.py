"""Ibis CastExpressionProtocol implementation.

Implements type casting operations for the Ibis backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Union

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

    def cast(
        self,
        x: IbisValueExpr,
        /,
        dtype: Union[MountainashDtype, NativeDtype],
        failure_behavior: Literal["throw", "null"] = "throw",
    ) -> IbisValueExpr:
        """Cast an expression to a canonical or native-passthrough dtype.

        `failure_behavior="null"` routes through Ibis' `try_cast`, which
        returns null for values that cannot convert instead of raising.
        """
        if isinstance(dtype, NativeDtype):
            if dtype.target is not self._TARGET:
                raise DtypeMappingError(
                    f"NativeDtype was built from a {dtype.target.value} dtype "
                    f"({dtype.value!r}) and cannot compile on {self._TARGET.value}. "
                    f"Use a canonical dtype for cross-backend expressions."
                )
            native_target = dtype.value
        else:
            native_target = registry.to_native_cast(dtype, self._TARGET)
        if failure_behavior == "null":
            return x.try_cast(native_target)
        return x.cast(native_target)
