"""
Core operations utilities for mountainash-dataframes.

This module provides:
- InputDetector: Unified type/backend detection
- OperationResolver: Unified resolution for cross-backend operations
- Legacy resolvers (DataFrameResolver, SeriesResolver) for backward compatibility
"""

from __future__ import annotations

from .detection import (
    InputDetector,
    DetectedInput,
)

from .context import (
    OperationContext,
    OperationResolver,
)

from .resolver import (
    DataFrameResolver,
    SeriesResolver,
    ResolvedDataFrame,
    ResolvedSeries,
    is_expression,
    is_series,
)

__all__ = [
    # New unified detection
    "InputDetector",
    "DetectedInput",
    # New unified resolver
    "OperationContext",
    "OperationResolver",
    # Legacy resolvers (backward compatibility)
    "DataFrameResolver",
    "SeriesResolver",
    "ResolvedDataFrame",
    "ResolvedSeries",
    "is_expression",
    "is_series",
]
