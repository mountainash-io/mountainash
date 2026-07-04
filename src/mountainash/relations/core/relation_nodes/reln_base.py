"""Base class for relational AST nodes.

This module defines the abstract base class that all relational nodes
inherit from. These nodes form a logical query plan tree aligned with
Substrait's relational algebra.
"""

from __future__ import annotations
from abc import ABC
from enum import Enum
from typing import Any, ClassVar, Optional

from pydantic import BaseModel, ConfigDict

from mountainash.core.constants import CONST_BACKEND


# Attribute names the base children() scan inspects for structural child
# relation nodes. Single source of truth — consumed by RelationNode.children(),
# dag.traversal.relation_children()'s fallback branch, and the exhaustiveness
# test in tests/relations/test_node_children_exhaustive.py.
RELATION_CHILD_ATTRS: tuple[str, ...] = ("input", "left", "right", "inputs")


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
    _operation_key: ClassVar[Optional[Enum]] = None

    @property
    def operation_key(self) -> Optional[Enum]:
        """The RKEY this node dispatches under, or None for node types that
        rely on a RelationVisitRegistry handler (third-party nodes)."""
        return type(self)._operation_key

    def children(self) -> tuple[Any, ...]:
        """Return structural child relation nodes for tree traversal."""
        found: list[Any] = []
        for attr in RELATION_CHILD_ATTRS:
            child = getattr(self, attr, None)
            if child is None:
                continue
            if isinstance(child, list):
                found.extend(child)
            else:
                found.append(child)
        return tuple(found)

    def accept(self, visitor: Any) -> Any:
        """Compatibility shim — dispatch is owned by visitor.visit() (spec §3.5).

        No longer participates in dispatch: visit() never falls back here.
        """
        return visitor.visit(self)
