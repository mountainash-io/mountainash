"""Protocol for Substrait SortRel — ordering rows by sort fields."""

from __future__ import annotations

from typing import Any, Protocol

from mountainash.core.constants import SortField


class SubstraitSortRelationSystemProtocol(Protocol):
    """Contract for sorting a relation by one or more fields."""

    def sort(self, relation: Any, sort_fields: list[SortField], /) -> Any: ...
