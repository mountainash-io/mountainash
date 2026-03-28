"""
Series type aliases and detection utilities.

Type aliases are imported from mountainash.core.types.
This module adds series-specific type guards and detection.
"""

from __future__ import annotations

from typing import Any
from typing_extensions import TypeGuard

# Re-export type aliases from core
from mountainash.core.types import (
    PolarsSeries,
    PandasSeries,
    NarwhalsSeries,
    PyArrowArray,
    SupportedSeries,
)


# ============================================================================
# Type Guards - Series Detection
# ============================================================================


def is_polars_series(obj: Any) -> TypeGuard[PolarsSeries]:
    """
    Check if object is a Polars Series.

    Args:
        obj: Object to check

    Returns:
        True if object is a pl.Series
    """
    obj_type = type(obj)
    module = obj_type.__module__
    return module.startswith("polars") and obj_type.__name__ == "Series"


def is_pandas_series(obj: Any) -> TypeGuard[PandasSeries]:
    """
    Check if object is a pandas Series.

    Args:
        obj: Object to check

    Returns:
        True if object is a pd.Series
    """
    obj_type = type(obj)
    return obj_type.__module__.startswith("pandas") and obj_type.__name__ == "Series"


def is_narwhals_series(obj: Any) -> TypeGuard[NarwhalsSeries]:
    """
    Check if object is a Narwhals Series.

    Args:
        obj: Object to check

    Returns:
        True if object is a nw.Series
    """
    obj_type = type(obj)
    module = obj_type.__module__
    return module.startswith("narwhals") and obj_type.__name__ == "Series"


def is_pyarrow_array(obj: Any) -> bool:
    """
    Check if object is a PyArrow array (Array or ChunkedArray).

    Args:
        obj: Object to check

    Returns:
        True if object is a pa.Array or pa.ChunkedArray
    """
    obj_type = type(obj)
    module = obj_type.__module__
    class_name = obj_type.__name__
    return module.startswith("pyarrow") and ("Array" in class_name or "ChunkedArray" in class_name)


def is_native_series(obj: Any) -> bool:
    """
    Check if object is any native series/array type.

    This includes:
    - Polars Series (pl.Series)
    - pandas Series (pd.Series)
    - Narwhals Series (nw.Series)
    - PyArrow Array (pa.Array, pa.ChunkedArray)

    Args:
        obj: Object to check

    Returns:
        True if object is a native series/array type
    """
    return (
        is_polars_series(obj)
        or is_pandas_series(obj)
        or is_narwhals_series(obj)
        or is_pyarrow_array(obj)
    )


def is_supported_series(obj: Any) -> TypeGuard[SupportedSeries]:
    """
    Check if object is any supported series type.

    Args:
        obj: Object to check

    Returns:
        True if object is a supported series type
    """
    return is_native_series(obj)


# ============================================================================
# Series Backend Detection
# ============================================================================


def detect_series_backend(obj: Any) -> str | None:
    """
    Detect the backend type of a series object.

    Args:
        obj: Series object to check

    Returns:
        Backend name ('polars', 'pandas', 'narwhals', 'pyarrow') or None if not recognized
    """
    if is_polars_series(obj):
        return "polars"
    elif is_pandas_series(obj):
        return "pandas"
    elif is_narwhals_series(obj):
        return "narwhals"
    elif is_pyarrow_array(obj):
        return "pyarrow"
    return None


# ============================================================================
# Export List
# ============================================================================

__all__ = [
    # Type aliases
    "PolarsSeries",
    "PandasSeries",
    "NarwhalsSeries",
    "PyArrowArray",
    "SupportedSeries",
    # Type guards
    "is_polars_series",
    "is_pandas_series",
    "is_narwhals_series",
    "is_pyarrow_array",
    "is_native_series",
    "is_supported_series",
    # Detection utilities
    "detect_series_backend",
]
