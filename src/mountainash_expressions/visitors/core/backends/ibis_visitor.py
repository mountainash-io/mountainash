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

from ....constants import CONST_VISITOR_BACKEND
from .. import BaseBackendVisitor

class IbisBackendVisitor(BaseBackendVisitor):
    """Ternary-aware Ibis visitor with lambda-based operations following boolean pattern."""

    @property
    def _backend_type(self) -> str:
        return CONST_VISITOR_BACKEND.IBIS


    def _is_unknown_value(self, expr):
        """Type-safe UNKNOWN value detection for Ibis expressions.

        Args:
            expr: Ibis expression to check for UNKNOWN values

        Returns:
            Boolean Ibis expression indicating if value is UNKNOWN
        """
        # Always check for NULL first
        return expr.isnull()

        # # Try to determine type from expression
        # try:
        #     # Get the expression type if possible
        #     expr_type = getattr(expr, 'type', lambda: None)()

        #     if expr_type is not None:
        #         # If it's a string type, check for string unknown values
        #         if hasattr(expr_type, 'is_string') and expr_type.is_string():
        #             return null_check | (expr == "<NA>")
        #         # If it's a numeric type, check for numeric unknown values
        #         elif hasattr(expr_type, 'is_numeric') and expr_type.is_numeric():
        #             return null_check | (expr == -999999999)

        #     # If we can't determine type, fall back to NULL check only
        #     # This is the safest option to avoid type comparison errors
        #     return null_check

        # except Exception:
        #     # If anything goes wrong with type detection, just use NULL check
        #     return null_check

    # ===============
    # Comparison Data Prep - ibis concrete implementations
    # ===============

    def _format_column(self,  column: str, table: Any) -> Any:
        return table[column]

    def _format_literal(self, value: Any, table: Optional[Any]=None) -> Any:
        return ibis.literal(value)

    def _format_list(self, value: Any) -> Any:
        return list(value) if not isinstance(value, list) else value # Ensure it's a list
