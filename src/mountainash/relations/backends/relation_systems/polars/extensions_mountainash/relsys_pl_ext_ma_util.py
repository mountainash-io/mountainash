"""Polars implementation of Mountainash extension relation operations."""

from __future__ import annotations

from typing import Optional

import polars as pl

from mountainash.relations.core.relation_protocols.relation_systems.extensions_mountainash import (
    MountainashExtensionRelationSystemProtocol,
)


class MountainashPolarsExtensionRelationSystem(MountainashExtensionRelationSystemProtocol):
    """Mountainash-specific relation operations on Polars LazyFrames."""

    def drop_nulls(
        self, relation: pl.LazyFrame, /, *, subset: Optional[list[str]] = None
    ) -> pl.LazyFrame:
        if subset:
            return relation.drop_nulls(subset=subset)
        return relation.drop_nulls()

    def drop_nans(
        self, relation: pl.LazyFrame, /, *, subset: Optional[list[str]] = None
    ) -> pl.LazyFrame:
        if subset:
            return relation.drop_nans(subset=subset)
        return relation.drop_nans()

    def with_row_index(
        self, relation: pl.LazyFrame, /, *, name: str = "index"
    ) -> pl.LazyFrame:
        return relation.with_row_index(name=name)

    def explode(self, relation: pl.LazyFrame, /, *, columns: list[str]) -> pl.LazyFrame:
        return relation.explode(columns)

    def sample(
        self,
        relation: pl.LazyFrame,
        /,
        *,
        n: Optional[int] = None,
        fraction: Optional[float] = None,
    ) -> pl.LazyFrame:
        # LazyFrame does not support .sample() directly — collect, sample, re-lazy.
        return relation.collect().sample(n=n, fraction=fraction).lazy()

    def unpivot(
        self,
        relation: pl.LazyFrame,
        /,
        *,
        on: list[str],
        index: Optional[list[str]] = None,
        variable_name: str = "variable",
        value_name: str = "value",
    ) -> pl.LazyFrame:
        return relation.unpivot(
            on=on,
            index=index,
            variable_name=variable_name,
            value_name=value_name,
        )

    def pivot(
        self,
        relation: pl.LazyFrame,
        /,
        *,
        on: str,
        index: Optional[list[str]] = None,
        values: Optional[str] = None,
        aggregate_function: str = "first",
    ) -> pl.LazyFrame:
        # Pivot requires eager DataFrame — collect, pivot, re-lazy.
        return (
            relation.collect()
            .pivot(
                on=on,
                index=index,
                values=values,
                aggregate_function=aggregate_function,
            )
            .lazy()
        )

    def top_k(
        self, relation: pl.LazyFrame, /, *, k: int, by: str, descending: bool = True
    ) -> pl.LazyFrame:
        return relation.sort(by, descending=descending).head(k)
