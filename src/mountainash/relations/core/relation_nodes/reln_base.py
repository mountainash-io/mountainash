"""Base class for relational AST nodes.

This module defines the abstract base class that all relational nodes
inherit from. These nodes form a logical query plan tree aligned with
Substrait's relational algebra.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, ClassVar, Optional

from pydantic import BaseModel, ConfigDict

from mountainash.core.constants import CONST_BACKEND


class RelationNode(BaseModel, ABC):
    """Base class for all relational AST nodes.

    All relation nodes inherit from this class. Nodes form a logical plan
    tree that can be:
    1. Built by user code via the relation API
    2. Compiled to backend-native operations via visitors
    3. Serialized to Substrait protobuf for interoperability

    Node types align with Substrait's relational model:
    - ReadRelNode: Data source scan
    - ProjectRelNode: Column selection/transformation
    - FilterRelNode: Row filtering
    - SortRelNode: Ordering
    - FetchRelNode: Limit/offset
    - JoinRelNode: Joins
    - AggregateRelNode: Group-by aggregation
    - SetRelNode: Union/intersect/except
    """

    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True,
    )

    _leaf_backend: ClassVar[Optional[CONST_BACKEND]] = None

    def children(self) -> tuple[Any, ...]:
        """Return structural child relation nodes for tree traversal."""
        found: list[Any] = []
        for attr in ("input", "left", "right", "inputs"):
            child = getattr(self, attr, None)
            if child is None:
                continue
            if isinstance(child, list):
                found.extend(child)
            else:
                found.append(child)
        return tuple(found)

    @abstractmethod
    def accept(self, visitor: Any) -> Any:
        """Accept a visitor for double-dispatch pattern.

        Args:
            visitor: The visitor instance

        Returns:
            The result from the visitor's visit method
        """
        ...
