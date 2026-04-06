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
    FKEY_MOUNTAINASH_SCALAR_DATETIME as FK_DT,
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

    _NW_DATETIME_OFFSET_LITERAL_ONLY = KnownLimitation(
        message="Narwhals datetime offset operations require literal integer values",
        native_errors=(TypeError,),
        workaround="Use a literal integer for the offset amount",
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
        (FK_DT.ADD_YEARS, "years"): _NW_DATETIME_OFFSET_LITERAL_ONLY,
        (FK_DT.ADD_MONTHS, "months"): _NW_DATETIME_OFFSET_LITERAL_ONLY,
        (FK_DT.ADD_DAYS, "days"): _NW_DATETIME_OFFSET_LITERAL_ONLY,
        (FK_DT.ADD_HOURS, "hours"): _NW_DATETIME_OFFSET_LITERAL_ONLY,
        (FK_DT.ADD_MINUTES, "minutes"): _NW_DATETIME_OFFSET_LITERAL_ONLY,
        (FK_DT.ADD_SECONDS, "seconds"): _NW_DATETIME_OFFSET_LITERAL_ONLY,
        (FK_DT.ADD_MILLISECONDS, "milliseconds"): _NW_DATETIME_OFFSET_LITERAL_ONLY,
        (FK_DT.ADD_MICROSECONDS, "microseconds"): _NW_DATETIME_OFFSET_LITERAL_ONLY,
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
        """Extract the literal value from a backend literal expression.

        .. deprecated::
            Use ``_extract_literal_if_possible()`` + ``_call_with_expr_support()`` instead.
            See: docs/superpowers/specs/2026-04-06-expression-argument-consistency-design.md
            Remaining callers: datetime, rounding, logarithmic, name operations.
            Will be removed once all callers are migrated.
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
