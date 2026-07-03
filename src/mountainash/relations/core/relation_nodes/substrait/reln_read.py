"""Read relation node for data source scans.

Corresponds to Substrait's ReadRel message.
"""

from __future__ import annotations
from enum import Enum
from typing import Any, ClassVar, Optional

from mountainash.relations.core.relation_system.relation_keys.enums import (
    RKEY_SUBSTRAIT_REL,
)

from ..reln_base import RelationNode


class ReadRelNode(RelationNode):
    """A scan of a data source (DataFrame, table, etc.).

    Represents the leaf node of a relational plan tree.
    Corresponds to Substrait's ReadRel.

    Attributes:
        dataframe: The source data object (Polars DataFrame, Ibis table, etc.)
    """

    _operation_key: ClassVar[Optional[Enum]] = RKEY_SUBSTRAIT_REL.READ

    dataframe: Any

    def accept(self, visitor: Any) -> Any:
        """Accept a visitor for double-dispatch."""
        return visitor.visit_read_rel(self)
