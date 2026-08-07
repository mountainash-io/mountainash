"""Narwhals backend base class.

Provides the base ExpressionSystem class for the Narwhals backend.
"""

from __future__ import annotations

from typing import Any

import narwhals as nw

from mountainash.core.capabilities import CapabilityFact
from mountainash.expressions.core.constants import CONST_BACKEND
from mountainash.expressions.backends.capabilities.narwhals import (
    NARWHALS_EXPR_CAPABILITIES,
)
from mountainash.expressions.backends.expression_systems.base import BaseExpressionSystem


class NarwhalsBaseExpressionSystem(BaseExpressionSystem):
    """Base class for Narwhals expression system components.

    Provides common functionality and backend identification for all
    Narwhals protocol implementations.
    """

    BACKEND_NAME: str = "narwhals"

    CAPABILITIES: tuple[CapabilityFact, ...] = NARWHALS_EXPR_CAPABILITIES

    @property
    def backend_type(self) -> CONST_BACKEND:
        """Return the Narwhals backend type identifier."""
        return CONST_BACKEND.NARWHALS

    def is_native_expression(self, expr: Any) -> bool:
        """Check if the expression is a native Narwhals expression.

        Args:
            expr: Any expression object to check.

        Returns:
            True if expr is a nw.Expr instance.
        """
        return isinstance(expr, nw.Expr)
