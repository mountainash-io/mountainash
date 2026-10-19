"""Ibis relation system — composed from all substrait and extension mixins."""
from __future__ import annotations

from mountainash.core.constants import CONST_BACKEND
from mountainash.core.lowering_reuse import declare_lowering, LoweringDescriptor, ReuseCase
from mountainash.relations.core.relation_protocols.relsys_base import register_relation_system

from .base import IbisBaseRelationSystem
from .substrait import (
    SubstraitIbisReadRelationSystem,
    SubstraitIbisProjectRelationSystem,
    SubstraitIbisFilterRelationSystem,
    SubstraitIbisSortRelationSystem,
    SubstraitIbisFetchRelationSystem,
    SubstraitIbisJoinRelationSystem,
    SubstraitIbisAggregateRelationSystem,
    SubstraitIbisSetRelationSystem,
)
from .extensions_mountainash import (
    MountainashIbisExtensionRelationSystem,
)


@register_relation_system(CONST_BACKEND.IBIS)
class IbisRelationSystem(
    IbisBaseRelationSystem,
    SubstraitIbisReadRelationSystem,
    SubstraitIbisProjectRelationSystem,
    SubstraitIbisFilterRelationSystem,
    SubstraitIbisSortRelationSystem,
    SubstraitIbisFetchRelationSystem,
    SubstraitIbisJoinRelationSystem,
    SubstraitIbisAggregateRelationSystem,
    SubstraitIbisSetRelationSystem,
    MountainashIbisExtensionRelationSystem,
):
    """Ibis relation system — all operations composed via multiple inheritance."""

    pass



for _name in (
    "read", "project_select", "project_with_columns", "project_drop", "project_rename",
    "filter", "sort", "fetch", "join", "aggregate", "distinct", "union_all",
    "union_distinct", "drop_nulls", "drop_nans", "with_row_index", "explode",
    "sample", "unpivot", "top_k", "unnest", "fetch_from_end", "join_asof",
    "empty_frame", "read_resource",
):
    declare_lowering(getattr(IbisRelationSystem, _name))
declare_lowering(IbisRelationSystem.pivot, LoweringDescriptor(ReuseCase.REPEATABLE, materializes_input=True))
del _name
