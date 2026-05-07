"""Polars implementation of Substrait SetRel."""

from __future__ import annotations

import polars as pl

from mountainash.relations.core.relation_protocols.relation_systems.substrait import (
    SubstraitSetRelationSystemProtocol,
)


class SubstraitPolarsSetRelationSystem(SubstraitSetRelationSystemProtocol):
    """Set operations on Polars LazyFrames."""

    def union_all(self, relations: list[pl.LazyFrame], /) -> pl.LazyFrame:
        return pl.concat(relations)
