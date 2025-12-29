"""Polars backend base class.

Provides the base ExpressionSystem class for the Polars backend.
"""

from __future__ import annotations

from typing import Any

import polars as pl

from mountainash_expressions.core.constants import CONST_VISITOR_BACKENDS
from mountainash_expressions.backends.expression_systems.base import BaseExpressionSystem


class PolarsBaseExpressionSystem(BaseExpressionSystem):
    """Base class for Polars expression system components.

    Provides common functionality and backend identification for all
    Polars protocol implementations.
    """

    @property
    def backend_type(self) -> CONST_VISITOR_BACKENDS:
        """Return the Polars backend type identifier."""
        return CONST_VISITOR_BACKENDS.POLARS

    def is_native_expression(self, expr: Any) -> bool:
        """Check if the expression is a native Polars expression.

        Args:
            expr: Any expression object to check.

        Returns:
            True if expr is a pl.Expr instance.
        """
        return isinstance(expr, pl.Expr)

    def _extract_literal_value(self, expr: Any) -> Any:
        """Extract the literal value from a Polars literal expression.

        Some operations (like string slice/substring) work better with raw
        Python values than Expr objects. This helper extracts the underlying
        value from pl.lit() expressions.

        Args:
            expr: A Polars expression or literal value.

        Returns:
            The underlying Python value if it's a literal expression,
            otherwise returns the expr unchanged.
        """
        # If it's already a raw Python value, return as-is
        if isinstance(expr, (str, int, float, bool, type(None))):
            return expr

        # If it's a Polars Expr, try to extract the literal value
        if isinstance(expr, pl.Expr):
            try:
                # Create a tiny DataFrame to evaluate the literal
                result = pl.select(expr).item()
                return result
            except Exception:
                pass

        # If extraction fails, return the original expr
        return expr
