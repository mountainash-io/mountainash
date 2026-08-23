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


def _present_operation_keys(node: RelationNode, op: Any) -> frozenset:
    """The op's own RKEY plus the function keys structurally present in
    *node*'s bound ``EXPRESSION``/``EXPRESSION_LIST`` args -- the caller's
    evidence for which operation(s) were actually being compiled, used to
    disambiguate :func:`~mountainash.core.limitations.enrich_materialization`
    candidates that share a native exception type."""
    from mountainash.relations.core.relation_system.relation_mapping.registry import ArgKind

    keys: set = {op.operation_key}
    for binding in op.args:
        if binding.kind in (ArgKind.EXPRESSION, ArgKind.EXPRESSION_LIST):
            keys.update(_iter_function_keys(getattr(node, binding.field)))
    return frozenset(keys)


_UNRESOLVED = object()


def _first_input_node(node: RelationNode) -> "RelationNode | None":
    from mountainash.relations.core.relation_nodes import (
        AggregateRelNode, ConformRelNode, ExtensionRelNode, FetchRelNode,
        FilterRelNode, JoinRelNode, ProjectRelNode, SetRelNode, SortRelNode,
    )
    if isinstance(node, JoinRelNode):
        return node.left
    if isinstance(node, SetRelNode):
        return node.inputs[0] if node.inputs else None
    if isinstance(node, (FilterRelNode, ProjectRelNode, SortRelNode, FetchRelNode,
                         AggregateRelNode, ConformRelNode, ExtensionRelNode)):
        return node.input
    return None


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
        identity_resolver: Optional[Callable[[str], Any]] = None,
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
        self.identity_resolver = identity_resolver
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
        dialect = self._authoritative_dialect(node, op)
        if dialect is _UNRESOLVED:
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

        # Compound predicate gate (§3): collect blocking predicate facts once per call.
        from mountainash.core.capabilities.predicates import BoundCall
        bindings = {p: getattr(node, p, None) for p in param_names}
        supplied = frozenset(p for p in param_names if getattr(node, p, None) is not None)
        bound = BoundCall(
            operation_key=op.operation_key, backend=family, dialect=dialect,
            bindings=bindings, supplied=supplied,
        )
        violations = CapabilityRegistry.violations_for(bound)
        if violations:
            ordered = sorted(violations, key=lambda f: (f.param, f.message))
            combined = "; ".join(f.message for f in ordered)
            raise BackendCapabilityError(
                combined, backend=self.backend.BACKEND_NAME,
                function_key=op.operation_key, limitation=ordered[0],
            )

        for param in param_names:
            fact = CapabilityRegistry.capability_for(op.operation_key, param, family, dialect)
            if fact is None or fact.level is not CapabilityLevel.UNSUPPORTED:
                continue
            if fact.enforcement is not Enforcement.GATE:
                continue
            if getattr(node, param, None) is not None:
                _raise(fact)

    def _authoritative_dialect(self, node: RelationNode, op: Any):
        input_node = _first_input_node(node)
        if input_node is None:
            return _UNRESOLVED
        family, dialect = self._physical_identity(input_node)
        if family is None or family != self.backend.backend_type:
            return _UNRESOLVED
        return dialect

    def _physical_identity(self, node: RelationNode, seen: "set | None" = None):
        if seen is None:
            seen = set()
        try:
            from mountainash.core.backend_detection import identify_backend_identity
            from mountainash.relations.core.relation_nodes import ReadRelNode
            from mountainash.relations.core.relation_nodes.extensions_mountainash import (
                RefRelNode, ResourceReadRelNode, SourceRelNode,
            )
            if isinstance(node, ReadRelNode):
                ident = identify_backend_identity(node.dataframe)
                return ident.family, ident.dialect
            if isinstance(node, RefRelNode):
                if self.identity_resolver is None or node.name in seen:
                    return None, None
                resolved = self.identity_resolver(node.name)
                return (self._physical_identity(resolved, seen | {node.name})
                        if resolved is not None else (None, None))
            if isinstance(node, (SourceRelNode, ResourceReadRelNode)):
                return None, None
            child = _first_input_node(node)
            return self._physical_identity(child, seen) if child is not None else (None, None)
        except Exception:
            return None, None

    def _dispatch(self, node: RelationNode, op: Any) -> Any:
        if self.enforce_capabilities:
            self._gate_capabilities(node, op)

        from mountainash.core.limitations import enrich_materialization

        if op.handler is not None:
            # Handler ops wrap their own native call (see handlers.py) --
            # never wrap the whole handler, or a child read/coercion
            # TypeError would be narrowed under the parent's RKEY.
            return op.handler(node, self)
        method = getattr(self.backend, op.protocol_method.__name__)
        args = [self._bind(node, b) for b in op.args]  # children compiled OUTSIDE the wrap
        kwargs = self._bind_options(node, op)
        prefer = _present_operation_keys(node, op)
        d = self._authoritative_dialect(node, op)
        dialect = getattr(self.backend, "dialect", None) if d is _UNRESOLVED else d
        return enrich_materialization(
            self.backend, lambda: method(*args, **kwargs),
            prefer_operation_keys=prefer,
            dialect=dialect,
        )

    def _enrich_native_call(self, node: RelationNode, operation_key: Any, fn: Callable[[], Any]) -> Any:
        """Wrap a single native backend call in residue enrichment, scoped to
        ``operation_key`` and the authoritative input dialect (item 95)."""
        from mountainash.core.limitations import enrich_materialization
        from mountainash.relations.core.relation_system.relation_mapping.registry import (
            RelationOperationRegistry,
        )
        op = RelationOperationRegistry.get(operation_key)
        d = self._authoritative_dialect(node, op)   # item 95: _UNRESOLVED | str | None
        dialect = getattr(self.backend, "dialect", None) if d is _UNRESOLVED else d
        return enrich_materialization(
            self.backend, fn,
            prefer_operation_keys=frozenset({operation_key}),
            dialect=dialect,
        )

    def _bind(self, node: RelationNode, binding: Any) -> Any:
        from mountainash.relations.core.relation_system.relation_mapping.registry import (
            ArgKind,
        )
        value = getattr(node, binding.field)
        if binding.kind is ArgKind.INPUT:
            return self.visit(value)
        if binding.kind is ArgKind.INPUT_LIST:
            anchor = self.visit(value[0])   # anchor must succeed; a TypeError propagates
            results = [anchor]
            for v in value[1:]:
                try:
                    results.append(self.visit(v))
                except TypeError:
                    # Cross-family operand: the shared visitor's read() rejected
                    # the operand's raw dataframe. Coerce it to the anchor's
                    # family (and, for a narwhals anchor, exact dialect/shape)
                    # -- the same catch-and-coerce shape _visit_and_coerce_right
                    # uses for joins. A derived (non-ReadRelNode) root re-raises:
                    # that is the join path's pre-existing direct-read-only boundary.
                    if not isinstance(v, ReadRelNode):
                        raise
                    results.append(self._coerce_to_match(anchor, v.dataframe))
            if len(results) > 1:
                results = [anchor] + [
                    self._coerce_same_family_dialect(anchor, r) for r in results[1:]
                ]
            return results
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

        fields_match = schema.fields_match
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

        Also coerces a same-family, different-dialect narwhals operand (item
        91) -- narwhals' own read() never raises for a cross-dialect wrap, so
        both sides visit successfully; the mismatch is caught here instead,
        after both are visited, by comparing their actual dialects.
        """
        try:
            right_result = self.visit(right_node)
        except TypeError:
            # The backend's read() rejected the right side's type.
            # Extract the raw dataframe and coerce it to match the left.
            if isinstance(right_node, ReadRelNode):
                coerced = self._coerce_to_match(left_result, right_node.dataframe)
                return coerced
            raise
        return self._coerce_same_family_dialect(left_result, right_result)

    @staticmethod
    def _coerce_to_match(target: Any, value: Any) -> Any:
        """Coerce *value* to match *target*'s backend type.

        Supports:
        - target is Polars LazyFrame/DataFrame -> convert value via pl.from_pandas()
          or narwhals intermediary (existing ladder, extended with list[dict])
        - target is Narwhals DataFrame/LazyFrame -> convert dict/list[dict]/Polars
          LazyFrame/anything exposing to_pyarrow() (e.g. an Ibis Table -- same
          duck-type pattern the Polars branch below already uses) into a narwhals
          frame, then delegate to _coerce_same_family_dialect() (item 91) to match
          the target's EXACT dialect and eager/lazy shape -- not merely "some"
          narwhals frame (Revision 1's bug, item 94 Codex review round 1 finding 2)
        - target is an Ibis Table -> convert value via ibis.memtable(), unwrapping
          a lazy narwhals wrapper via .to_native() first (memtable() cannot ingest
          a lazy narwhals frame directly -- round 1 finding 3)
        """
        from mountainash.core.types import (
            is_narwhals_dataframe,
            is_narwhals_lazyframe,
            is_ibis_table,
        )

        if is_polars_dataframe(target) or is_polars_lazyframe(target):
            if is_polars_lazyframe(value):
                return value
            if is_polars_dataframe(value):
                return value.lazy()
            if is_pandas_dataframe(value):
                import polars as pl
                return pl.from_pandas(value).lazy()
            if is_pyarrow_table(value):
                import polars as pl
                return pl.from_arrow(value).lazy()
            if isinstance(value, dict):
                import polars as pl
                return pl.DataFrame(value).lazy()
            if isinstance(value, (list, tuple)) and (not value or isinstance(value[0], dict)):
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

        if is_narwhals_dataframe(target) or is_narwhals_lazyframe(target):
            source_type = type(value).__name__
            try:
                import narwhals as nw
                if isinstance(value, dict) or (
                    isinstance(value, (list, tuple))
                    and (not value or isinstance(value[0], dict))
                ):
                    import pandas as pd
                    value = pd.DataFrame(value)
                elif is_polars_lazyframe(value):
                    value = value.collect()
                else:
                    to_arrow = getattr(value, "to_pyarrow", None)
                    if callable(to_arrow):
                        value = to_arrow()
                value = nw.from_native(value, eager_only=True)
            except Exception as exc:
                raise TypeError(
                    f"Cannot coerce {source_type} to Narwhals for cross-type "
                    f"join: {exc}"
                ) from exc
            # Delegate dialect/shape matching to item 91's already-reviewed
            # function -- its own exceptions are already clean and enriched,
            # so they propagate unwrapped (no double-wrap).
            return UnifiedRelationVisitor._coerce_same_family_dialect(target, value)

        if is_ibis_table(target):
            source_type = type(value).__name__
            try:
                import ibis
                from mountainash.relations.backends.relation_systems.ibis._sqlite_compat import (
                    ensure_sqlite_nat_adapter,
                )
                ensure_sqlite_nat_adapter()
                if is_narwhals_lazyframe(value):
                    value = value.to_native()
                return ibis.memtable(value)
            except Exception as exc:
                raise TypeError(
                    f"Cannot coerce {source_type} to Ibis for cross-type join: {exc}"
                ) from exc

        # Unreachable for any genuine Polars/Narwhals/Ibis-native target (this
        # function's sole call site passes the LEFT side's own already-visited,
        # backend-native compiled result -- always one of the three checks
        # above). Deliberately reachable for an object that satisfies narwhals'
        # own permissive detection (hasattr(..., "_compliant_frame")) but fails
        # the strict TypeGuards used above -- a compatibility tightening
        # consistent with item 91's established policy (_coerce_same_family_
        # dialect's own docstring: never duck-type where a non-narwhals object
        # could spoof). Fails loud rather than the prior silent no-op.
        raise TypeError(
            f"Cannot coerce {type(value).__name__} to unrecognized target type "
            f"{type(target).__name__} for cross-type join."
        )

    _NW_DIALECT_CONVERTERS: "dict[str, str]" = {
        "pandas": "to_pandas",
        "polars": "to_polars",
        "pyarrow": "to_arrow",
    }

    @staticmethod
    def _coerce_same_family_dialect(target: Any, value: Any) -> Any:
        """Coerce *value* to match *target*'s narwhals native dialect when both
        are narwhals frames -- checked via the codebase's own typed
        `is_narwhals_dataframe`/`is_narwhals_lazyframe` TypeGuards
        (`core/types.py`, module-name + class-name based; NEVER a duck-typed
        `hasattr(..., "_compliant_frame")` or `getattr(..., "implementation",
        None)` check, either of which a non-narwhals object could spoof) -- of
        the same family but a different native dialect OR a different eager/
        lazy shape (checked independently of the dialect *string*: narwhals'
        own dialect helper only distinguishes eager vs lazy for the `polars`
        implementation, so an eager-pandas and a lazy-pandas frame -- lazy
        pandas is real, reachable via `.lazy()` -- share the identical
        "narwhals-pandas" string; comparing eager/lazy explicitly, not via
        dialect-string equality, is what actually makes this shape-aware for
        every implementation, not just Polars). No-op when either side isn't
        a genuine narwhals frame, or both share the exact same dialect string
        AND the same eager/lazy shape (untouched -- a performance/no-round-
        trip guarantee, not a correctness contract: nothing downstream relies
        on operand identity). Polars/Ibis raw-value cross-type coercion is
        handled separately by _coerce_to_match."""
        from mountainash.core.types import is_narwhals_dataframe, is_narwhals_lazyframe

        if not (
            (is_narwhals_dataframe(target) or is_narwhals_lazyframe(target))
            and (is_narwhals_dataframe(value) or is_narwhals_lazyframe(value))
        ):
            return value
        from mountainash.core.backend_detection import narwhals_dialect

        target_dialect = narwhals_dialect(target)
        value_dialect = narwhals_dialect(value)
        target_is_lazy = is_narwhals_lazyframe(target)
        value_is_lazy = is_narwhals_lazyframe(value)
        if (
            target_dialect is not None
            and target_dialect == value_dialect
            and target_is_lazy == value_is_lazy
        ):
            return value  # identical shape: same dialect string AND same eager/lazy-ness

        if target_is_lazy:
            # Narwhals itself cannot join/concat an eager operand -- or a
            # differently-shaped lazy operand -- against a lazy target,
            # regardless of dialect match: a pre-existing narwhals limitation
            # this coercion fix does not attempt to lift (would require
            # materializing/lazifying across the whole tree, a much larger
            # scope than dialect coercion). Fail clean, not with whatever raw
            # error narwhals itself would eventually raise. Deliberately
            # OUTSIDE the try block below -- this is a validation decision,
            # not a conversion attempt, so it must never be wrapped as a
            # "conversion failed" error.
            raise TypeError(
                f"Cannot coerce a {value_dialect} operand against a lazy "
                f"{target_dialect} target for cross-dialect join/union -- "
                "narwhals does not support combining a lazy target with an "
                "eager or differently-shaped lazy operand."
            )

        method_name = UnifiedRelationVisitor._NW_DIALECT_CONVERTERS.get(
            target.implementation.value
        )
        if method_name is None:
            # Also a validation decision (dict lookup, deterministic), not a
            # conversion attempt -- deliberately outside the try block, same
            # reasoning as the lazy-target check above. Covers e.g. Modin- or
            # cuDF-backed narwhals targets: recognized dialects, deliberately
            # unsupported conversion targets.
            raise TypeError(
                f"Cannot coerce {value_dialect} operand to match "
                f"{target_dialect} for cross-dialect join/union -- "
                "unsupported target dialect."
            )

        try:
            if value_is_lazy:
                value = value.collect()  # mountainash's house default is eager
                if narwhals_dialect(value) == target_dialect:
                    return value
            converted = getattr(value, method_name)()
            import narwhals as nw
            return nw.from_native(converted, eager_only=True)
        except Exception as exc:
            # Every remaining exception -- from .collect(), the conversion
            # call itself, or the re-wrap -- is uniformly wrapped with
            # dialect context, INCLUDING a TypeError raised by the real
            # conversion method (e.g. .to_pandas() failing for its own
            # reasons): both validation raises above already exited before
            # this block, so there is no longer an "our TypeError vs their
            # TypeError" ambiguity to preserve here.
            raise TypeError(
                f"Failed to coerce {value_dialect} operand to {target_dialect} "
                f"for cross-dialect join/union: {exc}"
            ) from exc

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
