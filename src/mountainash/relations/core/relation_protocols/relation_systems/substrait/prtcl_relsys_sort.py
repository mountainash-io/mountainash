"""Protocol for Substrait SortRel — ordering rows by sort fields."""

from __future__ import annotations

from typing import Protocol

from mountainash.core.constants import SortField
from mountainash.core.types import RelationT


class SubstraitSortRelationSystemProtocol(Protocol[RelationT]):
    """Contract for sorting a relation by one or more fields."""

    def sort(self, relation: RelationT, sort_fields: list[SortField], /) -> RelationT: ...
