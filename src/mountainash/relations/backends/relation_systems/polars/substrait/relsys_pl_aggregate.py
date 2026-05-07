"""Polars implementation of Substrait AggregateRel."""

from __future__ import annotations

from typing import Any

import polars as pl

from mountainash.relations.core.relation_protocols.relation_systems.substrait import (
    SubstraitAggregateRelationSystemProtocol,
)


class SubstraitPolarsAggregateRelationSystem(SubstraitAggregateRelationSystemProtocol):
    """Aggregation operations on Polars LazyFrames."""

    def aggregate(
        self, relation: pl.LazyFrame, keys: list[Any], measures: list[Any], /
    ) -> pl.LazyFrame:
        if not keys:
            # Global aggregate (no group-by keys): use select() to get a
            # single-row scalar result.  group_by([]) raises a ComputeError.
            return relation.select(measures)
        return relation.group_by(keys).agg(measures)

    def distinct(self, relation: pl.LazyFrame, columns: list[Any], /) -> pl.LazyFrame:
        if columns:
            return relation.unique(subset=columns)
        return relation.unique()
