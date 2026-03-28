"""Backend implementations for relational operations.

Currently supported:
- Polars
- Narwhals (cross-backend compatibility layer)
- Ibis (multiple database backends: DuckDB, SQLite, Postgres, etc.)
"""

# Import relation systems to register them
from .relation_systems.polars import PolarsRelationSystem
from .relation_systems.narwhals import NarwhalsRelationSystem
from .relation_systems.ibis import IbisRelationSystem

__all__ = [
    "PolarsRelationSystem",
    "NarwhalsRelationSystem",
    "IbisRelationSystem",
]
