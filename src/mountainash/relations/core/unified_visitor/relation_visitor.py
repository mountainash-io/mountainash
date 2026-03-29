"""Unified relation visitor for relational AST nodes.

Walks the relational AST and calls backend RelationSystem methods.
Composes with the expression visitor for compiling embedded expression ASTs.
"""

from __future__ import annotations
from typing import Any

from mountainash.core.constants import JoinType, ProjectOperation
from mountainash.expressions.core.expression_api.api_base import BaseExpressionAPI
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

    def visit_source_rel(self, node: Any) -> Any:
        """Visit a source node — materialize Python data into a DataFrame."""
        from mountainash.pydata.ingress.pydata_ingress import PydataIngress

        df = PydataIngress.convert(node.data)
        return self.backend.read(df)

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
        """Visit a join node — dispatches asof joins separately.

        When the right side is a different backend type from the left,
        the visitor coerces the right side to match (e.g. pandas → Polars).
        """
        left = self.visit(node.left)
        right = self._visit_and_coerce_right(node.right, left)
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

    def _visit_and_coerce_right(self, right_node: RelationNode, left_result: Any) -> Any:
        """Visit the right side of a join, coercing to match the left's type if needed.

        If the right side produces a different backend type (e.g. pandas DataFrame
        when left is a Polars LazyFrame), convert it to match the left side.
        This enables cross-type joins like ``relation(polars_df).join(pandas_df, ...)``.
        """
        try:
            return self.visit(right_node)
        except TypeError:
            # The backend's read() rejected the right side's type.
            # Extract the raw dataframe and coerce it to match the left.
            if isinstance(right_node, ReadRelNode):
                coerced = self._coerce_to_match(left_result, right_node.dataframe)
                return coerced
            raise

    @staticmethod
    def _coerce_to_match(target: Any, value: Any) -> Any:
        """Coerce *value* to match *target*'s backend type.

        Supports:
        - target is Polars LazyFrame/DataFrame → convert value via pl.from_pandas()
          or narwhals intermediary
        - target is narwhals DataFrame → convert via nw.from_native()
        """
        import polars as pl

        if isinstance(target, (pl.DataFrame, pl.LazyFrame)):
            if isinstance(value, (pl.DataFrame, pl.LazyFrame)):
                return value.lazy() if isinstance(value, pl.DataFrame) else value
            # Try pandas → polars
            import pandas as pd
            if isinstance(value, pd.DataFrame):
                return pl.from_pandas(value).lazy()
            # Try pyarrow → polars
            try:
                import pyarrow as pa
                if isinstance(value, pa.Table):
                    return pl.from_arrow(value).lazy()
            except ImportError:
                pass
            # Try dict → polars
            if isinstance(value, dict):
                return pl.DataFrame(value).lazy()
            # Fallback via narwhals
            try:
                import narwhals as nw
                native = nw.from_native(value, eager_only=True)
                return pl.from_pandas(native.to_pandas()).lazy()
            except Exception:
                pass
            raise TypeError(
                f"Cannot coerce {type(value).__name__} to Polars for cross-type join."
            )
        return value

    def _compile_expression(self, expr: Any) -> Any:
        """Compile an expression AST node, or pass through native/string expressions.

        Handles three cases:
        1. ExpressionNode — compile directly via the expression visitor.
        2. BaseExpressionAPI (e.g. ma.col("x").gt(5)) — extract ._node and compile.
        3. Anything else (native expressions, strings) — pass through unchanged.
        """
        if isinstance(expr, ExpressionNode):
            return self.expr_visitor.visit(expr)
        if isinstance(expr, BaseExpressionAPI):
            return self.expr_visitor.visit(expr._node)
        return expr
