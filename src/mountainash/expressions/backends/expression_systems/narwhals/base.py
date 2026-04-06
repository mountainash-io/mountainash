"""Narwhals backend base class.

Provides the base ExpressionSystem class for the Narwhals backend.
"""

from __future__ import annotations

from typing import Any

import narwhals as nw

from mountainash.core.types import KnownLimitation
from mountainash.expressions.core.constants import CONST_VISITOR_BACKENDS
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)
from mountainash.expressions.backends.expression_systems.base import BaseExpressionSystem


class NarwhalsBaseExpressionSystem(BaseExpressionSystem):
    """Base class for Narwhals expression system components.

    Provides common functionality and backend identification for all
    Narwhals protocol implementations.
    """

    BACKEND_NAME: str = "narwhals"

    _NW_STRING_LITERAL_ONLY = KnownLimitation(
        message="Narwhals string methods require literal values, not column references",
        native_errors=(TypeError,),
        workaround="Use a literal string value instead of a column reference",
    )

    KNOWN_EXPR_LIMITATIONS: dict[tuple[Any, str], KnownLimitation] = {
        (FK_STR.STARTS_WITH, "substring"): _NW_STRING_LITERAL_ONLY,
        (FK_STR.ENDS_WITH, "substring"): _NW_STRING_LITERAL_ONLY,
        (FK_STR.CONTAINS, "substring"): _NW_STRING_LITERAL_ONLY,
        (FK_STR.REPLACE, "substring"): _NW_STRING_LITERAL_ONLY,
        (FK_STR.REPLACE, "replacement"): _NW_STRING_LITERAL_ONLY,
        (FK_STR.LIKE, "match"): _NW_STRING_LITERAL_ONLY,
        (FK_STR.REGEXP_REPLACE, "pattern"): _NW_STRING_LITERAL_ONLY,
        (FK_STR.REGEXP_REPLACE, "replacement"): _NW_STRING_LITERAL_ONLY,
        (FK_STR.SUBSTRING, "start"): _NW_STRING_LITERAL_ONLY,
        (FK_STR.SUBSTRING, "length"): _NW_STRING_LITERAL_ONLY,
        (FK_STR.LEFT, "count"): _NW_STRING_LITERAL_ONLY,
        (FK_STR.RIGHT, "count"): _NW_STRING_LITERAL_ONLY,
        (FK_STR.TRIM, "characters"): _NW_STRING_LITERAL_ONLY,
        (FK_STR.LTRIM, "characters"): _NW_STRING_LITERAL_ONLY,
        (FK_STR.RTRIM, "characters"): _NW_STRING_LITERAL_ONLY,
    }

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

    def _extract_literal_if_possible(self, expr: Any) -> Any:
        """Extract literal value from a Narwhals expression.

        Narwhals/Pandas string methods require raw Python values -- they reject
        even nw.lit("hello"). This unwraps literal expressions back to raw
        values while letting column references pass through unchanged.
        """
        if isinstance(expr, (str, int, float, bool, type(None))):
            return expr
        if isinstance(expr, nw.Expr):
            expr_repr = repr(expr)
            if "lit(" in expr_repr.lower() or "literal" in expr_repr.lower():
                try:
                    import pandas as pd

                    tiny_df = nw.from_native(pd.DataFrame({"_": [0]}))
                    result = tiny_df.select(expr.alias("_val"))["_val"].to_list()[0]
                    return result
                except Exception:
                    pass
        return expr
