"""
Series backend enumeration.
"""

from __future__ import annotations

from enum import Enum, auto


class SeriesBackend(Enum):
    """
    Enumeration of supported series/array backends.

    Uses Enum with auto() for identity-based comparison.
    """

    POLARS = auto()
    PANDAS = auto()
    PYARROW = auto()
    NARWHALS = auto()


__all__ = ["SeriesBackend"]
