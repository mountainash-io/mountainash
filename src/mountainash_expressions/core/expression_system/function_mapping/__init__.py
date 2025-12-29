"""Function registry for Substrait-aligned operations.

This module provides the central function registry that maps operation names
to Substrait metadata and backend methods.
"""

from .registry import (
    ExpressionFunctionRegistry as FunctionRegistry,
    ExpressionFunctionDef as FunctionDef,
    SubstraitExtension,
)
from .definitions import register_all_functions


__all__ = [
    "FunctionRegistry",
    "FunctionDef",
    "SubstraitExtension",
    "register_all_functions",
]
