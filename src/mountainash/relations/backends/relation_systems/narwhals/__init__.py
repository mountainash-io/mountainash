"""Narwhals relation system — composed backend for pandas, PyArrow, and cuDF."""
from __future__ import annotations

from mountainash.core.constants import CONST_BACKEND
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
