"""Narwhals implementation of Substrait AggregateRel."""

from __future__ import annotations

from typing import Any

from mountainash.relations.core.relation_protocols.relation_systems.substrait import (
    SubstraitAggregateRelationSystemProtocol,
)


class SubstraitNarwhalsAggregateRelationSystem(SubstraitAggregateRelationSystemProtocol):
    """Aggregation operations on Narwhals DataFrames."""

    def aggregate(self, relation: Any, keys: list[Any], measures: list[Any], /) -> Any:
        if not keys:
            # Global aggregate (no group-by keys): use select() to get a
            # single-row scalar result.  group_by([]) is not portable across
            # Narwhals-backed libraries.
            return relation.select(measures)
        return relation.group_by(keys).agg(measures)

    def distinct(self, relation: Any, columns: list[Any], /) -> Any:
        if columns:
            return relation.unique(subset=columns)
        return relation.unique()
