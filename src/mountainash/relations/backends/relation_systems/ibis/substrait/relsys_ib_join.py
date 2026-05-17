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

        result = left.join(right, predicates=predicates, how=how, lname="", rname=suffix or "{name}_right")

        # Ibis keeps the right-side join key column in the output for non-inner
        # joins (named with the suffix, e.g. ``"_right"`` for shared key ``"id"``).
        # Inner joins deduplicate automatically; others do not.
        # We must drop the right-side duplicate key so the schema matches the
        # expectation of every other backend (single unified key column).
        if on is not None and how not in ("inner", "semi", "anti", "cross"):
            effective_suffix = suffix or "_right"
            cols_to_drop = []
            for key in on:
                candidate_suffixed = f"{key}{effective_suffix}"
                # When `rname=suffix` (not `rname="{name}_right"`), ibis names
                # the right key column exactly `suffix` (e.g. ``"_right"``).
                if effective_suffix in result.columns and effective_suffix != f"{key}{effective_suffix}":
                    cols_to_drop.append(effective_suffix)
                    break  # Only one ``_right`` column exists when a bare suffix is used.
                elif candidate_suffixed in result.columns:
                    cols_to_drop.append(candidate_suffixed)

            if how in ("right", "outer"):
                # For right and outer joins, either side's key can be NULL for
                # non-matching rows; coalesce left and right keys into a single
                # unified key column.
                import ibis

                for key in on:
                    candidate_suffixed = f"{key}{effective_suffix}"
                    bare_suffix = effective_suffix
                    right_col_name = (
                        bare_suffix
                        if (bare_suffix in result.columns and bare_suffix != candidate_suffixed)
                        else candidate_suffixed
                    )
                    if right_col_name in result.columns:
                        result = result.mutate(
                            **{key: ibis.coalesce(result[key], result[right_col_name])}
                        )

            if cols_to_drop:
                result = result.drop(*cols_to_drop)

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
