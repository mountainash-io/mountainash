"""Narwhals backend implementation of ExpressionSystem."""

from typing import Any
import narwhals as nw

from ....core.expression_system import ExpressionSystem
from ....core.constants import CONST_VISITOR_BACKENDS


class NarwhalsBaseExpressionSystem(ExpressionSystem):
    """
    Narwhals-specific implementation of ExpressionSystem.

    This class encapsulates all Narwhals-specific operations,
    allowing visitors to build expressions without direct knowledge
    of the Narwhals API.
    """

    @property
    def backend_type(self) -> CONST_VISITOR_BACKENDS:
        """Return Narwhals backend type."""
        return CONST_VISITOR_BACKENDS.NARWHALS

    def is_native_expression(self, expr: Any) -> bool:
        """
        Check if an expression is a native Narwhals expression.

        Args:
            expr: Expression to check

        Returns:
            True if expr is a nw.Expr, False otherwise

        Note:
            ISSUE: Missing from deprecated backend - added to match ExpressionSystem requirement.
        """
        return isinstance(expr, nw.Expr)
