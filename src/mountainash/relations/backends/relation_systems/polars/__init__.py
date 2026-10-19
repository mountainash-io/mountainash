"""Polars relation system — composed backend for all relational operations."""
from __future__ import annotations

from mountainash.core.constants import CONST_BACKEND
from mountainash.core.lowering_reuse import declare_lowering, LoweringDescriptor, ReuseCase
from mountainash.relations.core.relation_protocols.relsys_base import register_relation_system

from .base import PolarsBaseRelationSystem
from .substrait import (
    SubstraitPolarsReadRelationSystem,
    SubstraitPolarsProjectRelationSystem,
    SubstraitPolarsFilterRelationSystem,
    SubstraitPolarsSortRelationSystem,
    SubstraitPolarsFetchRelationSystem,
    SubstraitPolarsJoinRelationSystem,
    SubstraitPolarsAggregateRelationSystem,
    SubstraitPolarsSetRelationSystem,
)
from .extensions_mountainash import MountainashPolarsExtensionRelationSystem


@register_relation_system(CONST_BACKEND.POLARS)
class PolarsRelationSystem(
    PolarsBaseRelationSystem,
    SubstraitPolarsReadRelationSystem,
    SubstraitPolarsProjectRelationSystem,
    SubstraitPolarsFilterRelationSystem,
    SubstraitPolarsSortRelationSystem,
    SubstraitPolarsFetchRelationSystem,
    SubstraitPolarsJoinRelationSystem,
    SubstraitPolarsAggregateRelationSystem,
    SubstraitPolarsSetRelationSystem,
    MountainashPolarsExtensionRelationSystem,
):
    """Polars relation system — composes all protocol implementations."""

    pass



for _name in (
    "read", "project_select", "project_with_columns", "project_drop", "project_rename",
    "filter", "sort", "fetch", "join", "aggregate", "distinct", "union_all",
    "union_distinct", "drop_nulls", "drop_nans", "with_row_index", "explode",
    "sample", "unpivot", "top_k", "unnest", "fetch_from_end", "join_asof",
    "empty_frame", "read_resource",
):
    declare_lowering(getattr(PolarsRelationSystem, _name))
declare_lowering(PolarsRelationSystem.pivot, LoweringDescriptor(ReuseCase.REPEATABLE, materializes_input=True))
del _name
