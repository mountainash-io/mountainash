"""Narwhals implementation of Substrait AggregateRel."""

from __future__ import annotations

from typing import Any

import narwhals as nw

from mountainash.relations.core.relation_protocols.relation_systems.substrait import (
    SubstraitAggregateRelationSystemProtocol,
)


class SubstraitNarwhalsAggregateRelationSystem(
    SubstraitAggregateRelationSystemProtocol[nw.DataFrame | nw.LazyFrame, nw.Expr]
):
    """Aggregation operations on Narwhals DataFrames."""

    @staticmethod
    def _typed_null_columns(relation: Any, keys: list[Any]) -> Any:
        """Give Null-typed PyArrow measure columns a Float64 type.

        PyArrow has no stddev/variance kernel for a Null-typed (all-null)
        column, while every other Narwhals backend aggregates it to null.
        Grouping keys keep their type.
        """
        if getattr(relation, "implementation", None) is not nw.Implementation.PYARROW:
            return relation
        import pyarrow as pa

        schema = relation.to_native().schema
        null_columns = [
            name for name in relation.columns
            if name not in keys and pa.types.is_null(schema.field(name).type)
        ]
        if not null_columns:
            return relation
        return relation.with_columns(nw.col(*null_columns).cast(nw.Float64))

    def aggregate(self, relation: Any, keys: list[Any], measures: list[Any], /) -> Any:
        relation = self._typed_null_columns(relation, keys)
        if not keys:
            # Global aggregate (no group-by keys): use select() to get a
            # single-row scalar result.  group_by([]) is not portable across
            # Narwhals-backed libraries.
            return relation.select(measures)
        return relation.group_by(keys).agg(measures)

    def distinct(self, relation: Any, columns: list[Any], /) -> Any:
        if columns:
            return relation.unique(subset=columns)
        return relation.unique()
