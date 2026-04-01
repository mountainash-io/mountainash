# Import relation systems to register them.
# Polars is a core dependency — always imported.
# Narwhals and Ibis are optional — imported only if available.
from .relation_systems.polars import PolarsRelationSystem

"""Backend implementations for relational operations.

Currently supported:
- Polars
- Narwhals (cross-backend compatibility layer)
- Ibis (multiple database backends: DuckDB, SQLite, Postgres, etc.)
"""


__all__ = [
    "PolarsRelationSystem",
]

try:
    from .relation_systems.narwhals import NarwhalsRelationSystem
    __all__.append("NarwhalsRelationSystem")
except ImportError:
    pass

try:
    from .relation_systems.ibis import IbisRelationSystem
    __all__.append("IbisRelationSystem")
except ImportError:
    pass
