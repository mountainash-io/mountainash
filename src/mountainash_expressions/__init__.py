"""Mountain Ash Expressions

A sophisticated dual-logic expression system for building cross-backend DataFrame operations.
Supports Boolean (TRUE/FALSE) and Ternary (TRUE/FALSE/UNKNOWN) logic systems with automatic
backend detection across pandas, polars, Ibis, PyArrow, and Narwhals.

Quick Start:
    >>> import mountainash_expressions as ma
    >>>
    >>> # Build expression (backend-agnostic)
    >>> expr = ma.col("age").gt(30).and_(ma.col("score").ge(85))
    >>>
    >>> # Compile to backend-native expression
    >>> backend_expr = expr.compile(df)
    >>>
    >>> # Use with dataframe
    >>> result = df.filter(backend_expr)
    >>>
    >>> # Or use helper functions
    >>> result = ma.filter(df, ma.col("age").gt(30))
    >>>
    >>> # Natural language temporal filtering (like journalctl/find)
    >>> # Show logs from last 10 minutes
    >>> recent_logs = ma.filter(logs, ma.within_last(ma.col("timestamp"), "10 minutes"))
    >>>
    >>> # Find files older than 7 days
    >>> old_files = ma.filter(files, ma.older_than(ma.col("created_at"), "7 days"))
    >>>
    >>> # Date arithmetic and temporal operations
    >>> expr = ma.col("timestamp").dt_add_hours(2).dt_truncate("1d")
"""

from .__version__ import __version__

# ========================================
# Public API (Primary Interface)
# ========================================
from .api import (
    # Builder class
    ExpressionBuilder,
    # Entry points
    col,
    lit,
    # Helper functions
    filter,
    select,
    with_columns,
    # Conditional operations
    when,
    coalesce,
    # Logical combinators
    and_,
    or_,
    not_,
)

# Temporal helpers - natural language time filtering
from .api.temporal_helpers import (
    # Parsing utilities
    parse_time_expression,
    to_timedelta,
    to_offset_string,
    # Absolute time functions
    time_ago,
    since,
    # Filter expressions
    within_last,
    within_next,
    between_last,
    older_than,
    newer_than,
)

# Core constants
from .core.constants import (
    CONST_VISITOR_BACKENDS,
    CONST_LOGIC_TYPES,
    CONST_EXPRESSION_NODE_TYPES,
    CONST_EXPRESSION_LOGICAL_OPERATORS,
    CONST_TERNARY_LOGIC_VALUES,
)

# Expression nodes - base types
from .core.expression_nodes import (
    ExpressionNode,
    NativeBackendExpressionNode,
    SourceExpressionNode,
    LiteralExpressionNode,
    CastExpressionNode,
    LogicalConstantExpressionNode,
    UnaryExpressionNode,
    LogicalExpressionNode,
    ComparisonExpressionNode,
    CollectionExpressionNode,
    ArithmeticExpressionNode,
    ConditionalIfElseExpressionNode,
)

# Expression nodes - Boolean logic
from .core.expression_nodes import (
    BooleanExpressionNode,
    BooleanUnaryExpressionNode,
    BooleanLogicalExpressionNode,
    BooleanComparisonExpressionNode,
    BooleanConditionalIfElseExpressionNode,
    BooleanCollectionExpressionNode,
)

# Visitor pattern
from .core.expression_visitors import (
    ExpressionVisitor,
    # BooleanExpressionVisitor,
    ExpressionVisitorFactory,
)

# Backend visitor interface
from .core.backend_visitors import BackendVisitor

# Parameter system
from .core.expression_parameters import ExpressionParameter, ParameterType

__all__ = [
    # Version
    "__version__",

    # Constants
    "CONST_VISITOR_BACKENDS",
    "CONST_LOGIC_TYPES",
    "CONST_EXPRESSION_NODE_TYPES",
    "CONST_EXPRESSION_LOGICAL_OPERATORS",
    "CONST_TERNARY_LOGIC_VALUES",

    # Base expression nodes
    "ExpressionNode",
    "NativeBackendExpressionNode",
    "SourceExpressionNode",
    "LiteralExpressionNode",
    "CastExpressionNode",
    "LogicalConstantExpressionNode",
    "UnaryExpressionNode",
    "LogicalExpressionNode",
    "ComparisonExpressionNode",
    "CollectionExpressionNode",
    "ArithmeticExpressionNode",
    "ConditionalIfElseExpressionNode",

    # Boolean expression nodes
    "BooleanExpressionNode",
    "BooleanUnaryExpressionNode",
    "BooleanLogicalExpressionNode",
    "BooleanComparisonExpressionNode",
    "BooleanConditionalIfElseExpressionNode",
    "BooleanCollectionExpressionNode",

    # Visitor pattern
    "ExpressionVisitor",
    # "BooleanExpressionVisitor",
    "ExpressionVisitorFactory",

    # Backend visitor
    "BackendVisitor",

    # Parameter system
    "ExpressionParameter",
    "ParameterType",

    # Temporal helpers - natural language time filtering
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
