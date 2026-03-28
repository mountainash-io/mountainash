"""
Constants for the DataFrameSystem.

Backend enum is imported from mountainash.core.constants.
This module adds the detection order specific to DataFrameSystem routing.
"""

from mountainash.core.constants import CONST_BACKEND_SYSTEM as CONST_DATAFRAME_BACKEND


# Backend detection order (important - more specific first)
BACKEND_DETECTION_ORDER = [
    CONST_DATAFRAME_BACKEND.IBIS,
    CONST_DATAFRAME_BACKEND.NARWHALS,
    CONST_DATAFRAME_BACKEND.POLARS,
]
