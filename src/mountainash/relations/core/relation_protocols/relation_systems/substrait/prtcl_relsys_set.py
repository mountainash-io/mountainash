"""Protocol for Substrait SetRel — set operations on relations."""

from __future__ import annotations

from typing import Protocol

from mountainash.core.types import RelationT


class SubstraitSetRelationSystemProtocol(Protocol[RelationT]):
    """Contract for set operations (union, etc.) on relations."""

    def union_all(self, relations: list[RelationT], /) -> RelationT: ...

    def union_distinct(self, relations: list[RelationT], /) -> RelationT: ...

    # --- Aspirational (Substrait SetOp domain; not yet wired) ---

    def union_multiset(self, relations: list[RelationT], /) -> RelationT: ...

    def minus_primary(self, relations: list[RelationT], /) -> RelationT: ...

    def minus_multiset(self, relations: list[RelationT], /) -> RelationT: ...

    def intersection_primary(self, relations: list[RelationT], /) -> RelationT: ...

    def intersection_multiset(self, relations: list[RelationT], /) -> RelationT: ...
