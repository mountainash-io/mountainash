"""Unified relation visitor for relational AST nodes.

Walks the relational AST and calls backend RelationSystem methods.
Composes with the expression visitor for compiling embedded expression ASTs.
"""

from __future__ import annotations
from typing import Any, Callable, Optional

from mountainash.core.constants import JoinType, ProjectOperation
from mountainash.core.types import (
    is_polars_dataframe, is_polars_lazyframe,
    is_pandas_dataframe, is_pyarrow_table,
)
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

    def __init__(
        self,
        relation_system: Any,
        expression_visitor: Any,
        *,
        ref_resolver: Optional[Callable[[str], Any]] = None,
    ) -> None:
        self.backend = relation_system
        self.expr_visitor = expression_visitor
        self.ref_resolver = ref_resolver

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
        compiled_exprs = [self.compile_expression(e) for e in node.expressions]
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
        predicate = self.compile_expression(node.predicate)
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
        compiled_measures = [self.compile_expression(m) for m in node.measures]
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

    def visit_ref_rel(self, node: Any) -> Any:
        """Visit a ref node — resolves via ref_resolver or raises RelationDAGRequired."""
        if self.ref_resolver is None:
            from mountainash.relations.dag.errors import RelationDAGRequired
            raise RelationDAGRequired(
                f"RefRelNode({node.name!r}) cannot be compiled standalone — "
                "use RelationDAG.collect() or supply ref_resolver explicitly"
            )
        return self.ref_resolver(node.name)

    def visit_resource_read_rel(self, node: Any) -> Any:
        """Visit a resource-read node — delegates to backend's read_resource."""
        out = self.backend.read_resource(node.resource)
        if node.resource.table_schema is not None:
            out = self.apply_conform(out, node.resource.table_schema)
        return out

    def visit_pipeline_step_rel(self, node: Any) -> Any:
        """Visit a pipeline-step node — delegates to node's executor."""
        if node.executor is None:
            raise ValueError(
                f"No executor provided for PipelineStepRelNode '{node.step_name}'. "
                f"Pass an executor via source(..., executor=runner) or dag.add(..., executor=runner)."
            )
        return node.executor.execute(
            pipeline=node.pipeline,
            step_name=node.step_name,
            predicates=node.pushed_predicates,
            data_key=node.data_key,
        )

    def apply_conform(self, native: Any, schema: Any) -> Any:
        """Apply conform from a TypeSpec or raw frictionless schema dict.

        ``compile_conform`` always returns a Polars DataFrame; wrap back to
        LazyFrame so this method's return type is consistent with the Polars
        path of ``visit_resource_read_rel``.

        For non-Polars backends, conform is deferred.
        # TODO: conform on non-Polars backends (narwhals, ibis)
        """
        cls_name = type(self.backend).__name__
        if "Narwhals" in cls_name or "Ibis" in cls_name:
            # Conform on non-Polars backends is not yet supported.
            return native
        if isinstance(schema, dict):
            from mountainash.typespec.frictionless import typespec_from_frictionless
            schema = typespec_from_frictionless(schema)
        from mountainash.conform.compiler import compile_conform
        import polars as pl
        # compile_conform returns a Polars DataFrame; re-wrap as LazyFrame
        result_df = compile_conform(schema, native)
        if isinstance(result_df, pl.DataFrame):
            return result_df.lazy()
        return result_df

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
        if is_polars_dataframe(target) or is_polars_lazyframe(target):
            if is_polars_lazyframe(value):
                return value
            if is_polars_dataframe(value):
                return value.lazy()
            # Try pandas → polars
            if is_pandas_dataframe(value):
                import polars as pl
                return pl.from_pandas(value).lazy()
            # Try pyarrow → polars
            if is_pyarrow_table(value):
                import polars as pl
                return pl.from_arrow(value).lazy()
            # Try dict → polars
            if isinstance(value, dict):
                import polars as pl
                return pl.DataFrame(value).lazy()
            # Fallback via narwhals
            try:
                import narwhals as nw
                import polars as pl
                native = nw.from_native(value, eager_only=True)
                return pl.from_pandas(native.to_pandas()).lazy()
            except Exception:
                pass
            raise TypeError(
                f"Cannot coerce {type(value).__name__} to Polars for cross-type join."
            )
        return value

    def compile_expression(self, expr: Any) -> Any:
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
