"""Polars implementation of Substrait SortRel."""

from __future__ import annotations

import polars as pl

from mountainash.core.constants import SortField


class SubstraitPolarsSortRelationSystem:
    """Sort operations on Polars LazyFrames."""

    def sort(self, relation: pl.LazyFrame, sort_fields: list[SortField], /) -> pl.LazyFrame:
        return relation.sort(
            by=[sf.column for sf in sort_fields],
            descending=[sf.descending for sf in sort_fields],
            nulls_last=[sf.nulls_last for sf in sort_fields],
        )
