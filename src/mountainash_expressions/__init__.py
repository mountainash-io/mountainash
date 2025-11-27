"""Mountain Ash Expressions

A sophisticated expression system for building cross-backend DataFrame operations.
Supports Boolean logic with automatic backend detection across Polars, Narwhals, Ibis, and Pandas.

Architecture:
- Protocol-driven design with three layers (Visitor, Expression, Builder)
- Namespace-based composition for clean separation of concerns
- ExpressionNode AST that compiles to backend-native expressions

Quick Start:
    >>> import mountainash_expressions as ma
    >>>
    >>> # Build expression (backend-agnostic AST)
    >>> expr = ma.col("age").gt(30).and_(ma.col("score").ge(85))
    >>>
    >>> # The expression automatically compiles for any supported backend
    >>> # Use with Polars, Narwhals, Ibis (Polars/DuckDB/SQLite), or Pandas DataFrames

Supported Operations:
    - Boolean: eq, ne, gt, lt, ge, le, and_, or_, not_, is_in
    - Arithmetic: add, subtract, multiply, divide, modulo, power, floor_divide
    - String: str_upper, str_lower, str_trim, str_contains, pat_regex_match
    - Temporal: dt_year, dt_month, dt_add_days, dt_diff_hours
    - Null: is_null, not_null, fill_null, coalesce
    - Type: cast
    - Name: alias, prefix, suffix
    - Iterable: coalesce, greatest, least
    - Native: native (wrap backend-specific expressions)

Python Operator Overloading:
    >>> # Use natural Python syntax
    >>> expr = (ma.col("price") * ma.col("quantity")) + ma.col("tax")
    >>> # Equivalent to:
    >>> expr = ma.col("price").multiply(ma.col("quantity")).add(ma.col("tax"))
"""

from .__version__ import __version__

# ========================================
# Backend Registration
# ========================================
# Import backends to register expression systems
from . import backends  # noqa: F401

# ========================================
# Public API (Primary Interface)
# ========================================
from .api import (
    # Expression API classes
    BaseExpressionAPI,
    BooleanExpressionAPI,
    ExpressionBuilder,  # Backwards compatibility alias

    # Entry point functions (from namespaces)
    col,
    lit,
    coalesce,
    greatest,
    least,
    when,
)

# ========================================
# Core constants
# ========================================
from .core.constants import (
    CONST_VISITOR_BACKENDS,
    CONST_LOGIC_TYPES,
    CONST_EXPRESSION_NODE_TYPES,
)

__all__ = [
    # Version
    "__version__",

    # Expression API classes
    "BaseExpressionAPI",
    "BooleanExpressionAPI",
    "ExpressionBuilder",  # Deprecated alias

    # Factory functions (PRIMARY API)
    "col",
    "lit",

    # Conditional functions
    "coalesce",
    "greatest",
    "least",
    "when",

    # Constants
    "CONST_VISITOR_BACKENDS",
    "CONST_LOGIC_TYPES",
    "CONST_EXPRESSION_NODE_TYPES",
]
