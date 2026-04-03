"""Polars relation system — composed backend for all relational operations."""
from __future__ import annotations

from mountainash.core.constants import CONST_BACKEND
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
