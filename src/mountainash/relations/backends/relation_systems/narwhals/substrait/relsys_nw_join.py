"""Narwhals implementation of Substrait JoinRel."""

from __future__ import annotations

from typing import Any, Optional

from mountainash.core.constants import JoinType
from mountainash.relations.core.relation_protocols.relation_systems.substrait import (
    SubstraitJoinRelationSystemProtocol,
)

# Substrait/mountainash JoinType → Narwhals ``how`` parameter.
# Narwhals uses "full" where Substrait says "outer".
# Narwhals does not natively support RIGHT joins — we swap operands and use LEFT.
_JOIN_TYPE_MAP: dict[JoinType, str] = {
    JoinType.INNER: "inner",
    JoinType.LEFT: "left",
    JoinType.OUTER: "full",
    JoinType.SEMI: "semi",
    JoinType.ANTI: "anti",
    JoinType.CROSS: "cross",
}


class SubstraitNarwhalsJoinRelationSystem(SubstraitJoinRelationSystemProtocol):
    """Join operations on Narwhals DataFrames."""

    def join(
        self,
        left: Any,
        right: Any,
        *,
        join_type: JoinType,
        on: Optional[list[str]],
        left_on: Optional[list[str]],
        right_on: Optional[list[str]],
        suffix: str,
    ) -> Any:
        # Handle RIGHT join by swapping operands and using LEFT join.
        if join_type == JoinType.RIGHT:
            return right.join(
                left,
                on=on,
                left_on=right_on,
                right_on=left_on,
                how="left",
                suffix=suffix,
            )

        how = _JOIN_TYPE_MAP.get(join_type)
        if how is None:
            raise ValueError(
                f"Unsupported join type for Narwhals: {join_type!r}. "
                f"Supported: {list(_JOIN_TYPE_MAP.keys()) + [JoinType.RIGHT]}"
            )
        result = left.join(
            right,
            on=on,
            left_on=left_on,
            right_on=right_on,
            how=how,
            suffix=suffix,
        )

        # For outer (full) joins, Narwhals keeps both key columns when rows are
        # unmatched — e.g. ``id`` (left, NULL for right-only rows) and
        # ``id_right`` (right, NULL for left-only rows).  Coalesce them into a
        # single unified key column and drop the duplicate.
        if how == "full" and on is not None:
            import narwhals as nw

            effective_suffix = suffix or "_right"
            cols_to_drop = []
            select_exprs = []
            for key in on:
                right_key = f"{key}{effective_suffix}"
                if right_key in result.columns:
                    select_exprs.append(
                        nw.coalesce(nw.col(key), nw.col(right_key)).alias(key)
                    )
                    cols_to_drop.append(right_key)
            if select_exprs:
                result = result.with_columns(select_exprs).drop(cols_to_drop)

        return result

    def join_asof(
        self,
        left: Any,
        right: Any,
        *,
        on: str,
        by: Optional[list[str]],
        strategy: str,
        tolerance: Any,
    ) -> Any:
        return left.join_asof(
            right,
            on=on,
            by=by if by else None,
            strategy=strategy,
            tolerance=tolerance,
        )
