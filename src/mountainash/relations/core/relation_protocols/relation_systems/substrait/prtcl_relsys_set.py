"""Protocol for Substrait SetRel — set operations on relations."""

from __future__ import annotations

from typing import Protocol

from mountainash.core.types import RelationT


class SubstraitSetRelationSystemProtocol(Protocol[RelationT]):
    """Contract for set operations (union, etc.) on relations."""

    def union_all(self, relations: list[RelationT], /) -> RelationT: ...
