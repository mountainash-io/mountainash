"""Ibis implementation of Substrait FilterRel."""

from __future__ import annotations

from typing import Any

import ibis.expr.types as ir


class SubstraitIbisFilterRelationSystem:
    """Row filtering on Ibis table expressions."""

    def filter(self, relation: ir.Table, predicate: Any, /) -> ir.Table:
        return relation.filter(predicate)
