"""Unified relation visitor for relational AST nodes.

Walks the relational AST and calls backend RelationSystem methods.
Composes with the expression visitor for compiling embedded expression ASTs.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable, Optional

from mountainash.core.types import (
    is_polars_dataframe, is_polars_lazyframe,
    is_pandas_dataframe, is_pyarrow_table,
)
from mountainash.expressions.core.expression_api.api_base import BaseExpressionAPI
from mountainash.expressions.core.expression_nodes import (
    ExpressionNode, ScalarFunctionNode, CastNode, IfThenNode,
    SingularOrListNode, WindowFunctionNode, OverNode,
)

from ..relation_nodes import RelationNode, ReadRelNode

if TYPE_CHECKING:
    from mountainash.conform.drift import ConformDrift
    from mountainash.relations.dag.key_context import KeyDriftContext


def _expression_children(node: ExpressionNode) -> list:
    """Genuine expression-AST children of *node* -- never an ``Any``-typed
    options/literal payload (``arguments-vs-options.md``: options are raw,
    never visited). Exhaustive over the 7 substrait + 1 mountainash-extension
    node types (``minimal-ast.md``, ENFORCED)."""
    if isinstance(node, ScalarFunctionNode):
        return list(node.arguments)
    if isinstance(node, CastNode):
        return [node.input]
    if isinstance(node, IfThenNode):
        return [c for pair in node.conditions for c in pair] + [node.else_clause]
    if isinstance(node, SingularOrListNode):
        return [node.value, *node.options]
    if isinstance(node, WindowFunctionNode):
        kids = [a for a in node.arguments if isinstance(a, ExpressionNode)]
        if node.window_spec is not None:
            kids += [
                p for p in node.window_spec.partition_by
                if isinstance(p, ExpressionNode)
            ]
        return kids
    if isinstance(node, OverNode):
        return [
            node.expression,
            *(p for p in node.window_spec.partition_by if isinstance(p, ExpressionNode)),
        ]
    return []  # FieldReferenceNode, LiteralNode: genuine leaves


def _iter_function_keys(value: Any, _seen: "set[int] | None" = None):
    """Recursively yield every non-None ``function_key`` in an expression
    AST, handling a raw :class:`ExpressionNode` tree, a
    :class:`BaseExpressionAPI` wrapper, or a list/tuple of either."""
    if isinstance(value, BaseExpressionAPI):
        value = value._node
    if isinstance(value, ExpressionNode):
        seen = _seen if _seen is not None else set()
        if id(value) in seen:
            return
        seen.add(id(value))
        if value.function_key is not None:
            yield value.function_key
        for child in _expression_children(value):
            yield from _iter_function_keys(child, seen)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _iter_function_keys(item, _seen)


def _present_expression_function_keys(node: RelationNode, op: Any) -> frozenset:
    """Function keys structurally present in *node*'s bound
    ``EXPRESSION``/``EXPRESSION_LIST`` args -- the caller's evidence for
    which operation(s) were actually being compiled, used to disambiguate
    :func:`~mountainash.core.limitations.enrich_materialization` candidates
    that share a native exception type."""
    from mountainash.relations.core.relation_system.relation_mapping.registry import ArgKind

    keys: set = set()
    for binding in op.args:
        if binding.kind in (ArgKind.EXPRESSION, ArgKind.EXPRESSION_LIST):
            keys.update(_iter_function_keys(getattr(node, binding.field)))
    return frozenset(keys)


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
        key_context: Optional["KeyDriftContext"] = None,
        enforce_capabilities: bool = True,
    ) -> None:
        self.backend = relation_system
        self.expr_visitor = expression_visitor
        self.ref_resolver = ref_resolver
        # DAG-provided FK context (item 48 PR-D), +1 optional param
        # analogous to ref_resolver (relation-dag-orchestrator). None for a
        # standalone/frame-level compile (relation_base.py) -- apply_conform
        # then never assesses the keys dimension and ConformDrift.key_changes
        # stays None (not assessed).
        self.key_context = key_context
        self.enforce_capabilities = enforce_capabilities
        if enforce_capabilities:
            # A gating consumer must ensure the capability declaration modules
            # are imported before querying the registry (bootstrap.py contract);
            # idempotent under the registry's load lock. Covers _gate_capabilities
            # below. Query-path autoload — a no-op in LOADED and ISOLATED states,
            # so test fixtures that reset() into ISOLATED do not break the visitor.
            from mountainash.core.capabilities.registry import CapabilityRegistry
            CapabilityRegistry.ensure_loaded()
        # Accumulates one ConformDrift per apply_conform() call that actually
        # assessed something (item 48 Task 7). Populated in AST-traversal
        # order — visits are depth-first sequential, so node_id
        # f"conform:{len(self.drift_reports)}" is deterministic. Only
        # non-None drift reports are appended; a conform call with no
        # available_columns and no actual_dtypes evidence contributes
        # nothing (honest non-assessment, not "assessed clean").
        self.drift_reports: list["ConformDrift"] = []

    def visit(self, node: RelationNode) -> Any:
        """Single dispatch site (spec §3.5): third-party visit-registry
        handler -> operation registry -> def handler or generic bind+call."""
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
        key = node.operation_key
        if key is None:
            from mountainash.relations.core.errors import UnregisteredRelationNodeError
            raise UnregisteredRelationNodeError(type(node))
        from mountainash.relations.core.relation_system.relation_mapping.registry import (
            RelationOperationRegistry,
        )
        op = RelationOperationRegistry.get(key)
        return self._dispatch(node, op)

    def _gate_capabilities(self, node, op) -> None:
        """Compile-time capability gate (spec Section 2, relations side).

        Declarative ops: every ArgBinding field + option is a gateable param.
        Handler ops: only gate_params are consulted, and a param-scoped fact
        fires ONLY when the node's field is populated (Codex finding #2 —
        narwhals join_asof is fine without tolerance).
        """
        from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry, Enforcement, WILDCARD_PARAM
        from mountainash.core.types import BackendCapabilityError

        family = getattr(self.backend, "backend_type", None)
        if family is None:
            return
        dialect = getattr(self.backend, "dialect", None)

        def _raise(fact):
            raise BackendCapabilityError(
                fact.message,
                backend=self.backend.BACKEND_NAME,
                function_key=op.operation_key,
                limitation=fact,
            )

        # Whole-op wildcard fact (e.g. narwhals unnest)
        fact = CapabilityRegistry.capability_for(
            op.operation_key, WILDCARD_PARAM, family, dialect
        )
        if fact is not None and fact.enforcement is Enforcement.GATE \
                and fact.level is CapabilityLevel.UNSUPPORTED:
            _raise(fact)

        # Param-scoped facts — fire only when the node field is populated.
        # Only GATE facts reach the gate; ROUTER_METADATA is consumed by the
        # backend router and MATERIALIZE_RESIDUE enriches a later error.
        # gate_params keeps its narrowed job: declaring that a populated node
        # field is sufficient evidence for a GATE fact to fire on a
        # handler-routed op.
        param_names = tuple(b.field for b in op.args) + tuple(op.options) + op.gate_params
        for param in param_names:
            fact = CapabilityRegistry.capability_for(op.operation_key, param, family, dialect)
            if fact is None or fact.level is not CapabilityLevel.UNSUPPORTED:
                continue
            if fact.enforcement is not Enforcement.GATE:
                continue
            if getattr(node, param, None) is not None:
                _raise(fact)

    def _dispatch(self, node: RelationNode, op: Any) -> Any:
        if self.enforce_capabilities:
            self._gate_capabilities(node, op)

        from mountainash.core.limitations import enrich_materialization

        if op.handler is not None:
            # No generic expression-field introspection for handler-routed
            # ops today -- an empty (non-None) preferred set is
            # authoritative in enrich_materialization, so this is a
            # verified no-op unless/until a handler op registers a
            # MATERIALIZE_RESIDUE fact.
            return enrich_materialization(
                self.backend, lambda: op.handler(node, self),
                prefer_operation_keys=frozenset(),
            )
        method = getattr(self.backend, op.protocol_method.__name__)
        args = [self._bind(node, b) for b in op.args]  # children compiled OUTSIDE the wrap
        kwargs = self._bind_options(node, op)
        prefer = _present_expression_function_keys(node, op)
        return enrich_materialization(
            self.backend, lambda: method(*args, **kwargs),
            prefer_operation_keys=prefer,
        )

    def _bind(self, node: RelationNode, binding: Any) -> Any:
        from mountainash.relations.core.relation_system.relation_mapping.registry import (
            ArgKind,
        )
        value = getattr(node, binding.field)
        if binding.kind is ArgKind.INPUT:
            return self.visit(value)
        if binding.kind is ArgKind.INPUT_LIST:
            return [self.visit(v) for v in value]
        if binding.kind is ArgKind.EXPRESSION:
            return self.compile_expression(value)
        if binding.kind is ArgKind.EXPRESSION_LIST:
            return [self.compile_expression(v) for v in value]
        return value  # LITERAL

    def _bind_options(self, node: RelationNode, op: Any) -> dict:
        kwargs = {f: getattr(node, f) for f in op.options}
        if op.options_field is not None:
            kwargs.update(getattr(node, op.options_field))
        return kwargs

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

        # Keys dimension (item 48 PR-D): only assessed when a DAG supplied a
        # KeyDriftContext. The "child" identity prefers this call's own
        # resource_name (the Frictionless resource actually being read, e.g.
        # a ResourceReadRelNode) and falls back to the currently-compiling
        # DAG relation's name (a bare ConformRelNode has no resource_name of
        # its own) — the DAG re-points key_context.resource_name per node
        # during its dependency loop (see dag.py _compile_with_refs), so
        # this fallback is correct for dependencies, not just the target.
        key_fks = None
        key_resource_name = None
        key_schema_of = None
        if self.key_context is not None:
            key_resource_name = (
                resource_name if resource_name is not None
                else self.key_context.resource_name
            )
            key_fks = self.key_context.constraints_for(key_resource_name)
            key_schema_of = self.key_context.schema_of

        conform_result = _build_conform_exprs(
            schema,
            available_columns=available,
            actual_dtypes=available_schema or None,
            contract=resolved_contract,
            node_identity=(node_id, resource_name, getattr(schema, "name", None)),
            key_fks=key_fks,
            key_resource_name=key_resource_name,
            schema_of=key_schema_of,
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
            # Arrow before pandas: a pandas round-trip widens temporal types
            # (ibis `date` -> datetime64[s]); Arrow preserves them.
            to_arrow = getattr(value, "to_pyarrow", None)
            if callable(to_arrow):
                try:
                    import polars as pl
                    return pl.from_arrow(to_arrow()).lazy()
                except Exception:
                    pass
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
