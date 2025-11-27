"""
Public API for Mountain Ash Expressions.

This module provides a Polars/Narwhals-style API for building expressions
that compile to backend-native expressions.

Example:
    >>> import mountainash_expressions as ma
    >>>
    >>> # Build expression (backend-agnostic)
    >>> expr = ma.col("age").gt(30).and_(ma.col("score").ge(85))
    >>>
    >>> # The expression is an AST that can be compiled to any backend
    >>> # (Currently: Polars, Narwhals, Ibis-Polars, Ibis-DuckDB, Ibis-SQLite)

Basic Usage:
    >>> # Column references
    >>> age_expr = ma.col("age")
    >>>
    >>> # Literals
    >>> threshold = ma.lit(30)
    >>>
    >>> # Comparisons
    >>> condition = ma.col("age").gt(30)
    >>>
    >>> # Logical operations
    >>> complex_filter = ma.col("age").gt(30).and_(ma.col("active").eq(True))
    >>>
    >>> # Arithmetic
    >>> total = ma.col("price").mul(ma.col("quantity"))
    >>>
    >>> # String operations
    >>> formatted = ma.col("name").str_upper().str_trim()
    >>>
    >>> # Temporal operations
    >>> year = ma.col("date").dt_year()
"""

from __future__ import annotations

# # Re-export expression API classes
# from .expression_builder import (
#     BaseExpressionAPI,
#     BooleanExpressionAPI,
#     ExpressionBuilder,  # Backwards compatibility alias
# )

# Entry point functions and conditional builders from namespaces
from ..core.namespaces import (
    col,
    lit,
    coalesce,
    greatest,
    least,
    when,
    native,
    WhenBuilder,
    WhenThenBuilder,
)

# # Re-export temporal helpers
# from .temporal_helpers import (
#     parse_time_expression,
#     to_timedelta,
#     to_offset_string,
#     time_ago,
#     since,
#     within_last,
#     within_next,
#     between_last,
#     older_than,
#     newer_than,
# )

__all__ = [
    # Expression API classes
    "BaseExpressionAPI",
    "BooleanExpressionAPI",
    "ExpressionBuilder",  # Deprecated alias

    # Entry point functions
    "col",
    "lit",
    "coalesce",
    "greatest",
    "least",
    "when",
    "native",
    "WhenBuilder",
    "WhenThenBuilder",

    # Temporal helpers
    "parse_time_expression",
    "to_timedelta",
    "to_offset_string",
    "time_ago",
    "since",
    "within_last",
    "within_next",
    "between_last",
    "older_than",
    "newer_than",
]
