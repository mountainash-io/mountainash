"""
Expression compiler utilities.

This submodule provides functionality to compile mountainash expressions
to native backend expressions (Polars, Narwhals, Ibis).

The compiler handles backend detection and wrapping logic:
- Polars/Ibis/Narwhals DataFrames: compile directly
- pandas/PyArrow DataFrames: wrap in Narwhals first, compile to nw.Expr
"""

from __future__ import annotations

from .compiler import compile_expression

__all__ = [
    "compile_expression",
]
