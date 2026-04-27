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
    FKEY_MOUNTAINASH_SCALAR_STRING as FK_MA_STR,
    FKEY_MOUNTAINASH_SCALAR_TERNARY as FK_MA_TERN,
)
from mountainash.expressions.backends.expression_systems.base import BaseExpressionSystem


class NarwhalsBaseExpressionSystem(BaseExpressionSystem):
    """Base class for Narwhals expression system components.

    Provides common functionality and backend identification for all
    Narwhals protocol implementations.
    """

    BACKEND_NAME: str = "narwhals"

    _NW_STRING_LITERAL_ONLY = KnownLimitation(
        message=(
            "Narwhals string methods require literal values, not column references, "
            "on the pandas backend. The polars-backed narwhals path supports "
            "expression arguments for str.contains (since narwhals 2.19.0) but "
            "other string methods remain literal-only on all narwhals sub-backends."
        ),
        native_errors=(TypeError,),
        workaround="Use a literal string value instead of a column reference",
    )

    _NW_DATETIME_OFFSET_LITERAL_ONLY = KnownLimitation(
        message="Narwhals datetime offset operations require literal integer values",
        native_errors=(TypeError,),
        workaround="Use a literal integer for the offset amount",
    )

    _NW_LIST_CONTAINS_LIMITED = KnownLimitation(
        message=(
            "Narwhals (as of 2.19.0) does not accept expression arguments for "
            "list.contains on any native backend — its `item` parameter is typed "
            "`NonNestedLiteral` and rejects Expr. Use the polars or an ibis "
            "backend directly, or pass a literal list/tuple/set as the argument."
        ),
        native_errors=(TypeError, AttributeError),
        workaround="Use a literal collection, the polars backend, or an ibis backend",
    )

    KNOWN_EXPR_LIMITATIONS: dict[tuple[Any, str], KnownLimitation] = {
        (FK_STR.STARTS_WITH, "substring"): _NW_STRING_LITERAL_ONLY,
        (FK_STR.ENDS_WITH, "substring"): _NW_STRING_LITERAL_ONLY,
        (FK_STR.CONTAINS, "substring"): _NW_STRING_LITERAL_ONLY,
        (FK_STR.REPLACE, "substring"): _NW_STRING_LITERAL_ONLY,
        (FK_STR.REPLACE, "replacement"): _NW_STRING_LITERAL_ONLY,
        (FK_STR.LIKE, "match"): _NW_STRING_LITERAL_ONLY,
        # Mountainash extension — regex_contains pattern is literal-only
        # on every backend (per arguments-vs-options.md). Defensive entry:
        # the API builder rejects non-str patterns at build time, so this
        # lookup should never actually fire — but if a future caller routes
        # around the builder this surfaces an enriched error instead of the
        # raw `TypeError: unhashable type: 'Expr'` from re.compile.
        (FK_MA_STR.REGEX_CONTAINS, "pattern"): _NW_STRING_LITERAL_ONLY,
        (FK_MA_TERN.T_IS_IN, "collection"): _NW_LIST_CONTAINS_LIMITED,
        (FK_MA_TERN.T_IS_NOT_IN, "collection"): _NW_LIST_CONTAINS_LIMITED,
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
