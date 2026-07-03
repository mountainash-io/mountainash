"""Narwhals implementation of Substrait SetRel."""

from __future__ import annotations

from typing import Any

import narwhals as nw

from mountainash.relations.core.relation_protocols.relation_systems.substrait import (
    SubstraitSetRelationSystemProtocol,
)


class SubstraitNarwhalsSetRelationSystem(
    SubstraitSetRelationSystemProtocol[nw.DataFrame | nw.LazyFrame]
):
    """Set operations on Narwhals DataFrames."""

    def union_all(self, relations: list[Any], /) -> Any:
        return nw.concat(relations)

    def union_distinct(self, relations: list[Any], /) -> Any:
        return nw.concat(relations).unique()
