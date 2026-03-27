"""Mountainash - Unified cross-backend DataFrame expression system."""

# Re-export the full expressions public API at the top level
# so that `import mountainash as ma; ma.col("x")` works
from mountainash.expressions import (
    BaseExpressionAPI,
    BooleanExpressionAPI,
    col,
    lit,
    native,
    coalesce,
    greatest,
    least,
    when,
    t_col,
    always_true,
    always_false,
    always_unknown,
    CONST_VISITOR_BACKENDS,
    CONST_LOGIC_TYPES,
    CONST_EXPRESSION_NODE_TYPES,
)  # noqa: F401

from mountainash.expressions.__version__ import __version__  # noqa: F401

# Dataframes - TableBuilder fluent API
try:
    from mountainash.dataframes import table, TableBuilder  # noqa: F401
except ImportError:
    pass  # dataframes module not yet available
