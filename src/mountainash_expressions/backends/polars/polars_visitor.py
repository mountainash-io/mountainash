# file: src/mountainash_dataframes/utils/expressions/ternary/ternary_expression_ibis.py

"""
Ibis Ternary Expression Visitor

This module provides a clean, lambda-based approach to ternary logic expressions
that mirrors the boolean system design while handling three-valued logic (TRUE/FALSE/UNKNOWN).
"""

from typing import Callable, Any, Optional, List, Literal
import ibis
import ibis.expr.types as ir
from functools import reduce
import polars as pl

from ...core.constants import CONST_VISITOR_BACKENDS
from ...core.visitor import BackendVisitorMixin

class PolarsBackendVisitorMixin(BackendVisitorMixin):
    """Ternary-aware Ibis visitor with lambda-based operations following boolean pattern."""

    @property
    def backend_type(self) -> CONST_VISITOR_BACKENDS:
        return CONST_VISITOR_BACKENDS.IBIS

    def _is_unknown_value(self, expr: pl.Expr) -> pl.Expr:
        """Type-safe UNKNOWN value detection for Polars expressions.

        Args:
            expr: Polars expression to check for UNKNOWN values

        Returns:
            Boolean Polars expression indicating if value is UNKNOWN
        """
        # Use Polars' when/then construct for type-safe comparisons
        # return pl.when(expr.is_null()).then(True).when(
        #     # Try string unknown check with error handling
        #     expr.cast(pl.Utf8, strict=False) == "<NA>"
        # ).then(True).when(
        #     # Try numeric unknown check with error handling
        #     expr.cast(pl.Int64, strict=False) == -999999999
        # ).then(True).otherwise(False)

        return expr.is_null()

    # ===============
    # Comparison Data Prep - ibis concrete implementations
    # ===============


    def _format_column(self,  column: str, table: Any) -> Any:
        return pl.col(column)

    def _format_literal(self, value: Any, table: Optional[Any]=None) -> Any:
        return pl.lit(value)

    def _format_list(self, value: Any) -> Any:
        return list(value) if not isinstance(value, list) else value # Ensure it's a list
