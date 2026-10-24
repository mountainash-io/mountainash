"""Narwhals CastExpressionProtocol implementation.

Implements type casting operations for the Narwhals backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import narwhals as nw
from mountainash.expressions.backends.expression_systems.narwhals.extensions_mountainash.expsys_nw_ext_ma_scalar_value import _polars_native_transform

from ..base import NarwhalsBaseExpressionSystem
from ..numeric_cast import (
    WRAPPING_STORAGE, checked_cast, checked_member, checks, numeric_target, source_of,
)
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
                _ElementwiseBatchExpr,
            )

            def cast_bound(series):
                # Bind from the existing operand, without sampling or reevaluation.
                source = registry.from_native(series.dtype, self._TARGET)
                target = resolve_dtype_parameters(dtype, source)
                return series.cast(registry.to_native_cast(target, self._TARGET))

            def bind_eager(source):
                return source._from_callable(
                    lambda frame: [cast_bound(series) for series in source(frame)],
                    evaluate_output_names=source._evaluate_output_names,
                    alias_output_names=source._alias_output_names,
                    context=source,
                )

            return _ElementwiseBatchExpr(
                x, None, None, native_polars=False, compliant_transform=bind_eager,
            )
        if needs_source and self.dialect in {"narwhals-duckdb", "narwhals-dask"}:
            from ..extensions_mountainash.expsys_nw_ext_ma_scalar_value import (
                _ElementwiseBatchExpr,
            )

            return _ElementwiseBatchExpr(
                x, None, None, native_polars=False,
                compliant_transform=lambda source: self._bind_lazy_cast(source, dtype),
            )
        native_target = registry.to_native_cast(dtype, self._TARGET)
        numeric = numeric_target(native_target)
        if numeric is not None:
            return self._cast_numeric(x, native_target, numeric)
        evidence = self.native_operand_type("x") if isinstance(native_target, nw.Struct) else None
        if evidence is not None and evidence.native_dtype is not None:
            # Struct leaves narrowing to Float32 follow the same scalar validity.
            checked = checked_member(x, evidence.native_dtype, native_target, self._cast_target)
            if checked is not None:
                return checked.name.keep()
        return self._cast_target(x, native_target)

    def _cast_numeric(self, x: NarwhalsExpr, native_target: object, target: MountainashDtype) -> NarwhalsExpr:
        """Reject newly invalid integer/Float32 conversions without re-reading the source.

        The operand's native dtype, when the visitor can supply one, selects the
        predicates from type domains. Wrapping storage (NumPy/nullable pandas) is
        bound from the evaluated series instead, so an opaque operand runs once.
        Without evidence the same eager binding is used where the compliant
        expression supports it; other expressions keep the plain native cast.
        """
        evidence = self.native_operand_type("x")
        if evidence is None or evidence.native_dtype is None:
            return self._cast_bound_numeric(x, native_target, target)
        source = source_of(evidence.native_dtype)
        if source is None or not checks(source, target):
            return self._cast_target(x, native_target)
        if evidence.descriptor.storage_kind in WRAPPING_STORAGE:
            return self._cast_bound_numeric(x, native_target, target)
        if target is not MountainashDtype.FP32:
            # Polars and Arrow-backed integer casts already raise natively.
            return self._cast_target(x, native_target)
        return checked_cast(x, native_target, source, target)

    def _cast_bound_numeric(self, x: NarwhalsExpr, native_target: object, target: MountainashDtype) -> NarwhalsExpr:
        from ..extensions_mountainash.expsys_nw_ext_ma_scalar_value import _ElementwiseBatchExpr

        def cast_series(series):
            # The evaluated operand's own dtype is the evidence; nothing is sampled.
            source = source_of(series.dtype)
            if source is None or not checks(source, target):
                return series.cast(native_target)
            return checked_cast(
                nw.Series(series, level="full"), native_target, source, target,
            )._compliant_series

        def bind(source):
            if not hasattr(source, "_from_callable"):
                # Preserve native behavior outside the qualified handoff:
                # supported Polars inputs resolve metadata before this path;
                # supported pandas inputs provide this eager binding seam.
                return source.cast(native_target)
            return source._from_callable(
                lambda frame: [cast_series(series) for series in source(frame)],
                evaluate_output_names=source._evaluate_output_names,
                alias_output_names=source._alias_output_names,
                context=source,
            )

        return _ElementwiseBatchExpr(x, None, None, native_polars=False, compliant_transform=bind)

    def _bind_lazy_cast(self, expression, dtype):
        """Resolve lazy operands from bound metadata, never sampled rows."""
        if self.dialect == "narwhals-dask":
            from narwhals._dask.utils import narwhals_to_native_dtype

            def cast_series(series):
                source = registry.from_native(series.dtype, TypeTarget.PANDAS)
                resolved = resolve_dtype_parameters(dtype, source)
                if resolved == dtype:
                    # No source refinement: retain Dask's original defaults and
                    # numeric-to-temporal interpretation.
                    target = narwhals_to_native_dtype(
                        registry.to_native_cast(dtype, self._TARGET), expression._version,
                    )
                else:
                    target = registry.to_native_cast(resolved, TypeTarget.PANDAS)
                return series.astype(target)

            return expression._with_callable(cast_series)

        from narwhals._duckdb.utils import (
            DeferredTimeZone, native_to_narwhals_dtype, narwhals_to_native_dtype,
        )

        def cast_expressions(frame, operands):
            # DuckDB binds a projected relation's types without executing its rows.
            native_types = frame.native.select(*operands).types
            timezone = DeferredTimeZone(frame.native)
            result = []
            for operand, native in zip(operands, native_types, strict=True):
                source = registry.from_native(
                    native_to_narwhals_dtype(native, expression._version, timezone),
                    self._TARGET,
                )
                target = registry.to_native_cast(
                    resolve_dtype_parameters(dtype, source), self._TARGET,
                )
                result.append(operand.cast(
                    narwhals_to_native_dtype(target, expression._version, timezone),
                ))
            return result

        return expression.__class__(
            lambda frame: cast_expressions(frame, expression(frame)),
            lambda frame, inputs: cast_expressions(frame, expression.window_function(frame, inputs)),
            evaluate_output_names=expression._evaluate_output_names,
            alias_output_names=expression._alias_output_names,
            version=expression._version,
        )

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
