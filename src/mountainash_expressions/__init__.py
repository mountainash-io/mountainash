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
    BooleanExpressionVisitor,
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
    "BooleanExpressionVisitor",
    "ExpressionVisitorFactory",

    # Backend visitor
    "BackendVisitor",

    # Parameter system
    "ExpressionParameter",
    "ParameterType",
]
