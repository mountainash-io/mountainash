"""
Core utilities for mountainash-dataframes.

This module provides shared utilities used across the codebase:
- expression_compiler: Compile mountainash expressions to native backend expressions
"""

from __future__ import annotations

from .expression_compiler import compile_expression

__all__ = [
    "compile_expression",
]
