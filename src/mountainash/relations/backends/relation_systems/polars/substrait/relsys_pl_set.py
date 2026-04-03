"""Polars implementation of Substrait SetRel."""

from __future__ import annotations

import polars as pl


class SubstraitPolarsSetRelationSystem:
    """Set operations on Polars LazyFrames."""

    def union_all(self, relations: list[pl.LazyFrame], /) -> pl.LazyFrame:
        return pl.concat(relations)
