"""Narwhals implementation of Substrait SetRel."""

from __future__ import annotations

from typing import Any

import narwhals as nw

from mountainash.relations.core.relation_protocols.relation_systems.substrait import (
    SubstraitSetRelationSystemProtocol,
)


def _prepare_timestamps(relations: list[Any], timezone: str | None) -> list[Any]:
    """Reconcile timestamps entirely through Narwhals' native expressions."""
    if not relations or (len(relations) == 1 and timezone is None):
        return relations
    schemas = [relation.collect_schema() for relation in relations]
    targets = {}
    precision = {"s": 0, "ms": 3, "us": 6, "ns": 9}
    for name, dtype in schemas[0].items():
        if not isinstance(dtype, nw.Datetime):
            continue
        types = [schema.get(name) for schema in schemas]
        if not all(isinstance(item, nw.Datetime) for item in types):
            continue
        if any((item.time_zone is None) != (dtype.time_zone is None) for item in types):
            continue
        if timezone is None and any(item.time_zone != dtype.time_zone for item in types):
            continue
        zone = timezone if dtype.time_zone is not None and timezone is not None else dtype.time_zone
        unit = max((item.time_unit for item in types), key=precision.__getitem__)
        target = nw.Datetime(unit, zone)
        if any(item != target for item in types):
            targets[name] = target
    if not targets:
        return relations
    result = []
    for relation, schema in zip(relations, schemas):
        casts = []
        for name, target in targets.items():
            source = schema[name]
            if source == target:
                continue
            expression = nw.col(name)
            if source.time_zone != target.time_zone:
                expression = expression.dt.convert_time_zone(target.time_zone)
            if source.time_unit != target.time_unit:
                expression = expression.cast(target)
            casts.append(expression)
        result.append(relation.with_columns(casts) if casts else relation)
    return result


class SubstraitNarwhalsSetRelationSystem(
    SubstraitSetRelationSystemProtocol[nw.DataFrame | nw.LazyFrame]
):
    """Set operations on Narwhals DataFrames."""

    def union_all(
        self, relations: list[Any], /, *, timezone: str | None = None,
    ) -> Any:
        return nw.concat(_prepare_timestamps(relations, timezone))

    def union_distinct(
        self, relations: list[Any], /, *, timezone: str | None = None,
    ) -> Any:
        return nw.concat(_prepare_timestamps(relations, timezone)).unique()
