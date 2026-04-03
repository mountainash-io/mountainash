"""Polars implementation of Substrait FilterRel."""

from __future__ import annotations

from typing import Any

import polars as pl


class SubstraitPolarsFilterRelationSystem:
    """Row filtering on Polars LazyFrames."""

    def filter(self, relation: pl.LazyFrame, predicate: Any, /) -> pl.LazyFrame:
        return relation.filter(predicate)
