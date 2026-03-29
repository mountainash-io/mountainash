"""
Series converter - converts series/arrays between backends.

Supports conversions between:
- Polars Series (pl.Series)
- pandas Series (pd.Series)
- PyArrow Array (pa.Array, pa.ChunkedArray)
- Narwhals Series (nw.Series) - unwraps to native first

Usage:
    from mountainash.dataframes.core.conversion.series import SeriesConverter, SeriesBackend

    # Convert pl.Series to pd.Series
    pd_series = SeriesConverter.convert(pl_series, target=SeriesBackend.PANDAS)

    # Auto-detect source backend
    pa_array = SeriesConverter.convert(any_series, target=SeriesBackend.PYARROW)
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, Tuple

from .backends import SeriesBackend
from ...constants import Backend

logger = logging.getLogger(__name__)


# Mapping from core Backend enum to SeriesBackend enum
_BACKEND_TO_SERIES_BACKEND: Dict[Backend, SeriesBackend] = {
    Backend.POLARS: SeriesBackend.POLARS,
    Backend.PANDAS: SeriesBackend.PANDAS,
    Backend.PYARROW: SeriesBackend.PYARROW,
    Backend.NARWHALS: SeriesBackend.NARWHALS,
}


# Type alias for conversion functions
ConversionFunc = Callable[[Any], Any]


class SeriesConverter:
    """
    Converts series/arrays between different DataFrame backends.

    The converter uses a dispatch table to look up the appropriate conversion
    function based on (source_backend, target_backend) pairs.

    For Narwhals series, the converter first unwraps to the native backend,
    then converts from there.
    """

    # Dispatch table: (source, target) -> conversion function
    _conversions: Dict[Tuple[SeriesBackend, SeriesBackend], ConversionFunc] = {}
    _initialized: bool = False

    @classmethod
    def _initialize(cls) -> None:
        """Initialize the conversion dispatch table."""
        if cls._initialized:
            return

        # Identity conversions (no-op)
        for backend in SeriesBackend:
            if backend != SeriesBackend.NARWHALS:  # Narwhals always unwraps
                cls._conversions[(backend, backend)] = lambda x: x

        # Polars → others
        cls._conversions[(SeriesBackend.POLARS, SeriesBackend.PANDAS)] = cls._polars_to_pandas
        cls._conversions[(SeriesBackend.POLARS, SeriesBackend.PYARROW)] = cls._polars_to_pyarrow
        cls._conversions[(SeriesBackend.POLARS, SeriesBackend.NARWHALS)] = cls._polars_to_narwhals

        # pandas → others
        cls._conversions[(SeriesBackend.PANDAS, SeriesBackend.POLARS)] = cls._pandas_to_polars
        cls._conversions[(SeriesBackend.PANDAS, SeriesBackend.PYARROW)] = cls._pandas_to_pyarrow
        cls._conversions[(SeriesBackend.PANDAS, SeriesBackend.NARWHALS)] = cls._pandas_to_narwhals

        # PyArrow → others
        cls._conversions[(SeriesBackend.PYARROW, SeriesBackend.POLARS)] = cls._pyarrow_to_polars
        cls._conversions[(SeriesBackend.PYARROW, SeriesBackend.PANDAS)] = cls._pyarrow_to_pandas
        cls._conversions[(SeriesBackend.PYARROW, SeriesBackend.NARWHALS)] = cls._pyarrow_to_narwhals

        cls._initialized = True

    @classmethod
    def detect_backend(cls, series: Any) -> SeriesBackend:
        """
        Detect the backend of a series object.

        Args:
            series: Series/array object

        Returns:
            SeriesBackend enum value

        Raises:
            ValueError: If series type is not recognized
        """
        from ...operations.detection import InputDetector

        detected = InputDetector.detect(series)
        return _BACKEND_TO_SERIES_BACKEND[detected.backend]

    @classmethod
    def convert(cls, series: Any, target: SeriesBackend) -> Any:
        """
        Convert a series to the target backend.

        Args:
            series: Source series/array (pl.Series, pd.Series, pa.Array, nw.Series)
            target: Target backend to convert to

        Returns:
            Converted series in the target backend format

        Raises:
            ValueError: If source series type is not recognized
            NotImplementedError: If conversion path doesn't exist
        """
        cls._initialize()

        source = cls.detect_backend(series)

        # Special handling for Narwhals: unwrap first, then convert
        if source == SeriesBackend.NARWHALS:
            return cls._convert_from_narwhals(series, target)

        # Look up conversion function
        key = (source, target)
        if key not in cls._conversions:
            raise NotImplementedError(
                f"No conversion path from {source.name} to {target.name}"
            )

        converter = cls._conversions[key]
        logger.debug(f"Converting series from {source.name} to {target.name}")
        return converter(series)

    @classmethod
    def convert_to_match_dataframe(cls, series: Any, dataframe: Any) -> Any:
        """
        Convert a series to match the backend of a DataFrame.

        This is a convenience method that detects the DataFrame's backend
        and converts the series to the appropriate type.

        Args:
            series: Source series/array to convert
            dataframe: Target DataFrame whose backend to match

        Returns:
            Converted series matching the DataFrame's backend

        Raises:
            ValueError: If DataFrame or series type is not recognized
        """
        from ...operations.detection import InputDetector

        detected = InputDetector.detect(dataframe)
        df_backend = detected.backend

        # Map DataFrame backend to SeriesBackend
        # Ibis materializes to PyArrow for series operations
        if df_backend == Backend.IBIS:
            target = SeriesBackend.PYARROW
        else:
            target = _BACKEND_TO_SERIES_BACKEND.get(df_backend)

        if target is None:
            raise ValueError(f"Unknown DataFrame backend: {df_backend.name}")

        return cls.convert(series, target)

    @classmethod
    def _convert_from_narwhals(cls, series: Any, target: SeriesBackend) -> Any:
        """
        Convert a Narwhals series by unwrapping to native first.

        Narwhals series wrap an underlying native series (Polars or pandas).
        We unwrap to get the native series, then convert from there.
        """
        import narwhals as nw

        # Unwrap to native
        native_series = nw.to_native(series)
        logger.debug(f"Unwrapped nw.Series to {type(native_series).__name__}")

        # If target is Narwhals, just wrap
        if target == SeriesBackend.NARWHALS:
            return series  # Already Narwhals

        # Detect the native backend and convert from there
        native_backend = cls.detect_backend(native_series)

        # If native matches target, we're done
        if native_backend == target:
            return native_series

        # Otherwise, convert from native to target
        return cls.convert(native_series, target)

    # =========================================================================
    # Polars conversions
    # =========================================================================

    @staticmethod
    def _polars_to_pandas(series: Any) -> Any:
        """Convert pl.Series to pd.Series."""
        return series.to_pandas()

    @staticmethod
    def _polars_to_pyarrow(series: Any) -> Any:
        """Convert pl.Series to pa.Array."""
        return series.to_arrow()

    @staticmethod
    def _polars_to_narwhals(series: Any) -> Any:
        """Convert pl.Series to nw.Series."""
        import narwhals as nw
        return nw.from_native(series, series_only=True)

    # =========================================================================
    # pandas conversions
    # =========================================================================

    @staticmethod
    def _pandas_to_polars(series: Any) -> Any:
        """Convert pd.Series to pl.Series."""
        import polars as pl
        return pl.Series(series)

    @staticmethod
    def _pandas_to_pyarrow(series: Any) -> Any:
        """Convert pd.Series to pa.Array."""
        import pyarrow as pa
        return pa.Array.from_pandas(series)

    @staticmethod
    def _pandas_to_narwhals(series: Any) -> Any:
        """Convert pd.Series to nw.Series."""
        import narwhals as nw
        return nw.from_native(series, series_only=True)

    # =========================================================================
    # PyArrow conversions
    # =========================================================================

    @staticmethod
    def _pyarrow_to_polars(series: Any) -> Any:
        """Convert pa.Array to pl.Series."""
        import polars as pl
        return pl.from_arrow(series)

    @staticmethod
    def _pyarrow_to_pandas(series: Any) -> Any:
        """Convert pa.Array to pd.Series."""
        return series.to_pandas()

    @staticmethod
    def _pyarrow_to_narwhals(series: Any) -> Any:
        """Convert pa.Array to nw.Series."""
        # PyArrow arrays need to go through Polars or pandas first
        # since Narwhals doesn't directly wrap pa.Array
        import polars as pl
        import narwhals as nw
        pl_series = pl.from_arrow(series)
        return nw.from_native(pl_series, series_only=True)


__all__ = ["SeriesConverter"]
