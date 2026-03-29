"""Narwhals implementation of Substrait AggregateRel."""

from __future__ import annotations

from typing import Any


class SubstraitNarwhalsAggregateRelationSystem:
    """Aggregation operations on Narwhals DataFrames."""

    def aggregate(self, relation: Any, keys: list[Any], measures: list[Any], /) -> Any:
        return relation.group_by(keys).agg(measures)

    def distinct(self, relation: Any, columns: list[Any], /) -> Any:
        if columns:
            return relation.unique(subset=columns)
        return relation.unique()
