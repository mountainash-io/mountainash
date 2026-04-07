"""Polars backend base class.

Provides the base ExpressionSystem class for the Polars backend.
"""

from __future__ import annotations

from typing import Any

import polars as pl

from mountainash.core.types import KnownLimitation
from mountainash.expressions.core.constants import CONST_VISITOR_BACKENDS
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)
from mountainash.expressions.backends.expression_systems.base import BaseExpressionSystem


class PolarsBaseExpressionSystem(BaseExpressionSystem):
    """Base class for Polars expression system components.

    Provides common functionality and backend identification for all
    Polars protocol implementations.
    """

    BACKEND_NAME: str = "polars"

    KNOWN_EXPR_LIMITATIONS: dict[tuple[Any, str], KnownLimitation] = {
        (FK_STR.REPLACE, "substring"): KnownLimitation(
            message="Polars does not support dynamic column patterns in str.replace",
            native_errors=(pl.exceptions.ComputeError,),
            workaround="Use a literal string substring; replacement can be a column reference",
        ),
    }

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

    def _extract_literal_if_possible(self, expr: Any) -> Any:
        """Extract literal value from a Polars expression."""
        if isinstance(expr, (str, int, float, bool, type(None))):
            return expr
        if isinstance(expr, pl.Expr):
            try:
                result = pl.select(expr).item()
                return result
            except Exception:
                pass
        return expr
