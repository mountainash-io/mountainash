"""Ibis implementation of Substrait SetRel."""

from __future__ import annotations

from functools import reduce
from typing import Any

import ibis.expr.types as ir

from mountainash.relations.core.relation_protocols.relation_systems.substrait import (
    SubstraitSetRelationSystemProtocol,
)


class SubstraitIbisSetRelationSystem(SubstraitSetRelationSystemProtocol):
    """Set operations on Ibis table expressions."""

    def union_all(self, relations: list[Any], /) -> ir.Table:
        if not relations:
            raise ValueError("union_all requires at least one relation.")
        return reduce(lambda a, b: a.union(b), relations)
