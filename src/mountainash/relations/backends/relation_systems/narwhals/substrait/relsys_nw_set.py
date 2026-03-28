"""Narwhals implementation of Substrait SetRel."""

from __future__ import annotations

from typing import Any

import narwhals as nw


class SubstraitNarwhalsSetRelationSystem:
    """Set operations on Narwhals DataFrames."""

    def union_all(self, relations: list[Any], /) -> Any:
        return nw.concat(relations)
