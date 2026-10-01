"""Ibis implementation of Substrait JoinRel."""

from __future__ import annotations

from typing import Optional

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


class SubstraitIbisJoinRelationSystem(SubstraitJoinRelationSystemProtocol[ir.Table]):
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

        # Keyed joins arrive with disjoint names (see join_layout), so Ibis keeps
        # both key columns; visit_join owns any key merging.
        rname = "{name}" + suffix if suffix else "{name}_right"
        return left.join(right, predicates=predicates, how=how, lname="", rname=rname)
