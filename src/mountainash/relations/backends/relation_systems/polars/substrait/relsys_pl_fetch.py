"""Polars implementation of Substrait FetchRel."""

from __future__ import annotations

from typing import Optional

import polars as pl

from mountainash.relations.core.relation_protocols.relation_systems.substrait import (
    SubstraitFetchRelationSystemProtocol,
)


class SubstraitPolarsFetchRelationSystem(SubstraitFetchRelationSystemProtocol):
    """Offset/limit row retrieval on Polars LazyFrames."""

    def fetch(
        self, relation: pl.LazyFrame, offset: int, count: Optional[int], /
    ) -> pl.LazyFrame:
        if count is None:
            # All remaining rows from offset onward.
            return relation.slice(offset)
        return relation.slice(offset, count)

    def fetch_from_end(self, relation: pl.LazyFrame, count: int, /) -> pl.LazyFrame:
        return relation.tail(count)
