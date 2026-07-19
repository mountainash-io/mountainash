"""Ibis implementation of Substrait FetchRel."""

from __future__ import annotations

from typing import Optional

import ibis.expr.types as ir

from mountainash.relations.core.relation_protocols.relation_systems.substrait import (
    SubstraitFetchRelationSystemProtocol,
)


class SubstraitIbisFetchRelationSystem(SubstraitFetchRelationSystemProtocol[ir.Table]):
    """Offset/limit row retrieval on Ibis table expressions."""

    def fetch(
        self, relation: ir.Table, offset: int, count: Optional[int], /
    ) -> ir.Table:
        if count is not None:
            return relation.limit(count, offset=offset)
        # Ibis has no direct "skip N rows with no limit".
        # Use a very large limit as a practical workaround.
        if offset > 0:
            return relation.limit(None, offset=offset)
        return relation
