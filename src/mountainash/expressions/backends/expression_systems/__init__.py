"""Backend Expression Systems.

This module provides backend implementations for the ExpressionProtocol interfaces.
Each backend (Polars, Narwhals, Ibis) implements the same set of protocols, enabling
cross-backend expression compilation.

Backends are registered with the ExpressionVisitorFactory via the
@register_expression_system decorator.
"""
from __future__ import annotations

from .polars import PolarsExpressionSystem

__all__ = [
    "PolarsExpressionSystem",
]

# Optional backends: probe the dependency itself so a genuine "backend not
# installed" is skipped, but a real (nested) ImportError inside the backend's
# own module surfaces instead of being silently swallowed.
try:
    import narwhals  # noqa: F401 — optional-backend availability probe
except ImportError:
    pass  # narwhals not installed — skip its expression system
else:
    from .narwhals import NarwhalsExpressionSystem
    __all__.append("NarwhalsExpressionSystem")

try:
    import ibis  # noqa: F401 — optional-backend availability probe
except ImportError:
    pass  # ibis not installed — skip its expression system
else:
    from .ibis import IbisExpressionSystem
    __all__.append("IbisExpressionSystem")
