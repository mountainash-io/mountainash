"""
Series conversion utilities.

This submodule provides functionality to convert series/arrays between backends:
- Polars Series (pl.Series)
- pandas Series (pd.Series)
- PyArrow Array (pa.Array)
- Narwhals Series (nw.Series)
"""

from __future__ import annotations

from .converter import SeriesConverter
from .backends import SeriesBackend

__all__ = [
    "SeriesConverter",
    "SeriesBackend",
]
