"""Narwhals implementation of Substrait FilterRel."""

from __future__ import annotations

from typing import Any

import narwhals as nw

from mountainash.relations.core.relation_protocols.relation_systems.substrait import (
    SubstraitFilterRelationSystemProtocol,
)


class SubstraitNarwhalsFilterRelationSystem(
    SubstraitFilterRelationSystemProtocol[nw.DataFrame | nw.LazyFrame, nw.Expr]
):
    """Row filtering on Narwhals DataFrames."""

    def filter(self, relation: Any, predicate: Any, /) -> Any:
        return relation.filter(predicate)
