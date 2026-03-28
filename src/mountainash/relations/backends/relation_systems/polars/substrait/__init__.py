"""Polars implementations of Substrait-aligned relation system protocols."""

from .relsys_pl_read import SubstraitPolarsReadRelationSystem
from .relsys_pl_project import SubstraitPolarsProjectRelationSystem
from .relsys_pl_filter import SubstraitPolarsFilterRelationSystem
from .relsys_pl_sort import SubstraitPolarsSortRelationSystem
from .relsys_pl_fetch import SubstraitPolarsFetchRelationSystem
from .relsys_pl_join import SubstraitPolarsJoinRelationSystem
from .relsys_pl_aggregate import SubstraitPolarsAggregateRelationSystem
from .relsys_pl_set import SubstraitPolarsSetRelationSystem

__all__ = [
    "SubstraitPolarsReadRelationSystem",
    "SubstraitPolarsProjectRelationSystem",
    "SubstraitPolarsFilterRelationSystem",
    "SubstraitPolarsSortRelationSystem",
    "SubstraitPolarsFetchRelationSystem",
    "SubstraitPolarsJoinRelationSystem",
    "SubstraitPolarsAggregateRelationSystem",
    "SubstraitPolarsSetRelationSystem",
]
