"""Ibis implementation of Substrait ProjectRel."""

from __future__ import annotations

from typing import Any

import ibis.expr.types as ir


class SubstraitIbisProjectRelationSystem:
    """Projection operations on Ibis table expressions."""

    def project_select(self, relation: ir.Table, columns: list[Any], /) -> ir.Table:
        return relation.select(columns)

    def project_with_columns(
        self, relation: ir.Table, expressions: list[Any], /
    ) -> ir.Table:
        return relation.mutate(expressions)

    def project_drop(self, relation: ir.Table, columns: list[Any], /) -> ir.Table:
        return relation.drop(*columns)

    def project_rename(
        self, relation: ir.Table, mapping: dict[str, str], /
    ) -> ir.Table:
        return relation.rename(mapping)
