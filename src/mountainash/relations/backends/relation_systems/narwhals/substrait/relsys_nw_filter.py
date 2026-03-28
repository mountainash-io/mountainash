"""Narwhals implementation of Substrait FilterRel."""

from __future__ import annotations

from typing import Any


class SubstraitNarwhalsFilterRelationSystem:
    """Row filtering on Narwhals DataFrames."""

    def filter(self, relation: Any, predicate: Any, /) -> Any:
        return relation.filter(predicate)
