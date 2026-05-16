"""Base for Relation with compilation machinery."""

from __future__ import annotations

from typing import Any, Callable

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
        node = self._apply_optimisations(self._node)
        backend = self._detect_backend_from(node)
        relation_system_cls = get_relation_system(backend)
        relation_system = relation_system_cls()
        expression_system_cls = get_expression_system(backend)
        expression_system = expression_system_cls()
        expr_visitor = UnifiedExpressionVisitor(expression_system)
        visitor = UnifiedRelationVisitor(relation_system, expr_visitor)
        return visitor.visit(node)

    def _apply_optimisations(self, node: RelationNode) -> RelationNode:
        """Apply registered optimisation passes if the tree contains relevant nodes."""
        from .optimisation_registry import get_registered_node_types, get_passes

        registered_types = get_registered_node_types()
        if not registered_types:
            return node
        if not self._contains_registered_node(node, registered_types):
            return node

        passes = get_passes()
        for _node_type, transform_fn in passes:
            node = self._walk_and_push(node, transform_fn)
        return node

    def _contains_registered_node(
        self, node: RelationNode, registered_types: set[type]
    ) -> bool:
        """Check if the tree contains any node of a registered type."""
        if isinstance(node, tuple(registered_types)):
            return True
        if isinstance(node, JoinRelNode):
            return (
                self._contains_registered_node(node.left, registered_types)
                or self._contains_registered_node(node.right, registered_types)
            )
        if isinstance(node, SetRelNode):
            return any(
                self._contains_registered_node(inp, registered_types)
                for inp in node.inputs
            )
        if hasattr(node, "input"):
            return self._contains_registered_node(node.input, registered_types)
        return False

    def _walk_and_push(
        self, node: RelationNode, transform_fn: Callable[[Any], Any]
    ) -> RelationNode:
        """Bottom-up walk: reconstruct frozen nodes with rewritten children, then transform."""
        from ..relation_nodes.substrait.reln_filter import FilterRelNode
        from ..relation_nodes.substrait.reln_project import ProjectRelNode
        from ..relation_nodes.substrait.reln_fetch import FetchRelNode

        if isinstance(node, (ReadRelNode, SourceRelNode, RefRelNode)):
            return node
        if not hasattr(node, "input") and not isinstance(node, (JoinRelNode, SetRelNode)):
            return node

        if isinstance(node, JoinRelNode):
            new_left = self._walk_and_push(node.left, transform_fn)
            new_right = self._walk_and_push(node.right, transform_fn)
            if new_left is node.left and new_right is node.right:
                rebuilt = node
            else:
                rebuilt = node.model_copy(update={"left": new_left, "right": new_right})
        elif isinstance(node, SetRelNode):
            new_inputs = [self._walk_and_push(inp, transform_fn) for inp in node.inputs]
            if all(n is o for n, o in zip(new_inputs, node.inputs)):
                rebuilt = node
            else:
                rebuilt = node.model_copy(update={"inputs": new_inputs})
        elif hasattr(node, "input"):
            new_input = self._walk_and_push(node.input, transform_fn)
            if new_input is node.input:
                rebuilt = node
            else:
                rebuilt = node.model_copy(update={"input": new_input})
        else:
            rebuilt = node

        if isinstance(rebuilt, (FilterRelNode, ProjectRelNode, FetchRelNode)):
            return transform_fn(rebuilt)
        return rebuilt

    def _detect_backend(self) -> CONST_BACKEND:
        """Walk the plan tree to find a ReadRelNode and identify its backend."""
        return self._detect_backend_from(self._node)

    def _detect_backend_from(self, node: RelationNode) -> CONST_BACKEND:
        """Detect backend from the given node tree."""
        leaf = self._find_leaf_read_node(node)
        if leaf is not None:
            return identify_backend(leaf.dataframe)
        leaf_backend = self._find_leaf_backend(node)
        if leaf_backend is not None:
            return leaf_backend
        return CONST_BACKEND.POLARS

    @staticmethod
    def _find_leaf_read_node(node: RelationNode) -> ReadRelNode | None:
        """Recursively find the first ReadRelNode in the plan tree."""
        if isinstance(node, ReadRelNode):
            return node
        if isinstance(node, SourceRelNode):
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
