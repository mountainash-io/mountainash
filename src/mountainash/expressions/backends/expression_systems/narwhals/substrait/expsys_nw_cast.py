"""Narwhals CastExpressionProtocol implementation.

Implements type casting operations for the Narwhals backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Union

import narwhals as nw

from ..base import NarwhalsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitCastExpressionSystemProtocol
from mountainash.core.dtypes import (
    DtypeMappingError,
    MountainashDtype,
    NativeDtype,
    TypeTarget,
    registry,
)

if TYPE_CHECKING:
    from mountainash.expressions.types import NarwhalsExpr


class SubstraitNarwhalsCastExpressionSystem(NarwhalsBaseExpressionSystem, SubstraitCastExpressionSystemProtocol[nw.Expr]):
    """Narwhals implementation of CastExpressionProtocol."""

    _TARGET = TypeTarget.NARWHALS

    def cast(
        self,
        x: NarwhalsExpr,
        /,
        dtype: Union[MountainashDtype, NativeDtype],
        failure_behavior: Literal["throw", "null"] = "throw",
    ) -> NarwhalsExpr:
        """Cast an expression to a canonical or native-passthrough dtype.

        Narwhals' `Expr.cast(dtype)` has no strict/failure-behavior
        parameter (probed against narwhals 2.23.0: the signature is
        `cast(self, dtype)` only) — it always compiles to the equivalent
        of a strict/raising cast on every native backend it wraps (Polars
        raises `InvalidOperationError`, pandas raises `ValueError`).
        `failure_behavior="null"` therefore has no expressible translation
        on this backend and raises `BackendCapabilityError` up front
        rather than attempting a call that would fail with a confusing
        native error. See known-divergences.md.
        """
        if failure_behavior == "null":
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_CAST

            raise BackendCapabilityError(
                "Narwhals Expr.cast has no strict/failure-behavior parameter and always "
                "raises on invalid conversion; null-on-failure casts are not expressible "
                "on the Narwhals backend. Use Polars or Ibis for failure_behavior='null'.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_CAST.CAST,
            )
        if isinstance(dtype, NativeDtype):
            if dtype.target is not self._TARGET:
                raise DtypeMappingError(
                    f"NativeDtype was built from a {dtype.target.value} dtype "
                    f"({dtype.value!r}) and cannot compile on {self._TARGET.value}. "
                    f"Use a canonical dtype for cross-backend expressions."
                )
            return x.cast(dtype.value)
        return x.cast(registry.to_native_cast(dtype, self._TARGET))
