"""Narwhals backend base class.

Provides the base ExpressionSystem class for the Narwhals backend.
"""

from __future__ import annotations

from typing import Any

import narwhals as nw

from mountainash.expressions.core.constants import CONST_VISITOR_BACKENDS
from mountainash.expressions.backends.expression_systems.base import BaseExpressionSystem


class NarwhalsBaseExpressionSystem(BaseExpressionSystem):
    """Base class for Narwhals expression system components.

    Provides common functionality and backend identification for all
    Narwhals protocol implementations.
    """

    @property
    def backend_type(self) -> CONST_VISITOR_BACKENDS:
        """Return the Narwhals backend type identifier."""
        return CONST_VISITOR_BACKENDS.NARWHALS

    def is_native_expression(self, expr: Any) -> bool:
        """Check if the expression is a native Narwhals expression.

        Args:
            expr: Any expression object to check.

        Returns:
            True if expr is a nw.Expr instance.
        """
        return isinstance(expr, nw.Expr)

    def _extract_literal_value(self, expr: Any) -> Any:
        """Extract the literal value from a Narwhals literal expression.

        Narwhals wrapping Pandas doesn't support Expr patterns in string
        operations like contains(), starts_with(), ends_with(). This helper
        extracts the underlying value from nw.lit() expressions.

        Args:
            expr: A Narwhals expression or literal value.

        Returns:
            The underlying Python value if it's a literal expression,
            otherwise returns the expr unchanged.
        """
        # If it's already a raw Python value, return as-is
        if isinstance(expr, (str, int, float, bool, type(None))):
            return expr

        # If it's a Narwhals Expr, try to extract the literal value
        if isinstance(expr, nw.Expr):
            # Check if this is a literal expression by looking at the repr
            # Narwhals literals have a recognizable pattern
            expr_repr = repr(expr)
            if "lit(" in expr_repr.lower() or "literal" in expr_repr.lower():
                # Try to extract from the internal representation
                # The underlying value is typically stored in the expression
                try:
                    # For Narwhals, we can try to access the underlying call
                    # This is backend-dependent, so we need a workaround
                    # Create a tiny DataFrame to evaluate the literal
                    import pandas as pd
                    tiny_df = nw.from_native(pd.DataFrame({"_": [0]}))
                    result = tiny_df.select(expr.alias("_val"))["_val"].to_list()[0]
                    return result
                except Exception:
                    pass

        # If extraction fails, return the original expr
        # This will work for Polars-backed Narwhals but may fail for Pandas
        return expr
