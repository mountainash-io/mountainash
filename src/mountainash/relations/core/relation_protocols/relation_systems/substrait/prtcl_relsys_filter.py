"""Protocol for Substrait FilterRel — row filtering by predicate."""

from __future__ import annotations

from typing import Protocol

from mountainash.core.types import ExpressionT, RelationT


class SubstraitFilterRelationSystemProtocol(Protocol[RelationT, ExpressionT]):
    """Contract for filtering rows from a relation."""

    def filter(self, relation: RelationT, predicate: ExpressionT, /) -> RelationT: ...
