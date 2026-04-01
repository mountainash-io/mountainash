"""Narwhals implementation of Substrait FetchRel."""

from __future__ import annotations

from typing import Any, Optional



class SubstraitNarwhalsFetchRelationSystem:
    """Offset/limit row retrieval on Narwhals DataFrames."""

    def fetch(self, relation: Any, offset: int, count: Optional[int], /) -> Any:
        if offset == 0:
            if count is None:
                return relation
            return relation.head(count)

        # Narwhals lacks a direct .slice() method.
        # Use gather_every(n=1, offset=offset) to skip rows, then .head(count).
        sliced = relation.gather_every(n=1, offset=offset)
        if count is None:
            return sliced
        return sliced.head(count)

    def fetch_from_end(self, relation: Any, count: int, /) -> Any:
        return relation.tail(count)
