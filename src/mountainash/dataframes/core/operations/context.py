"""
Unified operation context and resolver for cross-backend operations.

This module provides:
- OperationContext: Encapsulates prepared DataFrame and input for an operation
- OperationResolver: Resolves any DataFrame + input combination for cross-backend compatibility

The resolver handles:
- Expression resolution (wrapping DataFrames in Narwhals for nw.Expr)
- Series resolution (converting series to match DataFrame backend)
- Unwrapping results back to original DataFrame type
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable

from ..constants import Backend, InputType, EXPRESSION_BACKENDS
from .detection import InputDetector, DetectedInput

logger = logging.getLogger(__name__)


# Identity function for when no transformation is needed
_identity: Callable[[Any], Any] = lambda x: x


@dataclass
class OperationContext:
    """
    Unified context for cross-backend operations.

    Encapsulates:
    - The prepared DataFrame (possibly wrapped)
    - The prepared input (expression or converted series)
    - Unwrap function to restore original DataFrame type
    - Metadata about the operation

    Usage:
        ctx = OperationResolver.resolve(df, input)
        result = system.filter(ctx.dataframe, ctx.input)
        return ctx.unwrap(result)
    """

    dataframe: Any
    """The prepared DataFrame (may be wrapped in Narwhals)."""

    input: Any
    """The prepared input (expression or converted series)."""

    unwrap: Callable[[Any], Any]
    """Function to restore original DataFrame type after operation."""

    df_backend: Backend
    """Original DataFrame backend."""

    input_backend: Backend
    """Original input backend."""

    input_type: InputType
    """Input category (EXPRESSION or SERIES)."""

    def __repr__(self) -> str:
        return (
            f"OperationContext("
            f"df={self.df_backend.name}, "
            f"input={self.input_type.name}:{self.input_backend.name})"
        )


class OperationResolver:
    """
    Unified resolver for cross-backend operations.

    Handles all DataFrame + input combinations by:
    1. Detecting backends of both DataFrame and input
    2. Applying appropriate transformations (wrap, convert)
    3. Returning an OperationContext with prepared data and unwrap function

    Resolution strategies:
    - Native match (e.g., pl.Expr on Polars): No transformation
    - Narwhals expression on non-Narwhals: Wrap DataFrame in Narwhals
    - Cross-backend series: Convert series to match DataFrame backend
    - Ibis with series: Materialize Ibis to match series backend

    Usage:
        ctx = OperationResolver.resolve(df, expr_or_series)
        result = dataframe_system.filter(ctx.dataframe, ctx.input)
        return ctx.unwrap(result)
    """

    @classmethod
    def resolve(cls, df: Any, input: Any) -> OperationContext:
        """
        Resolve DataFrame and input for cross-backend compatibility.

        Args:
            df: Source DataFrame (any supported backend)
            input: Expression or Series to apply

        Returns:
            OperationContext with prepared dataframe, input, and unwrap function

        Raises:
            ValueError: If DataFrame or input type not recognized
        """
        df_detected = InputDetector.detect(df)
        input_detected = InputDetector.detect(input)

        logger.debug(
            f"Resolving: df={df_detected.backend.name}, "
            f"input={input_detected.input_type.name}:{input_detected.backend.name}"
        )

        # Dispatch based on input type
        if input_detected.input_type == InputType.EXPRESSION:
            return cls._resolve_expression(df_detected, input_detected)
        elif input_detected.input_type == InputType.SERIES:
            return cls._resolve_series(df_detected, input_detected)
        else:
            raise ValueError(
                f"Cannot resolve input type: {input_detected.input_type.name}"
            )

    # =========================================================================
    # Expression Resolution
    # =========================================================================

    @classmethod
    def _resolve_expression(
        cls, df_detected: DetectedInput, expr_detected: DetectedInput
    ) -> OperationContext:
        """
        Resolve DataFrame for use with an expression.

        Strategies:
        - Native combination (pl.Expr on Polars): Identity
        - nw.Expr on eager backends: Wrap in Narwhals, unwrap result
        - nw.Expr on Ibis: Materialize to PyArrow, wrap in Narwhals
        - ir.Expr on Ibis: Identity (native)
        """
        df_backend = df_detected.backend
        expr_backend = expr_detected.backend

        # Native combinations - no transformation needed
        if cls._is_native_expression_combo(df_backend, expr_backend):
            logger.debug("Native expression combination, no transformation")
            return OperationContext(
                dataframe=df_detected.obj,
                input=expr_detected.obj,
                unwrap=_identity,
                df_backend=df_backend,
                input_backend=expr_backend,
                input_type=InputType.EXPRESSION,
            )

        # Narwhals expression on non-Narwhals DataFrame
        if expr_backend == Backend.NARWHALS:
            return cls._resolve_narwhals_expression(df_detected, expr_detected)

        # Unknown combination - pass through with warning
        logger.warning(
            f"Unknown expression combination: "
            f"df={df_backend.name}, expr={expr_backend.name}"
        )
        return OperationContext(
            dataframe=df_detected.obj,
            input=expr_detected.obj,
            unwrap=_identity,
            df_backend=df_backend,
            input_backend=expr_backend,
            input_type=InputType.EXPRESSION,
        )

    @classmethod
    def _is_native_expression_combo(
        cls, df_backend: Backend, expr_backend: Backend
    ) -> bool:
        """Check if expression is native to the DataFrame backend."""
        native_combos = {
            (Backend.POLARS, Backend.POLARS),
            (Backend.IBIS, Backend.IBIS),
            (Backend.NARWHALS, Backend.NARWHALS),
        }
        return (df_backend, expr_backend) in native_combos

    @classmethod
    def _resolve_narwhals_expression(
        cls, df_detected: DetectedInput, expr_detected: DetectedInput
    ) -> OperationContext:
        """Resolve DataFrame for use with nw.Expr."""
        import narwhals as nw

        df_backend = df_detected.backend

        # Already Narwhals - no wrapping needed
        if df_backend == Backend.NARWHALS:
            return OperationContext(
                dataframe=df_detected.obj,
                input=expr_detected.obj,
                unwrap=_identity,
                df_backend=df_backend,
                input_backend=Backend.NARWHALS,
                input_type=InputType.EXPRESSION,
            )

        # Ibis needs materialization first
        if df_backend == Backend.IBIS:
            from ..dataframe_system import DataFrameSystemFactory

            system = DataFrameSystemFactory.get_system(df_detected.obj)
            materialized = system.to_pyarrow(df_detected.obj)
            wrapped = nw.from_native(materialized, eager_only=True)

            logger.debug("Materialized Ibis to PyArrow and wrapped in Narwhals")
            return OperationContext(
                dataframe=wrapped,
                input=expr_detected.obj,
                unwrap=nw.to_native,
                df_backend=df_backend,
                input_backend=Backend.NARWHALS,
                input_type=InputType.EXPRESSION,
            )

        # Wrap eager DataFrame in Narwhals
        wrapped = nw.from_native(df_detected.obj, eager_only=True)
        logger.debug(f"Wrapped {df_backend.name} DataFrame in Narwhals")

        return OperationContext(
            dataframe=wrapped,
            input=expr_detected.obj,
            unwrap=nw.to_native,
            df_backend=df_backend,
            input_backend=Backend.NARWHALS,
            input_type=InputType.EXPRESSION,
        )

    # =========================================================================
    # Series Resolution
    # =========================================================================

    @classmethod
    def _resolve_series(
        cls, df_detected: DetectedInput, series_detected: DetectedInput
    ) -> OperationContext:
        """
        Resolve series for use with a DataFrame.

        Strategies:
        - Same backend: Identity
        - Cross-backend: Convert series to match DataFrame
        - Narwhals series: Unwrap to native first
        - Series on Ibis: Materialize Ibis to match series backend
        - Series on Narwhals DataFrame: Convert to native backend, wrap in Narwhals
        """
        df_backend = df_detected.backend
        series_backend = series_detected.backend

        # Handle Narwhals series by unwrapping first
        if series_backend == Backend.NARWHALS:
            return cls._resolve_narwhals_series(df_detected, series_detected)

        # Ibis can't use physical series - need to materialize
        if df_backend == Backend.IBIS:
            return cls._resolve_series_on_ibis(df_detected, series_detected)

        # Narwhals DataFrames need special handling
        if df_backend == Backend.NARWHALS:
            return cls._resolve_series_on_narwhals(df_detected, series_detected)

        # Same backend - no conversion needed
        if df_backend == series_backend:
            logger.debug("Series backend matches DataFrame, no conversion")
            return OperationContext(
                dataframe=df_detected.obj,
                input=series_detected.obj,
                unwrap=_identity,
                df_backend=df_backend,
                input_backend=series_backend,
                input_type=InputType.SERIES,
            )

        # Cross-backend - convert series to match DataFrame
        from ..conversion.series import SeriesConverter

        target_backend = cls._df_backend_to_series_backend(df_backend)
        converted = SeriesConverter.convert(series_detected.obj, target_backend)
        logger.debug(f"Converted series from {series_backend.name} to {target_backend.name}")

        return OperationContext(
            dataframe=df_detected.obj,
            input=converted,
            unwrap=_identity,
            df_backend=df_backend,
            input_backend=df_backend,  # Now matches
            input_type=InputType.SERIES,
        )

    @classmethod
    def _resolve_narwhals_series(
        cls, df_detected: DetectedInput, series_detected: DetectedInput
    ) -> OperationContext:
        """Resolve nw.Series by unwrapping to native first."""
        import narwhals as nw

        native_series = nw.to_native(series_detected.obj)
        logger.debug(f"Unwrapped nw.Series to {type(native_series).__name__}")

        # Re-detect and resolve with native series
        native_detected = InputDetector.detect(native_series)
        return cls._resolve_series(df_detected, native_detected)

    @classmethod
    def _resolve_series_on_ibis(
        cls, df_detected: DetectedInput, series_detected: DetectedInput
    ) -> OperationContext:
        """Resolve series on Ibis by materializing to match series backend."""
        from ..dataframe_system import DataFrameSystemFactory

        series_backend = series_detected.backend
        system = DataFrameSystemFactory.get_system(df_detected.obj)

        # Choose materialization target based on series backend
        if series_backend == Backend.POLARS:
            materialized = system.to_polars(df_detected.obj)
            logger.debug("Materialized Ibis to Polars for pl.Series")
        elif series_backend == Backend.PANDAS:
            materialized = system.to_pandas(df_detected.obj)
            logger.debug("Materialized Ibis to pandas for pd.Series")
        else:
            materialized = system.to_pyarrow(df_detected.obj)
            logger.debug(f"Materialized Ibis to PyArrow for {series_backend.name}")

        return OperationContext(
            dataframe=materialized,
            input=series_detected.obj,
            unwrap=_identity,  # No unwrap needed - we changed the DataFrame type
            df_backend=series_backend,  # DataFrame is now in series backend
            input_backend=series_backend,
            input_type=InputType.SERIES,
        )

    @classmethod
    def _resolve_series_on_narwhals(
        cls, df_detected: DetectedInput, series_detected: DetectedInput
    ) -> OperationContext:
        """
        Resolve native series for use with Narwhals DataFrame.

        Narwhals DataFrames wrap native backends. The series must be
        converted to match the native backend, then potentially wrapped.
        """
        import narwhals as nw
        from ..conversion.series import SeriesConverter, SeriesBackend

        series_backend = series_detected.backend

        # Get the native DataFrame and detect its backend
        native_df = nw.to_native(df_detected.obj)
        native_detected = InputDetector.detect(native_df)
        native_backend = native_detected.backend
        logger.debug(f"Narwhals DataFrame backed by {native_backend.name}")

        # Convert series to match native backend
        target_series_backend = cls._df_backend_to_series_backend(native_backend)
        converted_series = SeriesConverter.convert(
            series_detected.obj, target_series_backend
        )
        logger.debug(f"Converted {series_backend.name} series to {target_series_backend.name}")

        # PyArrow-backed Narwhals can't filter with series through Narwhals
        # Unwrap to native and filter directly
        if native_backend == Backend.PYARROW:
            logger.debug("PyArrow-backed Narwhals: unwrapping to native for filter")
            return OperationContext(
                dataframe=native_df,
                input=converted_series,
                unwrap=_identity,  # Result stays as PyArrow
                df_backend=Backend.PYARROW,
                input_backend=Backend.PYARROW,
                input_type=InputType.SERIES,
            )

        # Wrap series in Narwhals for other backends
        wrapped_series = SeriesConverter.convert(converted_series, SeriesBackend.NARWHALS)
        logger.debug("Wrapped converted series in Narwhals")

        return OperationContext(
            dataframe=df_detected.obj,
            input=wrapped_series,
            unwrap=_identity,  # Result stays as Narwhals
            df_backend=Backend.NARWHALS,
            input_backend=Backend.NARWHALS,
            input_type=InputType.SERIES,
        )

    @classmethod
    def _df_backend_to_series_backend(cls, backend: Backend):
        """Map DataFrame backend to corresponding SeriesBackend enum."""
        from ..conversion.series import SeriesBackend

        mapping = {
            Backend.POLARS: SeriesBackend.POLARS,
            Backend.PANDAS: SeriesBackend.PANDAS,
            Backend.PYARROW: SeriesBackend.PYARROW,
            Backend.NARWHALS: SeriesBackend.NARWHALS,
        }
        return mapping.get(backend, SeriesBackend.PYARROW)


__all__ = [
    "OperationContext",
    "OperationResolver",
]
