"""Base for Relation with compilation machinery."""

from __future__ import annotations

from typing import Any, Callable

from mountainash.core.constants import CONST_BACKEND
from mountainash.core.backend_detection import identify_backend
from mountainash.expressions.core.expression_system.expsys_base import (
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
        result, _visitor = self._compile_and_execute_with_visitor()
        return result

    def _compile_and_execute_with_visitor(
        self, backend: "str | None" = None
    ) -> "tuple[Any, UnifiedRelationVisitor]":
        """Compile the relational AST and return ``(result, visitor)``.

        Factored out of :meth:`_compile_and_execute` (whose existing callers
        are unaffected -- it now delegates here and discards the visitor) so
        terminals needing post-compile visitor state -- e.g.
        ``Relation.collect_with_drift()``'s ``visitor.drift_reports`` -- can
        retrieve it without a second compilation pass.

        Args:
            backend: Optional explicit backend name (``"polars"``, ``"ibis"``,
                ...), overriding auto-detection from the plan's leaf
                ``ReadRelNode``. ``None`` (default) preserves the existing
                auto-detect behaviour.
        """
        node = self._apply_optimisations(self._node)
        if backend is not None:
            try:
                resolved_backend = CONST_BACKEND(backend.lower())
            except ValueError:
                raise ValueError(f"unknown backend: {backend!r}")
        else:
            resolved_backend = self._detect_backend_from(node)
        dialect: str | None = None
        leaf = self._find_leaf_read_node(node)
        if leaf is not None:
            from mountainash.core.backend_detection import identify_backend_identity

            dialect = identify_backend_identity(leaf.dataframe).dialect
        relation_system_cls = get_relation_system(resolved_backend)
        relation_system = relation_system_cls(dialect=dialect)
        expression_system_cls = get_expression_system(resolved_backend)
        expression_system = expression_system_cls(dialect=dialect)
        expr_visitor = UnifiedExpressionVisitor(expression_system)
        visitor = UnifiedRelationVisitor(relation_system, expr_visitor)
        return visitor.visit(node), visitor

    def _apply_optimisations(self, node: RelationNode) -> RelationNode:
        """Apply registered optimisation passes if the tree contains relevant nodes."""
        from .optimisation_registry import get_registered_node_types, get_passes

        registered_types = get_registered_node_types()
        if not registered_types:
            return node
        if not self._contains_registered_node(node, registered_types):
            return node

        passes = get_passes()
        for node_type, transform_fn in passes:
            node = self._walk_and_push(node, transform_fn, node_type)
        return node

    def _contains_registered_node(
        self, node: RelationNode, registered_types: set[type]
    ) -> bool:
        """Check if the tree contains any node of a registered type."""
        if isinstance(node, tuple(registered_types)):
            return True
        return any(
            self._contains_registered_node(child, registered_types)
            for child in node.children()
        )

    def _walk_and_push(
        self, node: RelationNode, transform_fn: Callable[[Any], Any], target_type: type | None = None,
    ) -> RelationNode:
        """Bottom-up walk: reconstruct frozen nodes with rewritten children, then transform."""
        from ..relation_nodes.substrait.reln_filter import FilterRelNode
        from ..relation_nodes.substrait.reln_project import ProjectRelNode
        from ..relation_nodes.substrait.reln_fetch import FetchRelNode

        if isinstance(node, (ReadRelNode, SourceRelNode, RefRelNode)):
            return node
        if not node.children():
            return node

        rebuilt: RelationNode
        if isinstance(node, JoinRelNode):
            new_left = self._walk_and_push(node.left, transform_fn, target_type)
            new_right = self._walk_and_push(node.right, transform_fn, target_type)
            if new_left is node.left and new_right is node.right:
                rebuilt = node
            else:
                rebuilt = node.model_copy(update={"left": new_left, "right": new_right})
        elif isinstance(node, SetRelNode):
            new_inputs = [self._walk_and_push(inp, transform_fn, target_type) for inp in node.inputs]
            if all(n is o for n, o in zip(new_inputs, node.inputs)):
                rebuilt = node
            else:
                rebuilt = node.model_copy(update={"inputs": new_inputs})
        elif hasattr(node, "input"):
            new_input = self._walk_and_push(node.input, transform_fn, target_type)
            if new_input is node.input:
                rebuilt = node
            else:
                rebuilt = node.model_copy(update={"input": new_input})
        else:
            rebuilt = node

        # Apply transform to matching node type or legacy Filter/Project/Fetch types
        if target_type is not None and isinstance(rebuilt, target_type):
            return transform_fn(rebuilt)
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
        """Recursively find a ReadRelNode in the plan tree.

        Single-input nodes (the overwhelming majority) keep byte-identical
        behaviour: recurse into the one child, propagate whatever it raises
        or returns unmodified -- there is no sibling to reconcile against.
        A genuinely multi-input node (JoinRelNode/SetRelNode) walks EVERY
        child, so a RefRelNode in any position is detected before any node
        visiting begins (item 91); a leaf-less/unrecognized child (e.g.
        ResourceReadRelNode) is exactly as uninformative here as it always
        silently was for children[1:] under the old children[0]-only walk,
        and never aborts detection when another child DOES resolve.
        """
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
        children = node.children()
        if not children:
            raise ValueError(
                f"Cannot find ReadRelNode in plan tree from {type(node).__name__}"
            )
        if len(children) == 1:
            return RelationBase._find_leaf_read_node(children[0])
        result = None
        for child in children:
            try:
                found = RelationBase._find_leaf_read_node(child)
            except ValueError:
                continue  # RelationDAGRequired still propagates, uncaught
            if result is None:
                result = found
        return result

    @staticmethod
    def _find_leaf_backend(node: RelationNode) -> CONST_BACKEND | None:
        """Recursively find the first node with _leaf_backend set.

        Same single-input-unchanged / multi-input-exhaustive split as
        _find_leaf_read_node above; no raise semantics here at all, so the
        multi-input case is a simple short-circuit on first non-None.
        """
        if node._leaf_backend is not None:
            return node._leaf_backend
        if isinstance(node, (ReadRelNode, SourceRelNode)):
            return None
        if isinstance(node, RefRelNode):
            return None
        children = node.children()
        if not children:
            return None
        if len(children) == 1:
            return RelationBase._find_leaf_backend(children[0])
        for child in children:
            found = RelationBase._find_leaf_backend(child)
            if found is not None:
                return found
        return None
