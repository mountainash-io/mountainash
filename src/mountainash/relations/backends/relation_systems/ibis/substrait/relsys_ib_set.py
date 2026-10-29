"""Ibis implementation of Substrait SetRel."""

from __future__ import annotations

from functools import reduce
from typing import Any

import ibis.expr.datatypes as dt
import ibis.expr.types as ir

from mountainash.core.types import BackendCapabilityError
from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_SUBSTRAIT_REL
from mountainash.relations.core.relation_protocols.relation_systems.substrait import (
    SubstraitSetRelationSystemProtocol,
)


class SubstraitIbisSetRelationSystem(SubstraitSetRelationSystemProtocol[ir.Table]):
    """Set operations on Ibis table expressions."""

    def _prepare_timestamps(
        self, relations: list[Any], function_key: Any, timezone: str | None,
    ) -> list[Any]:
        """Resolve timestamps before Ibis checks set-operand schema equality."""
        if timezone is None and (len(relations) < 2 or self.dialect == "ibis-sqlite"):
            return relations
        schemas = [relation.schema() for relation in relations]
        targets = {}
        for name, dtype in schemas[0].items():
            if not isinstance(dtype, dt.Timestamp):
                continue
            types = [schema.get(name) for schema in schemas]
            if not all(isinstance(item, dt.Timestamp) for item in types):
                continue
            if any((item.timezone is None) != (dtype.timezone is None) for item in types):
                continue
            if timezone is None and any(item.timezone != dtype.timezone for item in types):
                continue
            if self.dialect == "ibis-sqlite":
                if timezone is not None and dtype.timezone is not None:
                    raise BackendCapabilityError(
                        "SQLite does not support concat timezone normalization.",
                        backend=self.BACKEND_NAME,
                        function_key=function_key,
                    )
                continue
            zone = timezone if dtype.timezone is not None and timezone is not None else dtype.timezone
            if zone == dtype.timezone and all(item == dtype for item in types):
                continue
            scales = [item.scale for item in types]
            if None in scales:
                # Native defaults differ; a mapper round-trip can narrow explicit ns.
                default = {"ibis-duckdb": 6, "ibis-polars": 9}.get(self.dialect)
                if default is None:
                    raise BackendCapabilityError(
                        "Timestamp default precision is not qualified for this dialect.",
                        backend=self.BACKEND_NAME,
                        function_key=function_key,
                    )
                scales = [default if scale is None else scale for scale in scales]
            targets[name] = dt.Timestamp(
                timezone=zone,
                scale=max(scales),
                nullable=any(item.nullable for item in types),
            )
        if not targets:
            return relations
        result = []
        for relation, schema in zip(relations, schemas):
            casts = {
                name: relation[name].cast(target)
                for name, target in targets.items() if schema[name] != target
            }
            result.append(relation.mutate(**casts) if casts else relation)
        return result

    def union_all(
        self, relations: list[Any], /, *, timezone: str | None = None,
    ) -> ir.Table:
        if not relations:
            raise ValueError("union_all requires at least one relation.")
        prepared = self._prepare_timestamps(relations, RKEY_SUBSTRAIT_REL.UNION_ALL, timezone)
        return reduce(lambda a, b: a.union(b), prepared)

    def union_distinct(
        self, relations: list[Any], /, *, timezone: str | None = None,
    ) -> ir.Table:
        if not relations:
            raise ValueError("union_distinct requires at least one relation.")
        prepared = self._prepare_timestamps(relations, RKEY_SUBSTRAIT_REL.UNION_DISTINCT, timezone)
        return reduce(lambda a, b: a.union(b, distinct=True), prepared)
