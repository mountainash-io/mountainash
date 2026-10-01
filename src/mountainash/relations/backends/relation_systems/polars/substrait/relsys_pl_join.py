"""Polars implementation of Substrait JoinRel."""

from __future__ import annotations

from typing import Optional

import polars as pl

from mountainash.core.constants import JoinType
from mountainash.relations.core.relation_protocols.relation_systems.substrait import (
    SubstraitJoinRelationSystemProtocol,
)

# Substrait/mountainash JoinType → Polars ``how`` parameter.
# Polars uses "full" where Substrait says "outer".
_JOIN_TYPE_MAP: dict[JoinType, str] = {
    JoinType.INNER: "inner",
    JoinType.LEFT: "left",
    JoinType.RIGHT: "right",
    JoinType.OUTER: "full",
    JoinType.SEMI: "semi",
    JoinType.ANTI: "anti",
    JoinType.CROSS: "cross",
}


class SubstraitPolarsJoinRelationSystem(SubstraitJoinRelationSystemProtocol[pl.LazyFrame]):
    """Join operations on Polars LazyFrames."""

    def join(
        self,
        left: pl.LazyFrame,
        right: pl.LazyFrame,
        *,
        join_type: JoinType,
        on: Optional[list[str]],
        left_on: Optional[list[str]],
        right_on: Optional[list[str]],
        suffix: str,
    ) -> pl.LazyFrame:
        how = _JOIN_TYPE_MAP.get(join_type)
        if how is None:
            raise ValueError(
                f"Unsupported join type for Polars: {join_type!r}. "
                f"Supported: {list(_JOIN_TYPE_MAP.keys())}"
            )
        # Keyed joins arrive from visit_join as disjoint ``left_on``/``right_on``
        # names (see join_layout); keep both key columns -- visit_join owns any
        # key merging. ``on=`` (semi/anti and direct protocol callers) keeps
        # Polars' native single-key output.
        return left.join(
            right,
            on=on,
            left_on=left_on,
            right_on=right_on,
            how=how,
            suffix=suffix,
            coalesce=False if on is None else None,
        )
