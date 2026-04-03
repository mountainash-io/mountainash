"""Core module for mountainash-expressions.

This module contains the core logic, visitor patterns, and infrastructure
for expression nodes and their evaluation across different backends.
"""
from __future__ import annotations

from .constants import (
    CONST_VISITOR_BACKENDS,
    CONST_LOGIC_TYPES,
    CONST_EXPRESSION_NODE_TYPES,
    CONST_EXPRESSION_LOGICAL_OPERATORS,
    CONST_TERNARY_LOGIC_VALUES,
)

__all__ = [
    "CONST_VISITOR_BACKENDS",
    "CONST_LOGIC_TYPES",
    "CONST_EXPRESSION_NODE_TYPES",
    "CONST_EXPRESSION_LOGICAL_OPERATORS",
    "CONST_TERNARY_LOGIC_VALUES",
]
