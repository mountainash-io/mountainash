"""Ibis implementation of Substrait FilterRel."""

from __future__ import annotations

from typing import Any

import ibis.expr.types as ir

from mountainash.relations.core.relation_protocols.relation_systems.substrait import (
    SubstraitFilterRelationSystemProtocol,
)


class SubstraitIbisFilterRelationSystem(SubstraitFilterRelationSystemProtocol):
    """Row filtering on Ibis table expressions."""

    def filter(self, relation: ir.Table, predicate: Any, /) -> ir.Table:
        return relation.filter(predicate)
