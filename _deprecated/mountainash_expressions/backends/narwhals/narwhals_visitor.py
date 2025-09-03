# file: src/mountainash_dataframes/utils/expressions/ternary/ternary_expression_ibis.py

"""
Ibis Ternary Expression Visitor

This module provides a clean, lambda-based approach to ternary logic expressions
that mirrors the boolean system design while handling three-valued logic (TRUE/FALSE/UNKNOWN).
"""

from typing import Any, Optional
import narwhals as nw

from ...core.constants import CONST_VISITOR_BACKENDS
from ...core.visitor import BackendVisitorMixin

class NarwhalsBackendVisitorMixin(BackendVisitorMixin):
    """Ternary-aware Narwhals visitor with lambda-based operations following boolean pattern."""

    @property
    def backend_type(self) -> CONST_VISITOR_BACKENDS:
        return CONST_VISITOR_BACKENDS.IBIS

    def _is_unknown_value(self, expr: nw.Expr) -> nw.Expr:
        """Type-safe UNKNOWN value detection for Narwhals expressions.

        Args:
            expr: Narwhals expression to check for UNKNOWN values

        Returns:
            Boolean Narwhals expression indicating if value is UNKNOWN
        """
        # Use Narwhals' when/then construct for type-safe comparisons
        # return nw.when(expr.is_null()).then(True).when(
        #     # Try string unknown check with error handling
        #     expr.cast(nw.Utf8, strict=False) == "<NA>"
        # ).then(True).when(
        #     # Try numeric unknown check with error handling
        #     expr.cast(nw.Int64, strict=False) == -999999999
        # ).then(True).otherwise(False)

        return expr.is_null()

    # ===============
    # Comparison Data Prep - ibis concrete implementations
    # ===============


    def _format_column(self,  column: str, table: Any) -> Any:
        return nw.col(column)

    def _format_literal(self, value: Any, table: Optional[Any]=None) -> Any:
        return nw.lit(value)

    def _format_list(self, value: Any) -> Any:
        return list(value) if not isinstance(value, list) else value # Ensure it's a list
