"""Ibis backend implementation of ExpressionSystem."""

from typing import Any
import ibis.expr.types as ir

from ....core.expression_system import ExpressionSystem
from ....core.constants import CONST_VISITOR_BACKENDS


class IbisBaseExpressionSystem(ExpressionSystem):
    """
    Ibis-specific implementation of ExpressionSystem.

    This class encapsulates all Ibis-specific operations,
    allowing visitors to build expressions without direct knowledge
    of the Ibis API.
    """

    @property
    def backend_type(self) -> CONST_VISITOR_BACKENDS:
        """Return Ibis backend type."""
        return CONST_VISITOR_BACKENDS.IBIS

    def is_native_expression(self, expr: Any) -> bool:
        """
        Check if an expression is a native Ibis expression.

        Args:
            expr: Expression to check

        Returns:
            True if expr is an ir.Expr, False otherwise

        Note:
            ISSUE: Missing from deprecated backend - added to match ExpressionSystem requirement.
        """
        return isinstance(expr, ir.Expr)
