"""Narwhals relation system — composed backend for pandas, PyArrow, and cuDF."""
from __future__ import annotations

from mountainash.core.constants import CONST_BACKEND
from mountainash.core.lowering_reuse import declare_lowering, LoweringDescriptor, ReuseCase
from mountainash.relations.core.relation_protocols.relsys_base import register_relation_system

from .base import NarwhalsBaseRelationSystem
from .substrait import (
    SubstraitNarwhalsReadRelationSystem,
    SubstraitNarwhalsProjectRelationSystem,
    SubstraitNarwhalsFilterRelationSystem,
    SubstraitNarwhalsSortRelationSystem,
    SubstraitNarwhalsFetchRelationSystem,
    SubstraitNarwhalsJoinRelationSystem,
    SubstraitNarwhalsAggregateRelationSystem,
    SubstraitNarwhalsSetRelationSystem,
)
from .extensions_mountainash import MountainashNarwhalsExtensionRelationSystem


@register_relation_system(CONST_BACKEND.NARWHALS)
class NarwhalsRelationSystem(
    NarwhalsBaseRelationSystem,
    SubstraitNarwhalsReadRelationSystem,
    SubstraitNarwhalsProjectRelationSystem,
    SubstraitNarwhalsFilterRelationSystem,
    SubstraitNarwhalsSortRelationSystem,
    SubstraitNarwhalsFetchRelationSystem,
    SubstraitNarwhalsJoinRelationSystem,
    SubstraitNarwhalsAggregateRelationSystem,
    SubstraitNarwhalsSetRelationSystem,
    MountainashNarwhalsExtensionRelationSystem,
):
    """Complete Narwhals relation system.

    Wraps pandas, PyArrow, and cuDF DataFrames via the Narwhals adapter
    layer, providing a uniform API for all relational operations.
    """

    pass



for _name in (
    "read", "project_select", "project_with_columns", "project_drop", "project_rename",
    "filter", "sort", "fetch", "join", "aggregate", "distinct", "union_all",
    "union_distinct", "drop_nulls", "drop_nans", "with_row_index", "explode",
    "sample", "unpivot", "top_k", "unnest", "fetch_from_end", "join_asof",
    "empty_frame", "read_resource",
):
    declare_lowering(getattr(NarwhalsRelationSystem, _name))
declare_lowering(NarwhalsRelationSystem.pivot, LoweringDescriptor(ReuseCase.REPEATABLE, materializes_input=True))
del _name
