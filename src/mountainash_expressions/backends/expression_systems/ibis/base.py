"""Ibis backend base class.

Provides the base ExpressionSystem class for the Ibis backend.
"""

from __future__ import annotations

from typing import Any

import ibis
import ibis.expr.types as ir

from mountainash_expressions.core.constants import CONST_VISITOR_BACKENDS
from mountainash_expressions.backends.expression_systems.base import BaseExpressionSystem


class IbisBaseExpressionSystem(BaseExpressionSystem):
    """Base class for Ibis expression system components.

    Provides common functionality and backend identification for all
    Ibis protocol implementations.
    """

    @property
    def backend_type(self) -> CONST_VISITOR_BACKENDS:
        """Return the Ibis backend type identifier."""
        return CONST_VISITOR_BACKENDS.IBIS

    def is_native_expression(self, expr: Any) -> bool:
        """Check if the expression is a native Ibis expression.

        Args:
            expr: Any expression object to check.

        Returns:
            True if expr is an Ibis expression type.
        """
        return isinstance(expr, (ir.Column, ir.Scalar, ir.Expr))
