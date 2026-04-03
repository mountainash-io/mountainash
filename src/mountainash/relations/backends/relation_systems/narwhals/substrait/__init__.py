"""Narwhals implementations of Substrait relation operations."""
from __future__ import annotations

from .relsys_nw_read import SubstraitNarwhalsReadRelationSystem
from .relsys_nw_project import SubstraitNarwhalsProjectRelationSystem
from .relsys_nw_filter import SubstraitNarwhalsFilterRelationSystem
from .relsys_nw_sort import SubstraitNarwhalsSortRelationSystem
from .relsys_nw_fetch import SubstraitNarwhalsFetchRelationSystem
from .relsys_nw_join import SubstraitNarwhalsJoinRelationSystem
from .relsys_nw_aggregate import SubstraitNarwhalsAggregateRelationSystem
from .relsys_nw_set import SubstraitNarwhalsSetRelationSystem

__all__ = [
    "SubstraitNarwhalsReadRelationSystem",
    "SubstraitNarwhalsProjectRelationSystem",
    "SubstraitNarwhalsFilterRelationSystem",
    "SubstraitNarwhalsSortRelationSystem",
    "SubstraitNarwhalsFetchRelationSystem",
    "SubstraitNarwhalsJoinRelationSystem",
    "SubstraitNarwhalsAggregateRelationSystem",
    "SubstraitNarwhalsSetRelationSystem",
]
