"""Ibis implementation of Substrait SortRel."""

from __future__ import annotations

import ibis
import ibis.expr.types as ir

from mountainash.core.constants import SortField


class SubstraitIbisSortRelationSystem:
    """Sort / order-by on Ibis table expressions."""

    def sort(self, relation: ir.Table, sort_fields: list[SortField], /) -> ir.Table:
        keys = []
        for sf in sort_fields:
            key = ibis.desc(sf.column) if sf.descending else sf.column
            keys.append(key)
        return relation.order_by(keys)
