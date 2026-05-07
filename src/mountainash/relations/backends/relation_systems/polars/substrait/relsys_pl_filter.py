"""Polars implementation of Substrait FilterRel."""

from __future__ import annotations

from typing import Any

import polars as pl

from mountainash.relations.core.relation_protocols.relation_systems.substrait import (
    SubstraitFilterRelationSystemProtocol,
)


class SubstraitPolarsFilterRelationSystem(SubstraitFilterRelationSystemProtocol):
    """Row filtering on Polars LazyFrames."""

    def filter(self, relation: pl.LazyFrame, predicate: Any, /) -> pl.LazyFrame:
        return relation.filter(predicate)
