"""Polars implementation of Substrait AggregateRel."""

from __future__ import annotations

from typing import Any

import polars as pl


class SubstraitPolarsAggregateRelationSystem:
    """Aggregation operations on Polars LazyFrames."""

    def aggregate(
        self, relation: pl.LazyFrame, keys: list[Any], measures: list[Any], /
    ) -> pl.LazyFrame:
        return relation.group_by(keys).agg(measures)

    def distinct(self, relation: pl.LazyFrame, columns: list[Any], /) -> pl.LazyFrame:
        if columns:
            return relation.unique(subset=columns)
        return relation.unique()
