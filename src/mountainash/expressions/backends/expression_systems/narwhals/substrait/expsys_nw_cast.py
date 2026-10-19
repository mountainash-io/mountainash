"""Narwhals CastExpressionProtocol implementation.

Implements type casting operations for the Narwhals backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import narwhals as nw
from mountainash.expressions.backends.expression_systems.narwhals.extensions_mountainash.expsys_nw_ext_ma_scalar_value import _polars_native_transform

from ..base import NarwhalsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitCastExpressionSystemProtocol
from mountainash.core.dtypes import (
    CastTarget, MountainashDtype, SchemaTypeStatus, TypeTarget, dtype_is_complete,
    registry, resolve_dtype_parameters,
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
        dtype: CastTarget,
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
        if dtype is SchemaTypeStatus.UNKNOWN:
            return x
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
        from mountainash.core.dtypes.canonical import PARAMETERIZED_DTYPES
        needs_source = (
            dtype is MountainashDtype.TIMESTAMP
            or dtype is MountainashDtype.DURATION
            or (
                isinstance(dtype, PARAMETERIZED_DTYPES)
                and dtype.native is None and not dtype_is_complete(dtype)
            )
        )
        if needs_source and self.dialect in {"narwhals-polars", "narwhals-lazy"}:
            from narwhals._polars.utils import native_to_narwhals_dtype, narwhals_to_native_dtype
            from narwhals._utils import Version
            from mountainash.expressions.backends.expression_systems.polars.temporal_cast import cast_temporal_compatible

            def cast_partial(bound, native):
                source = registry.from_native(
                    native_to_narwhals_dtype(native, Version.MAIN), TypeTarget.NARWHALS,
                )
                resolved = resolve_dtype_parameters(dtype, source)
                return cast_temporal_compatible(
                    bound,
                    narwhals_to_native_dtype(
                        registry.to_native_cast(resolved, TypeTarget.NARWHALS), Version.MAIN,
                    ),
                    strict=True,
                )

            return _polars_native_transform(
                x, lambda expr: expr.pipe_with_dtype(cast_partial)
            )
        if needs_source and self.dialect in {"narwhals-pandas", "narwhals-pyarrow"}:
            from ..extensions_mountainash.expsys_nw_ext_ma_scalar_value import (
                _pandas_elementwise_batches,
            )

            def cast_bound(series):
                # Bind from the existing operand, without sampling or reevaluation.
                source = registry.from_native(series.dtype, self._TARGET)
                target = resolve_dtype_parameters(dtype, source)
                return series.cast(registry.to_native_cast(target, self._TARGET))

            return _pandas_elementwise_batches(x, cast_bound, None)
        return self._cast_target(x, registry.to_native_cast(dtype, self._TARGET))

    def _cast_target(self, x: NarwhalsExpr, target: object) -> NarwhalsExpr:
        if self.dialect in {"narwhals-polars", "narwhals-lazy"}:
            from narwhals._polars.utils import narwhals_to_native_dtype
            from narwhals._utils import Version
            from mountainash.expressions.backends.expression_systems.polars.temporal_cast import (
                cast_temporal_compatible,
                contains_temporal,
            )

            native_dtype = narwhals_to_native_dtype(target, Version.MAIN)
            if contains_temporal(native_dtype):
                return _polars_native_transform(
                    x,
                    lambda native: cast_temporal_compatible(
                        native, native_dtype, strict=True
                    ),
                )
        return x.cast(target)
