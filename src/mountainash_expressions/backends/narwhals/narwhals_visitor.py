# file: src/mountainash_dataframes/utils/expressions/ternary/ternary_expression_ibis.py

"""
Ibis Ternary Expression Visitor

This module provides a clean, lambda-based approach to ternary logic expressions
that mirrors the boolean system design while handling three-valued logic (TRUE/FALSE/UNKNOWN).
"""
from __future__ import annotations

from typing import Any, Optional
import narwhals as nw

from ...core.constants import CONST_VISITOR_BACKENDS
from ...core.backend_visitors import BackendVisitor
# from ...core.expression_visitors.common_mixins import CastExpressionVisitor, LiteralExpressionVisitor, SourceExpressionVisitor #, NativeBackendExpressionVisitor

from ...core.expression_visitors.common_mixins import CastExpressionVisitor, LiteralExpressionVisitor, SourceExpressionVisitor #, NativeBackendExpressionVisitor


class NarwhalsBackendBaseVisitor(BackendVisitor, CastExpressionVisitor, LiteralExpressionVisitor, SourceExpressionVisitor):
    """Ternary-aware Narwhals visitor with lambda-based operations following boolean pattern."""

    @property
    def backend_type(self) -> CONST_VISITOR_BACKENDS:
        return CONST_VISITOR_BACKENDS.NARWHALS



    # ===============
    # Common
    # ===============

    # Baseline source values
    def _col(self,  column: Any, /,  **kwargs) -> nw.Expr:
        return nw.col(column, **kwargs)

    def _lit(self, value: Any) -> nw.Expr:
        return nw.lit(value)

    # Unary Comparisons
    def _is_null(self, column: nw.Expr, /,  **kwargs) -> nw.Expr:
        return column.is_null()

    def _is_not_null(self, column: nw.Expr, /,  **kwargs) -> nw.Expr:
        return ~column.is_null()


    # Collection Formatting - Python
    def _as_list(self, value: Any) -> Any:
        return list(value) if not isinstance(value, list) else value # Ensure it's a list

    def _as_set(self, value: Any) -> Any:
        return set(value) if not isinstance(value, set) else value # Ensure it's a set



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
