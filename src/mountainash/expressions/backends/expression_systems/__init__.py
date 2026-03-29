"""Backend Expression Systems.

This module provides backend implementations for the ExpressionProtocol interfaces.
Each backend (Polars, Narwhals, Ibis) implements the same set of protocols, enabling
cross-backend expression compilation.

Backends are registered with the ExpressionVisitorFactory via the
@register_expression_system decorator.
"""

from .polars import PolarsExpressionSystem

__all__ = [
    "PolarsExpressionSystem",
]

try:
    from .narwhals import NarwhalsExpressionSystem
    __all__.append("NarwhalsExpressionSystem")
except ImportError:
    pass

try:
    from .ibis import IbisExpressionSystem
    __all__.append("IbisExpressionSystem")
except ImportError:
    pass
