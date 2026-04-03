"""Function registry for Substrait-aligned operations.

This module provides the central function registry that maps operation names
to Substrait metadata and backend methods.
"""
from __future__ import annotations

from .registry import (
    ExpressionFunctionRegistry as FunctionRegistry,
    ExpressionFunctionDef as FunctionDef,
)
from .definitions import register_all_functions
from ..function_keys.enums import SubstraitExtension


__all__ = [
    "FunctionRegistry",
    "FunctionDef",
    "SubstraitExtension",
    "register_all_functions",
]
