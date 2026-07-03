"""Projection operations builder for the Relation API."""

from __future__ import annotations

from typing import Any

from mountainash.relations.core.relation_nodes import ProjectRelNode
from mountainash.relations.core.relation_system.relation_keys.enums import (
    RKEY_SUBSTRAIT_REL,
)
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
                operation=RKEY_SUBSTRAIT_REL.PROJECT_SELECT,
            )
        )

    def with_columns(self, *expressions: Any) -> Any:
        return self._build(
            ProjectRelNode(
                input=self._node,
                expressions=list(expressions),
                operation=RKEY_SUBSTRAIT_REL.PROJECT_WITH_COLUMNS,
            )
        )

    def drop(self, *columns: Any) -> Any:
        return self._build(
            ProjectRelNode(
                input=self._node,
                expressions=list(columns),
                operation=RKEY_SUBSTRAIT_REL.PROJECT_DROP,
            )
        )

    def rename(self, mapping: dict[str, str]) -> Any:
        return self._build(
            ProjectRelNode(
                input=self._node,
                expressions=[],
                operation=RKEY_SUBSTRAIT_REL.PROJECT_RENAME,
                rename_mapping=mapping,
            )
        )
