"""Protocol for Substrait SetRel — set operations on relations."""

from __future__ import annotations

from typing import Any, Protocol


class SubstraitSetRelationSystemProtocol(Protocol):
    """Contract for set operations (union, etc.) on relations."""

    def union_all(self, relations: list[Any], /) -> Any: ...
