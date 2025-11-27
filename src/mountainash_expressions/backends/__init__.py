"""Backend implementations for different DataFrame libraries.

Currently supported:
- Polars
- Narwhals (cross-backend compatibility layer)
- Ibis

Planned:
- Pandas
- PyArrow
"""

# Import expression systems to register them
from .expression_systems.polars import PolarsExpressionSystem
from .expression_systems.narwhals import NarwhalsExpressionSystem
from .expression_systems.ibis import IbisExpressionSystem

__all__ = [
    "PolarsExpressionSystem",
    "NarwhalsExpressionSystem",
    "IbisExpressionSystem",
]
