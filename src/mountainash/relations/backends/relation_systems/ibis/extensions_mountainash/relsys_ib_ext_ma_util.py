"""Ibis implementation of Mountainash extension relation operations."""

from __future__ import annotations

from typing import Any, Optional

import ibis
import ibis.expr.types as ir

from mountainash.relations.core.relation_protocols.relation_systems.extensions_mountainash import (
    MountainashExtensionRelationSystemProtocol,
)


class MountainashIbisExtensionRelationSystem(MountainashExtensionRelationSystemProtocol):
    """Mountainash-specific relation operations for the Ibis backend."""

    def drop_nulls(self, relation: ir.Table, /, *, subset: Optional[list[str]] = None) -> ir.Table:
        return relation.dropna(subset=subset)

    def drop_nans(
        self, relation: ir.Table, /, *, subset: Optional[list[str]] = None
    ) -> ir.Table:
        if subset is None:
            schema = relation.schema()
            subset = [
                name for name, dtype in schema.items()
                if dtype.is_floating()
            ]
        if not subset:
            return relation
        import functools
        import operator
        predicates = [~relation[c].isnan() for c in subset]
        combined = functools.reduce(operator.and_, predicates)
        return relation.filter(combined)

    def with_row_index(self, relation: ir.Table, /, *, name: str = "index") -> ir.Table:
        return relation.mutate(**{name: ibis.row_number()})

    def explode(self, relation: ir.Table, /, *, columns: list[str]) -> ir.Table:
        result = relation
        for col in columns:
            result = result.unnest(col)
        return result

    def sample(
        self, relation: ir.Table, /, *, n: Optional[int] = None, fraction: Optional[float] = None
    ) -> ir.Table:
        if fraction is not None:
            return relation.sample(fraction)
        if n is not None:
            total = relation.count().execute()
            frac = min(n / total, 1.0) if total > 0 else 1.0
            return relation.sample(frac)
        raise ValueError("Either n or fraction must be specified for sample().")

    def unpivot(
        self,
        relation: ir.Table,
        /,
        *,
        on: list[str],
        index: Optional[list[str]] = None,
        variable_name: str = "variable",
        value_name: str = "value",
    ) -> ir.Table:
        return relation.unpivot(
            on=on,
            index=index if index is not None else [],
            variable_name=variable_name,
            value_name=value_name,
        )

    def pivot(
        self,
        relation: ir.Table,
        /,
        *,
        on: str,
        index: Optional[list[str]] = None,
        values: Optional[str] = None,
        aggregate_function: str = "first",
    ) -> ir.Table:
        kwargs: dict[str, Any] = {
            "on": on,
            "names_from": on,
            "values_agg": aggregate_function,
        }
        if index is not None:
            kwargs["index"] = index
        if values is not None:
            kwargs["values_from"] = values
        return relation.pivot_wider(**kwargs)

    def top_k(
        self, relation: ir.Table, /, *, k: int, by: str, descending: bool = True
    ) -> ir.Table:
        order_key = ibis.desc(by) if descending else by
        return relation.order_by(order_key).limit(k)
