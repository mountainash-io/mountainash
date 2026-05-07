"""Ibis implementation of Substrait AggregateRel."""

from __future__ import annotations

from typing import Any

import ibis.expr.types as ir

from mountainash.relations.core.relation_protocols.relation_systems.substrait import (
    SubstraitAggregateRelationSystemProtocol,
)


class SubstraitIbisAggregateRelationSystem(SubstraitAggregateRelationSystemProtocol):
    """Grouping and aggregation on Ibis table expressions."""

    def aggregate(
        self, relation: ir.Table, keys: list[Any], measures: list[Any], /
    ) -> ir.Table:
        if not keys:
            return relation.aggregate(measures)
        return relation.group_by(keys).aggregate(measures)

    def distinct(self, relation: ir.Table, columns: list[Any], /) -> ir.Table:
        if columns:
            return relation.select(columns).distinct()
        return relation.distinct()
