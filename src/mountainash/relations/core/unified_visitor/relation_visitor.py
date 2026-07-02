"""Unified relation visitor for relational AST nodes.

Walks the relational AST and calls backend RelationSystem methods.
Composes with the expression visitor for compiling embedded expression ASTs.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable, Optional

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

if TYPE_CHECKING:
    from mountainash.conform.drift import ConformDrift


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
        # Accumulates one ConformDrift per apply_conform() call that actually
        # assessed something (item 48 Task 7). Populated in AST-traversal
        # order — visits are depth-first sequential, so node_id
        # f"conform:{len(self.drift_reports)}" is deterministic. Only
        # non-None drift reports are appended; a conform call with no
        # available_columns and no actual_dtypes evidence contributes
        # nothing (honest non-assessment, not "assessed clean").
        self.drift_reports: list["ConformDrift"] = []

    def visit(self, node: RelationNode) -> Any:
        """Dispatch to registered handler or fall back to accept()."""
        from .visit_registry import RelationVisitRegistry

        handler = RelationVisitRegistry.get(type(node))
        if handler is not None:
            try:
                return handler(node, self)
            except Exception as e:
                # Re-raise with context. Use add_note when available (Python 3.11+)
                # rather than reconstructing the exception (which breaks custom __init__
                # signatures that don't accept a single positional string).
                try:
                    e.add_note(f"Error in registered handler for {type(node).__name__}")
                except AttributeError:
                    pass
                raise
        return node.accept(self)

    def visit_read_rel(self, node: ReadRelNode) -> Any:
        """Visit a read (scan) node."""
        return self.backend.read(node.dataframe)

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

    def apply_conform(
        self,
        native: Any,
        schema: Any,
        *,
        empty_from_schema: bool = False,
        contract: Optional[Any] = None,
        resource_name: Optional[str] = None,
    ) -> Any:
        """Apply conform from a TypeSpec or raw Frictionless schema dict.

        Uses the shared _build_conform_exprs helper to build expressions,
        then compiles them against the native backend object. Works for
        all backends (Polars, Ibis, Narwhals).

        Dispatch is policy-driven (item 48 Task 7): the resolved
        ``ConformContract``'s ``extra_columns``/``mapping`` decide
        with_columns (keep unmapped) vs select (projection, drops
        unmapped) — outcome-identical to the pre-Task-7
        ``fields_match == "open"`` check for every ``fields_match`` preset,
        but also honours an explicit ``contract=`` override that changes
        the policy without changing ``fields_match`` itself.

        Fields whose source column is missing from the native object are
        silently skipped so that partial data (e.g. API responses missing
        optional fields) conforms without raising ColumnNotFoundError.

        Args:
            native: The backend-native object (Polars/Ibis/pandas/etc.) to
                conform.
            schema: A TypeSpec or raw Frictionless schema dict.
            empty_from_schema: Reconstruct an empty frame from the schema
                when the native object has zero columns (resource-read path).
            contract: Optional raw ``ConformRelNode.contract`` override
                (scalar string or dict) layered on top of ``schema.contract``
                and the ``fields_match`` preset via ``resolve_contract``.
            resource_name: The owning ``DataResource.name``, when this
                conform is being applied as part of a resource read. ``None``
                for a bare ``Relation.conform()`` call (no resource context).
        """
        if isinstance(schema, dict):
            from mountainash.typespec.frictionless import typespec_from_frictionless
            schema = typespec_from_frictionless(schema)

        from mountainash.conform.contract import resolve_contract
        from mountainash.conform.expressions import _VALID_FIELDS_MATCH, _build_conform_exprs
        from mountainash.conform.errors import ConformError, ConformTransformError
        from mountainash.expressions.core.expression_protocols.api_builders.substrait.prtcl_api_bldr_cast import (
            CaseFailureBehaviour,
        )
        from mountainash.relations.schema_inference import _schema_from_dataframe
        import mountainash as ma

        # dtype-aware detection first ({} degrades honestly for an
        # unrecognized backend or a genuinely zero-column frame); falls back
        # to today's names-only detection when that degrades to empty, so
        # `available` is unaffected by the new dtype path in either case.
        available_schema = _schema_from_dataframe(native)
        if available_schema:
            available = list(available_schema.keys())
        elif hasattr(native, "collect_schema"):
            available = list(native.collect_schema().names())
        elif hasattr(native, "columns"):
            available = list(native.columns)
        else:
            available = None

        fields_match = schema.fields_match if schema.fields_match is not None else "open"
        # Validate before resolve_contract(): resolve_contract's
        # FIELDS_MATCH_PRESETS[fields_match] lookup deliberately raises a
        # bare KeyError on an unknown preset name (pinned by
        # tests/conform/test_contract.py::
        # test_resolve_contract_unknown_fields_match_raises_keyerror) —
        # that behaviour is a contract.py invariant this call must not
        # disturb. resolve_conform_output performs this identical check
        # later too; duplicating it here preserves the typed ConformError
        # this entrypoint has always raised for a bad TypeSpec.fields_match.
        if fields_match not in _VALID_FIELDS_MATCH:
            raise ConformError(
                f"Invalid fields_match={fields_match!r}. "
                f"Must be one of: {sorted(_VALID_FIELDS_MATCH)}"
            )
        resolved_contract = resolve_contract(
            fields_match,
            spec_contract=getattr(schema, "contract", None),
            override=contract,
        )

        # node_id captures the current report count *before* appending below
        # — deterministic since visits are depth-first sequential.
        node_id = f"conform:{len(self.drift_reports)}"
        conform_result = _build_conform_exprs(
            schema,
            available_columns=available,
            actual_dtypes=available_schema or None,
            contract=resolved_contract,
            node_identity=(node_id, resource_name, getattr(schema, "name", None)),
        )
        if conform_result.drift is not None:
            self.drift_reports.append(conform_result.drift)

        # Zero-column reconstruction (resource-read path only). The fields_match
        # guard above has already run and raised for strict modes; only the
        # tolerant modes (open/superset) reach here with a zero-column read.
        # MUST be `available == []` (known-zero-columns), never None
        # (uninspectable) and never falsy — see design doc finding 3.
        if empty_from_schema and available == [] and schema.fields:
            return self.backend.empty_frame(schema)

        use_open = (
            resolved_contract.extra_columns == "evolve"
            and resolved_contract.mapping == "by_name"
        )

        try:
            rel = ma.relation(native)

            # discard_row predicate (item 48 Task 6/7, finding 12): drop iff
            # the raw source is non-null AND a null-on-failure cast of it
            # fails. Legitimately-null source rows are always kept. Must run
            # on the *raw* source column before the with_columns/select
            # projection below — in select mode the original column may be
            # renamed or dropped by the projection.
            for src, declared in conform_result.row_filter_sources:
                keep = ~(
                    ma.col(src).is_not_null()
                    & ma.col(src)
                    .cast(declared, failure_behavior=CaseFailureBehaviour.NULL)
                    .is_null()
                )
                rel = rel.filter(keep)

            if use_open:
                rel = rel.with_columns(*conform_result.exprs)
                if conform_result.renamed_sources:
                    rel = rel.drop(*conform_result.renamed_sources)
            else:
                rel = rel.select(*conform_result.exprs)

            return rel._compile_and_execute()
        except Exception as e:
            # Build spec summary for diagnostic (parsing properties only)
            parsing_props = []
            for f in schema.fields:
                if getattr(f, "decimal_char", None) and f.decimal_char != ".":
                    parsing_props.append(f"decimalChar={f.decimal_char!r}")
                if getattr(f, "group_char", None):
                    parsing_props.append(f"groupChar={f.group_char!r}")
                if getattr(f, "bare_number", None) is False:
                    parsing_props.append("bareNumber=false")
                if getattr(f, "delimiter", None) and f.delimiter != ",":
                    parsing_props.append(f"delimiter={f.delimiter!r}")
            if parsing_props:
                raise ConformTransformError(
                    original_error=e,
                    spec_summary=", ".join(parsing_props),
                ) from e
            raise

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
