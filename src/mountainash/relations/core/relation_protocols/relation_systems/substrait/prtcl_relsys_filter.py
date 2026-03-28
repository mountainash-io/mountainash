"""Protocol for Substrait FilterRel — row filtering by predicate."""

from __future__ import annotations

from typing import Any, Protocol


class SubstraitFilterRelationSystemProtocol(Protocol):
    """Contract for filtering rows from a relation."""

    def filter(self, relation: Any, predicate: Any, /) -> Any: ...
