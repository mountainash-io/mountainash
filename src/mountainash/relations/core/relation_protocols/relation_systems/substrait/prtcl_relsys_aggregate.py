"""Protocol for Substrait AggregateRel — grouping and aggregation."""

from __future__ import annotations

from typing import Any, Protocol


class SubstraitAggregateRelationSystemProtocol(Protocol):
    """Contract for aggregation operations on relations."""

    def aggregate(self, relation: Any, keys: list[Any], measures: list[Any], /) -> Any: ...

    def distinct(self, relation: Any, columns: list[Any], /) -> Any: ...
