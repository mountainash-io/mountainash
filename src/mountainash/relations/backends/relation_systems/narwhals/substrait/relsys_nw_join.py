"""Narwhals implementation of Substrait JoinRel."""

from __future__ import annotations

from typing import Any, Optional

import narwhals as nw

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


class SubstraitNarwhalsJoinRelationSystem(
    SubstraitJoinRelationSystemProtocol[nw.DataFrame | nw.LazyFrame]
):
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
        # Narwhals has no ``coalesce`` option and pandas drops or keeps a key
        # depending on ``how``. Join on private copies of the keys so the real
        # keys survive as ordinary columns, then select the canonical
        # left-then-right order (which also drops the private copies).
        order: list[str] | None = None
        if left_on and right_on:
            order = list(left.columns) + list(right.columns)
            taken = set(order)
            la = _fresh_names("__ma_lk", len(left_on), taken)
            ra = _fresh_names("__ma_rk", len(right_on), taken)
            left = left.with_columns([nw.col(c).alias(a) for c, a in zip(left_on, la)])
            right = right.with_columns([nw.col(c).alias(a) for c, a in zip(right_on, ra)])
            left_on, right_on = la, ra

        # Narwhals has no RIGHT join: swap operands and use LEFT.
        if join_type == JoinType.RIGHT:
            result = right.join(
                left, on=on, left_on=right_on, right_on=left_on, how="left", suffix=suffix,
            )
        else:
            how = _JOIN_TYPE_MAP.get(join_type)
            if how is None:
                raise ValueError(
                    f"Unsupported join type for Narwhals: {join_type!r}. "
                    f"Supported: {list(_JOIN_TYPE_MAP.keys()) + [JoinType.RIGHT]}"
                )
            result = left.join(
                right, on=on, left_on=left_on, right_on=right_on, how=how, suffix=suffix,
            )
        return result.select(order) if order is not None else result


def _fresh_names(prefix: str, count: int, taken: set[str]) -> list[str]:
    """``count`` names starting with ``prefix`` that collide with nothing in ``taken``."""
    out: list[str] = []
    i = 0
    while len(out) < count:
        name = f"{prefix}_{i}"
        i += 1
        if name not in taken:
            taken.add(name)
            out.append(name)
    return out
