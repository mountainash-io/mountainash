"""
Backwards-compatibility shim for mountainash.dataframes.constants.

All canonical definitions now live in mountainash.core.constants.
This module re-exports them under their old names.
"""

from mountainash.core.constants import (
    CONST_BACKEND as CONST_DATAFRAME_FRAMEWORK,
    CONST_BACKEND as CONST_DATAFRAME_BACKEND,
    CONST_BACKEND_SYSTEM as CONST_EXPRESSION_TYPE,
    CONST_BACKEND_SYSTEM as CONST_JOIN_BACKEND_TYPE,
    CONST_DATAFRAME_TYPE,
    CONST_IBIS_INMEMORY_BACKEND,
)
from mountainash.pydata.constants import CONST_PYTHON_DATAFORMAT

__all__ = [
    "CONST_DATAFRAME_FRAMEWORK",
    "CONST_DATAFRAME_BACKEND",
    "CONST_EXPRESSION_TYPE",
    "CONST_JOIN_BACKEND_TYPE",
    "CONST_DATAFRAME_TYPE",
    "CONST_IBIS_INMEMORY_BACKEND",
    "CONST_PYTHON_DATAFORMAT",
]
