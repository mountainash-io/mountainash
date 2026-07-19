"""Protocol for Substrait FetchRel — offset/limit row retrieval."""

from __future__ import annotations

from typing import Optional, Protocol

from mountainash.core.types import RelationT


class SubstraitFetchRelationSystemProtocol(Protocol[RelationT]):
    """Contract for fetching a subset of rows from a relation."""

    def fetch(self, relation: RelationT, offset: int, count: Optional[int], /) -> RelationT: ...
