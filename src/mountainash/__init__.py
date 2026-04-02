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

from mountainash.__version__ import __version__  # noqa: F401

# Relations - Substrait-aligned relational AST
from mountainash.relations import relation, concat  # noqa: F401

# TypeSpec - backend-agnostic type specification
from mountainash.typespec.spec import TypeSpec  # noqa: F401

# Conform - compile type specifications to relation operations
from mountainash.conform.builder import ConformBuilder  # noqa: F401


def typespec(columns: dict[str, str], **metadata) -> TypeSpec:
    """Create a TypeSpec from a simple {name: type_string} dict."""
    return TypeSpec.from_simple_dict(columns, **metadata)


def conform(source: dict | TypeSpec) -> ConformBuilder:
    """Create a ConformBuilder from a dict or TypeSpec."""
    return ConformBuilder(source)

"""Mountainash - Unified cross-backend DataFrame expression system."""
