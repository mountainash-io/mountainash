"""Backend Expression Systems.

This module provides backend implementations for the ExpressionProtocol interfaces.
Each backend (Polars, Narwhals, Ibis) implements the same set of protocols, enabling
cross-backend expression compilation.

Backends are registered with the ExpressionVisitorFactory via the
@register_expression_system decorator.
"""

from .polars import PolarsExpressionSystem
# from .narwhals import NarwhalsExpressionSystem
# from .ibis import IbisExpressionSystem

__all__ = [
    "PolarsExpressionSystem",
    # "NarwhalsExpressionSystem",
    # "IbisExpressionSystem",
]
