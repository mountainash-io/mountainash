"""Polars backend implementation of ExpressionSystem."""

from typing import Any
import polars as pl

from ....core.expression_system import ExpressionSystem
from ....core.constants import CONST_VISITOR_BACKENDS


class PolarsBaseExpressionSystem(ExpressionSystem):
    """
    Polars-specific implementation of ExpressionSystem.

    This class encapsulates all Polars-specific operations,
    allowing visitors to build expressions without direct knowledge
    of the Polars API.
    """

    @property
    def backend_type(self) -> CONST_VISITOR_BACKENDS:
        """Return Polars backend type."""
        return CONST_VISITOR_BACKENDS.POLARS

    def is_native_expression(self, expr: Any) -> bool:
        """
        Check if an expression is a native Polars expression.

        Args:
            expr: Expression to check

        Returns:
            True if expr is a pl.Expr, False otherwise
        """
        return isinstance(expr, pl.Expr)
