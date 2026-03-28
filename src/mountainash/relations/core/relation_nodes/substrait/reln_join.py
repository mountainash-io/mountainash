"""Join relation node for combining two relations.

Corresponds to Substrait's JoinRel message.
"""

from __future__ import annotations
from typing import Any, Optional

from mountainash.core.constants import ExecutionTarget, JoinType

from ..reln_base import RelationNode


class JoinRelNode(RelationNode):
    """Join two relations on specified keys.

    Corresponds to Substrait's JoinRel with extensions for
    asof joins and execution targeting.

    Attributes:
        left: The left relation node
        right: The right relation node
        join_type: The type of join (INNER, LEFT, etc.)
        on: Shared join key columns (when both sides use same name)
        left_on: Left-side join key columns
        right_on: Right-side join key columns
        suffix: Suffix for disambiguating duplicate column names
        strategy: Join strategy hint (e.g., for asof joins)
        tolerance: Tolerance for asof joins
        execute_on: Which side to execute the join on
    """

    left: RelationNode
    right: RelationNode
    join_type: JoinType
    on: Optional[list[str]] = None
    left_on: Optional[list[str]] = None
    right_on: Optional[list[str]] = None
    suffix: str = "_right"
    strategy: Optional[str] = None
    tolerance: Any = None
    execute_on: Optional[ExecutionTarget] = None

    def accept(self, visitor: Any) -> Any:
        """Accept a visitor for double-dispatch."""
        return visitor.visit_join_rel(self)
