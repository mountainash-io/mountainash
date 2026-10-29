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

# Optional backends: probe the dependency itself so a genuine "backend not
# installed" is skipped, but a real (nested) ImportError inside the backend's
# own module surfaces instead of being silently swallowed.
try:
    import narwhals  # noqa: F401 — optional-backend availability probe
except ImportError:
    pass  # narwhals not installed — skip its expression system
else:
    from .expression_systems.narwhals import NarwhalsExpressionSystem
    __all__.append("NarwhalsExpressionSystem")

try:
    import ibis  # noqa: F401 — optional-backend availability probe
except ImportError:
    pass  # ibis not installed — skip its expression system
else:
    from .expression_systems.ibis import IbisExpressionSystem
    __all__.append("IbisExpressionSystem")
