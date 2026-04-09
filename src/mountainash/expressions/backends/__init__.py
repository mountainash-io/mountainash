"""Backend implementations for different DataFrame libraries.

Currently supported:
- Polars
- Narwhals (cross-backend compatibility layer)
- Ibis (multiple database backends: DuckDB, SQLite, Postgres, etc.)

Planned:
- Pandas
- PyArrow
"""
from __future__ import annotations

# Import expression systems to register them.
# Polars is a core dependency — always imported.
# Narwhals and Ibis are optional — imported only if available.
from .expression_systems.polars import PolarsExpressionSystem

__all__ = [
    "PolarsExpressionSystem",
]

try:
    from .expression_systems.narwhals import NarwhalsExpressionSystem
    __all__.append("NarwhalsExpressionSystem")
except ImportError:
    pass

try:
    from .expression_systems.ibis import IbisExpressionSystem
    __all__.append("IbisExpressionSystem")
except ImportError:
    pass
