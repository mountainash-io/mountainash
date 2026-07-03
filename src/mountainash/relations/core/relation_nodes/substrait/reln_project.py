"""Project relation node for column selection and transformation.

Corresponds to Substrait's ProjectRel message.
"""

from __future__ import annotations
from typing import Any, ClassVar, Optional

from mountainash.core.constants import ProjectOperation
from mountainash.relations.core.relation_system.relation_keys.enums import (
    RKEY_SUBSTRAIT_REL,
)

from ..reln_base import RelationNode


class ProjectRelNode(RelationNode):
    """Column selection, addition, dropping, or renaming.

    Corresponds to Substrait's ProjectRel. The operation field
    determines which variant of projection is applied.

    Attributes:
        input: The child relation node
        expressions: Columns or expressions to project
        operation: The type of projection (SELECT, WITH_COLUMNS, DROP, RENAME)
        rename_mapping: Column rename mapping (only for RENAME operation)
    """

    _PROJECT_KEY_MAP: ClassVar[dict] = {}  # populated below

    input: RelationNode
    expressions: list[Any]
    operation: ProjectOperation
    rename_mapping: Optional[dict[str, str]] = None

    @property
    def operation_key(self):
        return self._PROJECT_KEY_MAP[self.operation]

    def accept(self, visitor: Any) -> Any:
        """Accept a visitor for double-dispatch."""
        return visitor.visit_project_rel(self)


ProjectRelNode._PROJECT_KEY_MAP = {
    ProjectOperation.SELECT: RKEY_SUBSTRAIT_REL.PROJECT_SELECT,
    ProjectOperation.WITH_COLUMNS: RKEY_SUBSTRAIT_REL.PROJECT_WITH_COLUMNS,
    ProjectOperation.DROP: RKEY_SUBSTRAIT_REL.PROJECT_DROP,
    ProjectOperation.RENAME: RKEY_SUBSTRAIT_REL.PROJECT_RENAME,
}
