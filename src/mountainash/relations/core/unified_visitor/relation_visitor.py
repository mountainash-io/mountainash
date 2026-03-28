"""Unified relation visitor for relational AST nodes.

Walks the relational AST and calls backend RelationSystem methods.
Composes with the expression visitor for compiling embedded expression ASTs.
"""

from __future__ import annotations
from typing import Any

from mountainash.core.constants import JoinType, ProjectOperation
from mountainash.expressions.core.expression_nodes import ExpressionNode

from ..relation_nodes import (
    RelationNode, ReadRelNode, ProjectRelNode, FilterRelNode,
    SortRelNode, FetchRelNode, JoinRelNode, AggregateRelNode,
    SetRelNode, ExtensionRelNode,
)


class UnifiedRelationVisitor:
    """Walks a relational AST and produces backend-native results.

    Attributes:
        backend: The relation system that executes backend-native operations.
        expr_visitor: The expression visitor for compiling expression AST nodes.
    """

    def __init__(self, relation_system: Any, expression_visitor: Any) -> None:
        self.backend = relation_system
        self.expr_visitor = expression_visitor

    def visit(self, node: RelationNode) -> Any:
        """Dispatch to the appropriate visit method via double-dispatch."""
        return node.accept(self)

    def visit_read_rel(self, node: ReadRelNode) -> Any:
        """Visit a read (scan) node."""
        return self.backend.read(node.dataframe)

    def visit_project_rel(self, node: ProjectRelNode) -> Any:
        """Visit a project node — dispatches on ProjectOperation variant."""
        relation = self.visit(node.input)
        compiled_exprs = [self._compile_expression(e) for e in node.expressions]
        match node.operation:
            case ProjectOperation.SELECT:
                return self.backend.project_select(relation, compiled_exprs)
            case ProjectOperation.WITH_COLUMNS:
                return self.backend.project_with_columns(relation, compiled_exprs)
            case ProjectOperation.DROP:
                return self.backend.project_drop(relation, compiled_exprs)
            case ProjectOperation.RENAME:
                return self.backend.project_rename(relation, node.rename_mapping)

    def visit_filter_rel(self, node: FilterRelNode) -> Any:
        """Visit a filter node — compiles the predicate expression."""
        relation = self.visit(node.input)
        predicate = self._compile_expression(node.predicate)
        return self.backend.filter(relation, predicate)

    def visit_sort_rel(self, node: SortRelNode) -> Any:
        """Visit a sort node."""
        relation = self.visit(node.input)
        return self.backend.sort(relation, node.sort_fields)

    def visit_fetch_rel(self, node: FetchRelNode) -> Any:
        """Visit a fetch node — handles both head and tail variants."""
        relation = self.visit(node.input)
        if node.from_end:
            return self.backend.fetch_from_end(relation, node.count)
        return self.backend.fetch(relation, node.offset, node.count)

    def visit_join_rel(self, node: JoinRelNode) -> Any:
        """Visit a join node — dispatches asof joins separately."""
        left = self.visit(node.left)
        right = self.visit(node.right)
        if node.join_type == JoinType.ASOF:
            return self.backend.join_asof(
                left, right,
                on=node.on[0] if node.on else node.left_on[0],
                by=None,
                strategy=node.strategy or "backward",
                tolerance=node.tolerance,
            )
        return self.backend.join(
            left, right,
            join_type=node.join_type,
            on=node.on,
            left_on=node.left_on,
            right_on=node.right_on,
            suffix=node.suffix,
        )

    def visit_aggregate_rel(self, node: AggregateRelNode) -> Any:
        """Visit an aggregate node — empty measures means distinct."""
        relation = self.visit(node.input)
        if not node.measures:
            return self.backend.distinct(relation, node.keys)
        compiled_measures = [self._compile_expression(m) for m in node.measures]
        return self.backend.aggregate(relation, node.keys, compiled_measures)

    def visit_set_rel(self, node: SetRelNode) -> Any:
        """Visit a set node (union)."""
        relations = [self.visit(inp) for inp in node.inputs]
        return self.backend.union_all(relations)

    def visit_extension_rel(self, node: ExtensionRelNode) -> Any:
        """Visit an extension node — dispatches via operation name lookup."""
        relation = self.visit(node.input)
        method_name = node.operation.name.lower()
        method = getattr(self.backend, method_name)
        return method(relation, **node.options)

    def _compile_expression(self, expr: Any) -> Any:
        """Compile an expression AST node, or pass through native/string expressions."""
        if isinstance(expr, ExpressionNode):
            return self.expr_visitor.visit(expr)
        return expr
