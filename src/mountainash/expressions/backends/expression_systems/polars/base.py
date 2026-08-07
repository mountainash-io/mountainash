"""Polars backend base class.

Provides the base ExpressionSystem class for the Polars backend.
"""

from __future__ import annotations

from typing import Any

import polars as pl

from mountainash.core.capabilities import CapabilityFact
from mountainash.expressions.core.constants import CONST_BACKEND
from mountainash.expressions.backends.capabilities.polars import (
    POLARS_EXPR_CAPABILITIES,
)
from mountainash.expressions.backends.expression_systems.base import BaseExpressionSystem


class PolarsBaseExpressionSystem(BaseExpressionSystem):
    """Base class for Polars expression system components.

    Provides common functionality and backend identification for all
    Polars protocol implementations.
    """

    BACKEND_NAME: str = "polars"

    CAPABILITIES: tuple[CapabilityFact, ...] = POLARS_EXPR_CAPABILITIES

    @property
    def backend_type(self) -> CONST_BACKEND:
        """Return the Polars backend type identifier."""
        return CONST_BACKEND.POLARS

    def is_native_expression(self, expr: Any) -> bool:
        """Check if the expression is a native Polars expression.

        Args:
            expr: Any expression object to check.

        Returns:
            True if expr is a pl.Expr instance.
        """
        return isinstance(expr, pl.Expr)
