"""
Input resolution for cross-backend operations.

This module provides separate resolvers for expressions and series:
- ExpressionResolver: Handles expression + DataFrame resolution (wrapping, materialization)
- SeriesResolver: Handles series + DataFrame resolution (conversion)

Usage:
    from mountainash.dataframes.core.operations import ExpressionResolver, SeriesResolver

    # For expressions (pl.Expr, nw.Expr, ir.Expr)
    resolved = ExpressionResolver.resolve(df, expr)
    result = resolved.dataframe.filter(resolved.input)
    final = resolved.unwrap(result)

    # For series (pl.Series, pd.Series, pa.Array)
    resolved = SeriesResolver.resolve(df, series)
    result = apply_filter(resolved.dataframe, resolved.input)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable

from ..conversion.series import SeriesConverter, SeriesBackend
from ..dataframe_system import DataFrameSystemFactory
from ..typing import (
    # Expression detection
    is_polars_expression,
    is_narwhals_expression,
    is_ibis_expression,
    detect_expression_backend,
    # Series detection
    is_narwhals_series,
    is_native_series,
    detect_series_backend,
    # DataFrame detection
    detect_dataframe_backend_type,
)

logger = logging.getLogger(__name__)


# Identity function for when no unwrapping/conversion is needed
_identity: Callable[[Any], Any] = lambda x: x


@dataclass
class ResolvedDataFrame:
    """
    Result of resolving a DataFrame for use with an expression.

    When using nw.Expr on a pandas/PyArrow DataFrame, we need to:
    1. Wrap the df in Narwhals before applying the expression
    2. Unwrap the result back to native format

    Attributes:
        wrap: Function to wrap the DataFrame (e.g., into Narwhals)
        unwrap: Function to unwrap the result back to native
    """
    wrap: Callable[[Any], Any]
    unwrap: Callable[[Any], Any]


@dataclass
class ResolvedSeries:
    """
    Result of series resolution.

    Attributes:
        series: The (possibly converted) series
        prepare_df: Function to prepare the DataFrame (e.g., materialize Ibis)
    """
    series: Any
    prepare_df: Callable[[Any], Any]


class DataFrameResolver:
    """
    Resolves how to prepare a DataFrame for use with a given expression.

    Returns a ResolvedDataFrame with wrap/unwrap functions:
    - pl.Expr on Polars → no wrapping needed
    - ir.Expr on Ibis → no wrapping needed
    - nw.Expr on Polars/pandas/PyArrow → wrap df in Narwhals, unwrap result
    - nw.Expr on Ibis → materialize to PyArrow, wrap in Narwhals
    """

    @classmethod
    def resolve(cls, df: Any, expr: Any) -> ResolvedDataFrame:
        """
        Resolve how to prepare a DataFrame for an expression.

        Args:
            df: Source DataFrame (any backend)
            expr: Expression to apply (pl.Expr, nw.Expr, ir.Expr)

        Returns:
            ResolvedDataFrame with wrap and unwrap functions
        """
        df_backend = detect_dataframe_backend_type(df)
        expr_backend = detect_expression_backend(expr)

        logger.debug(f"Resolving DataFrame: df={df_backend}, expr={expr_backend}")

        # Native combinations - no wrapping needed
        if cls._is_native_combination(df_backend, expr_backend):
            logger.debug("Native expression/df combination, no wrapping needed")
            return ResolvedDataFrame(wrap=_identity, unwrap=_identity)

        # Narwhals expression on non-Narwhals DataFrame
        if expr_backend == "narwhals":
            return cls._resolve_for_narwhals(df_backend)

        # Unknown combination - pass through
        logger.warning(f"Unknown expression/df combination: expr={expr_backend}, df={df_backend}")
        return ResolvedDataFrame(wrap=_identity, unwrap=_identity)

    @classmethod
    def _is_native_combination(cls, df_backend: str, expr_backend: str) -> bool:
        """Check if expression is native to the DataFrame backend."""
        native_combos = {
            ("polars", "polars"),
            ("ibis", "ibis"),
            ("narwhals", "narwhals"),
        }
        return (df_backend, expr_backend) in native_combos

    @classmethod
    def _resolve_for_narwhals(cls, df_backend: str) -> ResolvedDataFrame:
        """Resolve DataFrame for use with nw.Expr."""
        import narwhals as nw

        # Already Narwhals - no wrapping needed
        if df_backend == "narwhals":
            return ResolvedDataFrame(wrap=_identity, unwrap=_identity)

        # Ibis needs materialization first, then Narwhals wrapping
        if df_backend == "ibis":
            def wrap_ibis(df: Any) -> Any:
                system = DataFrameSystemFactory.get_system(df)
                materialized = system.to_pyarrow(df)
                return nw.from_native(materialized, eager_only=True)

            logger.debug("Will materialize Ibis to PyArrow and wrap in Narwhals")
            return ResolvedDataFrame(wrap=wrap_ibis, unwrap=nw.to_native)

        # Wrap eager DataFrame in Narwhals
        def wrap_eager(df: Any) -> Any:
            return nw.from_native(df, eager_only=True)

        logger.debug(f"Will wrap {df_backend} DataFrame in Narwhals for nw.Expr")
        return ResolvedDataFrame(wrap=wrap_eager, unwrap=nw.to_native)


class SeriesResolver:
    """
    Resolves series + DataFrame combinations.

    Handles:
    - Same-backend series → no conversion
    - Cross-backend series → convert series to match DataFrame
    - nw.Series → unwrap to native, then resolve
    - Series on Ibis → materialize Ibis to match series backend
    """

    @classmethod
    def resolve(cls, df: Any, series: Any) -> ResolvedSeries:
        """
        Resolve a series for use with a DataFrame.

        Args:
            df: Source DataFrame (any backend)
            series: Series to apply (pl.Series, pd.Series, pa.Array, nw.Series)

        Returns:
            ResolvedSeries with (possibly converted) series and prepare_df function
        """
        df_backend = detect_dataframe_backend_type(df)

        # Handle nw.Series by unwrapping first
        if is_narwhals_series(series):
            return cls._resolve_narwhals_series(df, series)

        series_backend = detect_series_backend(series)
        logger.debug(f"Resolving series: df={df_backend}, series={series_backend}")

        # Ibis can't use physical series - materialize first
        if df_backend == "ibis":
            return cls._resolve_series_on_ibis(series, series_backend)

        # Narwhals DataFrames need series converted to native backend then wrapped
        if df_backend == "narwhals":
            return cls._resolve_series_on_narwhals(df, series, series_backend)

        # Check if backends match
        if cls._backends_match(df_backend, series_backend):
            logger.debug("Series backend matches DataFrame, no conversion needed")
            return ResolvedSeries(
                series=series,
                prepare_df=_identity,
            )

        # Convert series to match DataFrame backend
        target_backend = cls._df_backend_to_series_backend(df_backend)
        converted_series = SeriesConverter.convert(series, target_backend)
        logger.debug(f"Converted series from {series_backend} to {target_backend}")

        return ResolvedSeries(
            series=converted_series,
            prepare_df=_identity,
        )

    @classmethod
    def _resolve_narwhals_series(cls, df: Any, series: Any) -> ResolvedSeries:
        """Resolve nw.Series by unwrapping to native and re-resolving."""
        import narwhals as nw

        native_series = nw.to_native(series)
        logger.debug(f"Unwrapped nw.Series to {type(native_series).__name__}")

        # Recursively resolve with the native series
        return cls.resolve(df, native_series)

    @classmethod
    def _resolve_series_on_ibis(cls, series: Any, series_backend: str) -> ResolvedSeries:
        """Resolve series on Ibis by returning a function to materialize Ibis."""

        def prepare_ibis_for_polars(df: Any) -> Any:
            system = DataFrameSystemFactory.get_system(df)
            return system.to_polars(df)

        def prepare_ibis_for_pandas(df: Any) -> Any:
            system = DataFrameSystemFactory.get_system(df)
            return system.to_pandas(df)

        def prepare_ibis_for_pyarrow(df: Any) -> Any:
            system = DataFrameSystemFactory.get_system(df)
            return system.to_pyarrow(df)

        # Choose materialization based on series backend
        if series_backend == "polars":
            logger.debug("Will materialize Ibis to Polars for pl.Series")
            return ResolvedSeries(series=series, prepare_df=prepare_ibis_for_polars)
        elif series_backend == "pandas":
            logger.debug("Will materialize Ibis to pandas for pd.Series")
            return ResolvedSeries(series=series, prepare_df=prepare_ibis_for_pandas)
        else:
            logger.debug(f"Will materialize Ibis to PyArrow for {series_backend}")
            return ResolvedSeries(series=series, prepare_df=prepare_ibis_for_pyarrow)

    @classmethod
    def _resolve_series_on_narwhals(cls, df: Any, series: Any, series_backend: str) -> ResolvedSeries:
        """
        Resolve native series for use with Narwhals DataFrame.

        Narwhals DataFrames wrap native backends (polars, pandas, pyarrow).
        The series must be converted to match the native backend.

        Special case: PyArrow-backed Narwhals DataFrames can't filter with
        any series type through Narwhals, so we unwrap to native and filter directly.
        """
        import narwhals as nw

        # Get the native DataFrame and detect its backend
        native_df = nw.to_native(df)
        native_backend = detect_dataframe_backend_type(native_df)
        logger.debug(f"Narwhals DataFrame backed by {native_backend}")

        # Convert series to match the native backend
        target_backend = cls._df_backend_to_series_backend(native_backend)
        converted_series = SeriesConverter.convert(series, target_backend)
        logger.debug(f"Converted {series_backend} series to {target_backend.value}")

        # PyArrow-backed Narwhals DataFrames can't filter with series through Narwhals
        # Unwrap to native and filter directly
        if native_backend == "pyarrow":
            logger.debug("PyArrow-backed Narwhals: unwrapping to native for filter")
            return ResolvedSeries(
                series=converted_series,
                prepare_df=nw.to_native,
            )

        # Wrap series in Narwhals for other backends
        wrapped_series = SeriesConverter.convert(converted_series, SeriesBackend.NARWHALS)
        logger.debug("Wrapped converted series in Narwhals for nw.DataFrame")

        return ResolvedSeries(
            series=wrapped_series,
            prepare_df=_identity,
        )

    @classmethod
    def _backends_match(cls, df_backend: str, series_backend: str) -> bool:
        """Check if series backend matches DataFrame backend."""
        return df_backend == series_backend

    @classmethod
    def _df_backend_to_series_backend(cls, df_backend: str) -> SeriesBackend:
        """Map DataFrame backend to corresponding SeriesBackend."""
        mapping = {
            "polars": SeriesBackend.POLARS,
            "pandas": SeriesBackend.PANDAS,
            "pyarrow": SeriesBackend.PYARROW,
            "narwhals": SeriesBackend.NARWHALS,
        }
        return mapping.get(df_backend, SeriesBackend.PYARROW)


# =============================================================================
# Convenience: Combined resolver for filter-like operations
# =============================================================================


def is_expression(obj: Any) -> bool:
    """Check if object is an expression (pl.Expr, nw.Expr, ir.Expr)."""
    return is_polars_expression(obj) or is_narwhals_expression(obj) or is_ibis_expression(obj)


def is_series(obj: Any) -> bool:
    """Check if object is a series (pl.Series, pd.Series, pa.Array, nw.Series)."""
    return is_native_series(obj)


__all__ = [
    "DataFrameResolver",
    "SeriesResolver",
    "ResolvedDataFrame",
    "ResolvedSeries",
    "is_expression",
    "is_series",
]
