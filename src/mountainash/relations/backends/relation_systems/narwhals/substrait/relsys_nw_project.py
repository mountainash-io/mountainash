"""Narwhals implementation of Substrait ProjectRel."""

from __future__ import annotations

from typing import Any

from mountainash.relations.core.relation_protocols.relation_systems.substrait import (
    SubstraitProjectRelationSystemProtocol,
)


class SubstraitNarwhalsProjectRelationSystem(SubstraitProjectRelationSystemProtocol):
    """Projection operations on Narwhals DataFrames."""

    def project_select(self, relation: Any, columns: list[Any], /) -> Any:
        return relation.select(columns)

    def project_with_columns(self, relation: Any, expressions: list[Any], /) -> Any:
        return relation.with_columns(expressions)

    def project_drop(self, relation: Any, columns: list[Any], /) -> Any:
        return relation.drop(columns)

    def project_rename(self, relation: Any, mapping: dict[str, str], /) -> Any:
        return relation.rename(mapping)
