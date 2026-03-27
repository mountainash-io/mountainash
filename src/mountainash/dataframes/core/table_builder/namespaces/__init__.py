"""
Table operation namespaces.

Namespaces group related DataFrame operations and provide the implementation
for the fluent TableBuilder API.
"""

from .select import SelectNamespace
from .filter import FilterNamespace
from .join import JoinNamespace
from .row import RowNamespace
from .cast import CastNamespace
from .lazy import LazyNamespace

__all__ = [
    "SelectNamespace",
    "FilterNamespace",
    "JoinNamespace",
    "RowNamespace",
    "CastNamespace",
    "LazyNamespace",
]
