"""Ibis implementation of Substrait JoinRel."""

from __future__ import annotations

from typing import Any, Optional

import ibis.expr.types as ir

from mountainash.core.constants import JoinType
from mountainash.relations.core.relation_protocols.relation_systems.substrait import (
    SubstraitJoinRelationSystemProtocol,
)

# Mapping from mountainash JoinType to Ibis ``how`` parameter values.
_JOIN_TYPE_MAP: dict[JoinType, str] = {
    JoinType.INNER: "inner",
    JoinType.LEFT: "left",
    JoinType.RIGHT: "right",
    JoinType.OUTER: "outer",
    JoinType.SEMI: "semi",
    JoinType.ANTI: "anti",
    JoinType.CROSS: "cross",
}


class SubstraitIbisJoinRelationSystem(SubstraitJoinRelationSystemProtocol):
    """Join operations on Ibis table expressions."""

    def join(
        self,
        left: ir.Table,
        right: ir.Table,
        *,
        join_type: JoinType,
        on: Optional[list[str]],
        left_on: Optional[list[str]],
        right_on: Optional[list[str]],
        suffix: str,
    ) -> ir.Table:
        how = _JOIN_TYPE_MAP.get(join_type)
        if how is None:
            raise ValueError(
                f"Unsupported join type for Ibis: {join_type!r}. "
                f"Supported: {list(_JOIN_TYPE_MAP.keys())}"
            )

        # Build predicates.
        if on is not None:
            # Simple equi-join on shared column names.
            predicates = [left[col] == right[col] for col in on]
        elif left_on is not None and right_on is not None:
            predicates = [
                left[lc] == right[rc] for lc, rc in zip(left_on, right_on)
            ]
        else:
            # Cross join or no predicate.
            predicates = []

        rname = "{name}" + suffix if suffix else "{name}_right"
        result = left.join(right, predicates=predicates, how=how, lname="", rname=rname)

        # Ibis keeps the right-side join key as a separate column for non-inner
        # joins (e.g. ``id_right`` alongside ``id``).  Polars and Narwhals
        # deduplicate automatically; we do it here to match.
        if on is not None and how not in ("inner", "semi", "anti", "cross"):
            effective_suffix = suffix or "_right"
            right_keys = [f"{k}{effective_suffix}" for k in on]
            right_keys = [rk for rk in right_keys if rk in result.columns]

            if how in ("right", "outer"):
                import ibis
                for key, rk in zip(on, right_keys):
                    result = result.mutate(
                        **{key: ibis.coalesce(result[key], result[rk])}
                    )

            if right_keys:
                result = result.drop(*right_keys)

        return result

    def join_asof(
        self,
        left: ir.Table,
        right: ir.Table,
        *,
        on: str,
        by: Optional[list[str]],
        strategy: str,
        tolerance: Any,
    ) -> ir.Table:
        kwargs: dict[str, Any] = {"on": on}
        if by is not None:
            kwargs["by"] = by
        if tolerance is not None:
            kwargs["tolerance"] = tolerance
        return left.asof_join(right, **kwargs)
