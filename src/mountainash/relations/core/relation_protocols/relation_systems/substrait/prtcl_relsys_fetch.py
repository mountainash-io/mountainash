"""Protocol for Substrait FetchRel — offset/limit row retrieval."""

from __future__ import annotations

from typing import Any, Optional, Protocol


class SubstraitFetchRelationSystemProtocol(Protocol):
    """Contract for fetching a subset of rows from a relation."""

    def fetch(self, relation: Any, offset: int, count: Optional[int], /) -> Any: ...

    def fetch_from_end(self, relation: Any, count: int, /) -> Any: ...
