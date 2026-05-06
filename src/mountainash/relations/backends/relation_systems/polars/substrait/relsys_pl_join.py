"""Polars implementation of Substrait JoinRel."""

from __future__ import annotations

from typing import Any, Optional

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


class SubstraitPolarsJoinRelationSystem(SubstraitJoinRelationSystemProtocol):
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
        return left.join(
            right,
            on=on,
            left_on=left_on,
            right_on=right_on,
            how=how,
            suffix=suffix,
        )

    def join_asof(
        self,
        left: pl.LazyFrame,
        right: pl.LazyFrame,
        *,
        on: str,
        by: Optional[list[str]],
        strategy: str,
        tolerance: Any,
    ) -> pl.LazyFrame:
        return left.join_asof(
            right,
            on=on,
            by=by if by else None,
            strategy=strategy,
            tolerance=tolerance,
        )
