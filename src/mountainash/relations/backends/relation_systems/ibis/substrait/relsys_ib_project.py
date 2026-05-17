"""Ibis implementation of Substrait ProjectRel."""

from __future__ import annotations

from typing import Any

import ibis.expr.types as ir

from mountainash.relations.core.relation_protocols.relation_systems.substrait import (
    SubstraitProjectRelationSystemProtocol,
)


class SubstraitIbisProjectRelationSystem(SubstraitProjectRelationSystemProtocol):
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
        # Ibis rename() uses {new_name: old_name}; mountainash convention is {old_name: new_name}
        return relation.rename({v: k for k, v in mapping.items()})
