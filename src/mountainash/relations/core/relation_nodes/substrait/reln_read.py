"""Read relation node for data source scans.

Corresponds to Substrait's ReadRel message.
"""

from __future__ import annotations
from typing import Any

from ..reln_base import RelationNode


class ReadRelNode(RelationNode):
    """A scan of a data source (DataFrame, table, etc.).

    Represents the leaf node of a relational plan tree.
    Corresponds to Substrait's ReadRel.

    Attributes:
        dataframe: The source data object (Polars DataFrame, Ibis table, etc.)
    """

    dataframe: Any

    def accept(self, visitor: Any) -> Any:
        """Accept a visitor for double-dispatch."""
        return visitor.visit_read_rel(self)
