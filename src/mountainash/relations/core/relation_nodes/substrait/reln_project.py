"""Project relation node for column selection and transformation.

Corresponds to Substrait's ProjectRel message.
"""

from __future__ import annotations
from typing import Any, Optional

from mountainash.core.constants import ProjectOperation

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

    input: RelationNode
    expressions: list[Any]
    operation: ProjectOperation
    rename_mapping: Optional[dict[str, str]] = None

    def accept(self, visitor: Any) -> Any:
        """Accept a visitor for double-dispatch."""
        return visitor.visit_project_rel(self)
