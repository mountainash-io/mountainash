"""Projection operations builder for the Relation API."""

from __future__ import annotations

from typing import Any

from mountainash.core.constants import ProjectOperation
from mountainash.relations.core.relation_nodes import ProjectRelNode
from mountainash.relations.core.relation_protocols.api_builders import (
    RelationProjectionBuilderProtocol,
)

from .rel_api_builder_base import BaseRelationAPIBuilder


class RelationProjectionBuilder(BaseRelationAPIBuilder, RelationProjectionBuilderProtocol):
    """Projection operations: select, with_columns, drop, rename."""

    def select(self, *columns: Any) -> Any:
        return self._build(
            ProjectRelNode(
                input=self._node,
                expressions=list(columns),
                operation=ProjectOperation.SELECT,
            )
        )

    def with_columns(self, *expressions: Any) -> Any:
        return self._build(
            ProjectRelNode(
                input=self._node,
                expressions=list(expressions),
                operation=ProjectOperation.WITH_COLUMNS,
            )
        )

    def drop(self, *columns: Any) -> Any:
        return self._build(
            ProjectRelNode(
                input=self._node,
                expressions=list(columns),
                operation=ProjectOperation.DROP,
            )
        )

    def rename(self, mapping: dict[str, str]) -> Any:
        return self._build(
            ProjectRelNode(
                input=self._node,
                expressions=[],
                operation=ProjectOperation.RENAME,
                rename_mapping=mapping,
            )
        )
