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
