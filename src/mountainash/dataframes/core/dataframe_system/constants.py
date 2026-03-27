"""
Constants for the DataFrameSystem.

Defines the three supported backends:
- POLARS: Native Polars (DataFrame and LazyFrame)
- NARWHALS: Universal adapter (pandas, PyArrow, cuDF)
- IBIS: SQL backends (DuckDB, PostgreSQL, BigQuery, etc.)
"""

from enum import Enum, auto


class CONST_DATAFRAME_BACKEND(Enum):
    """
    Supported DataFrame backends.

    Consolidated from 7 backends to 3:
    - POLARS: Native Polars support (includes LazyFrame)
    - NARWHALS: Universal adapter for pandas, PyArrow, cuDF
    - IBIS: SQL backend support via Ibis
    """

    POLARS = auto()
    NARWHALS = auto()
    IBIS = auto()


# Backend detection order (important - more specific first)
BACKEND_DETECTION_ORDER = [
    # Ibis first - most specific module patterns
    CONST_DATAFRAME_BACKEND.IBIS,
    # Narwhals second - wraps other backends
    CONST_DATAFRAME_BACKEND.NARWHALS,
    # Polars last - primary backend
    CONST_DATAFRAME_BACKEND.POLARS,
]
