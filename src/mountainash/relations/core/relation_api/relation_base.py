"""Base for Relation with compilation machinery."""

from __future__ import annotations

from typing import Any

from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.expsys_base import (
    identify_backend,
    get_expression_system,
)
from mountainash.expressions.core.unified_visitor import UnifiedExpressionVisitor
from ..relation_nodes import RelationNode, ReadRelNode, JoinRelNode, SetRelNode, SourceRelNode
from ..relation_nodes.extensions_mountainash import RefRelNode
from ..relation_protocols.relsys_base import get_relation_system
from ..unified_visitor.relation_visitor import UnifiedRelationVisitor
from ...dag.errors import RelationDAGRequired


class RelationBase:
    """Base class providing compilation and backend detection machinery.

    Subclasses (Relation) add the fluent API methods that build AST nodes.
    """

    __slots__ = ("_node",)

    def __init__(self, node: RelationNode) -> None:
        self._node = node

    def _compile_and_execute(self) -> Any:
        """Compile the relational AST and execute via the detected backend."""
        backend = self._detect_backend()
        relation_system_cls = get_relation_system(backend)
        relation_system = relation_system_cls()
        expression_system_cls = get_expression_system(backend)
        expression_system = expression_system_cls()
        expr_visitor = UnifiedExpressionVisitor(expression_system)
        visitor = UnifiedRelationVisitor(relation_system, expr_visitor)
        return visitor.visit(self._node)

    def _detect_backend(self) -> CONST_BACKEND:
        """Walk the plan tree to find a ReadRelNode and identify its backend."""
        leaf = self._find_leaf_read_node(self._node)
        if leaf is not None:
            return identify_backend(leaf.dataframe)
        leaf_backend = self._find_leaf_backend(self._node)
        if leaf_backend is not None:
            return leaf_backend
        return CONST_BACKEND.POLARS

    @staticmethod
    def _find_leaf_read_node(node: RelationNode) -> ReadRelNode | None:
        """Recursively find the first ReadRelNode in the plan tree."""
        if isinstance(node, ReadRelNode):
            return node
        if isinstance(node, SourceRelNode):
            # SourceRelNode is a leaf with no backend — return None.
            return None
        if node._leaf_backend is not None:
            return None
        if isinstance(node, RefRelNode):
            raise RelationDAGRequired(
                f"Relation contains a RefRelNode ('{node.name}') and cannot be compiled "
                "standalone. Use RelationDAG.collect() to resolve named references."
            )
        if isinstance(node, JoinRelNode):
            return RelationBase._find_leaf_read_node(node.left)
        if isinstance(node, SetRelNode):
            return RelationBase._find_leaf_read_node(node.inputs[0])
        if hasattr(node, "input"):
            return RelationBase._find_leaf_read_node(node.input)
        raise ValueError(
            f"Cannot find ReadRelNode in plan tree from {type(node).__name__}"
        )

    @staticmethod
    def _find_leaf_backend(node: RelationNode) -> CONST_BACKEND | None:
        """Recursively find the first node with _leaf_backend set."""
        if node._leaf_backend is not None:
            return node._leaf_backend
        if isinstance(node, (ReadRelNode, SourceRelNode)):
            return None
        if isinstance(node, RefRelNode):
            return None
        if isinstance(node, JoinRelNode):
            return RelationBase._find_leaf_backend(node.left)
        if isinstance(node, SetRelNode):
            return RelationBase._find_leaf_backend(node.inputs[0])
        if hasattr(node, "input"):
            return RelationBase._find_leaf_backend(node.input)
        return None
