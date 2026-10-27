"""Unified relation visitor for relational AST nodes.

Walks the relational AST and calls backend RelationSystem methods.
Composes with the expression visitor for compiling embedded expression ASTs.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Callable, Optional

from mountainash.expressions.core.expression_api.api_base import BaseExpressionAPI
from mountainash.expressions.core.expression_nodes import (
    ExpressionNode, ScalarFunctionNode, CastNode, IfThenNode,
    SingularOrListNode, WindowFunctionNode, OverNode,
)
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_BOOLEAN,
    FKEY_MOUNTAINASH_SCALAR_CATEGORICAL,
    FKEY_MOUNTAINASH_SCALAR_DATETIME,
    FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL,
    FKEY_MOUNTAINASH_SCALAR_LIST,
    FKEY_MOUNTAINASH_SCALAR_STRING,
    FKEY_MOUNTAINASH_SCALAR_STRUCT,
    FKEY_SUBSTRAIT_CAST,
    FKEY_SUBSTRAIT_SCALAR_DATETIME,
)

from mountainash.core.capabilities.schema import PolicyConsumer

from ..relation_nodes import RelationNode, ReadRelNode

from mountainash.relations.core.relation_system.relation_keys.enums import (
    RKEY_MOUNTAINASH_REL,
)

if TYPE_CHECKING:
    from mountainash.conform.drift import ConformDrift
    from mountainash.core.capabilities.policy import _ExecutionContext
    from mountainash.relations.core.execution.metadata import MetadataSession
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



CONFORM_TRANSFORM_KEYS = frozenset(
    {
        FKEY_SUBSTRAIT_CAST.CAST,
        FKEY_MOUNTAINASH_SCALAR_BOOLEAN.PARSE_TOKENS,
        FKEY_MOUNTAINASH_SCALAR_CATEGORICAL.CAST,
        FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_DEFAULT,
        FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_XSD_DURATION,
        FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_XSD_PARTIAL_DATE,
        FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_TEMPORAL_ANY,
        FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL.PARSE_GEOPOINT,
        FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL.PARSE_GEOJSON,
        FKEY_MOUNTAINASH_SCALAR_LIST.PARSE,
        FKEY_MOUNTAINASH_SCALAR_LIST.CAST_ITEMS,
        FKEY_MOUNTAINASH_SCALAR_STRING.TO_TIME,
        FKEY_MOUNTAINASH_SCALAR_STRING.TO_INTEGER,
        FKEY_MOUNTAINASH_SCALAR_STRUCT.CAST,
        FKEY_SUBSTRAIT_SCALAR_DATETIME.STRPTIME_DATE,
        FKEY_SUBSTRAIT_SCALAR_DATETIME.STRPTIME_TIMESTAMP,
    }
)
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


def _schema_prototype_expression(value: Any) -> bool:
    """Qualify value-independent native operations, never infer their types."""
    from mountainash.expressions.core.expression_nodes import FieldReferenceNode, LiteralNode
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_MOUNTAINASH_NAME,
        FKEY_SUBSTRAIT_SCALAR_ARITHMETIC as Arithmetic,
        FKEY_SUBSTRAIT_SCALAR_COMPARISON as Comparison,
    )

    if isinstance(value, BaseExpressionAPI):
        value = value._node
    if isinstance(value, (str, FieldReferenceNode)):
        return True
    if isinstance(value, LiteralNode):
        return not value.is_native
    if isinstance(value, CastNode):
        return all(_schema_prototype_expression(child) for child in _expression_children(value))
    if not isinstance(value, ScalarFunctionNode):
        return False
    key = value.function_key
    qualified = (
        isinstance(key, FKEY_MOUNTAINASH_NAME)
        or key in {Arithmetic.ADD, Arithmetic.SUBTRACT, Arithmetic.MULTIPLY,
                   Arithmetic.DIVIDE, Arithmetic.NEGATE, Arithmetic.ABS}
        or key in {Comparison.EQUAL, Comparison.NOT_EQUAL, Comparison.GT,
                   Comparison.LT, Comparison.GTE, Comparison.LTE,
                   Comparison.IS_NULL, Comparison.IS_NOT_NULL}
        or key is FKEY_SUBSTRAIT_CAST.CAST
    )
    return qualified and all(_schema_prototype_expression(arg) for arg in value.arguments)


def _numeric_schema_prototype_aggregate(value: Any, aggregates: Any, *, grouped: bool) -> bool:
    """Qualify native numeric reductions without calculating replacement types."""
    from mountainash.core.types import is_narwhals_dataframe, is_pyarrow_table
    from mountainash.expressions.core.expression_nodes import FieldReferenceNode
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_MOUNTAINASH_NAME,
        FKEY_SUBSTRAIT_SCALAR_AGGREGATE as Aggregate,
    )

    if is_narwhals_dataframe(value):
        value = value.to_native()
    for aggregate in aggregates:
        if isinstance(aggregate, BaseExpressionAPI):
            aggregate = aggregate._node
        while isinstance(aggregate, ScalarFunctionNode) and isinstance(
            aggregate.function_key, FKEY_MOUNTAINASH_NAME,
        ):
            aggregate = aggregate.arguments[0]
        if not (
            isinstance(aggregate, ScalarFunctionNode)
            and aggregate.function_key in {Aggregate.SUM, Aggregate.COUNT, Aggregate.AVG}
            and len(aggregate.arguments) == 1
            and isinstance(aggregate.arguments[0], FieldReferenceNode)
        ):
            return False
        name = aggregate.arguments[0].field
        if is_pyarrow_table(value):
            if not grouped and aggregate.function_key is Aggregate.AVG:
                # Narwhals builds an Arrow null scalar for an empty global mean,
                # but a double scalar for a populated mean.
                return False
            import pyarrow.types as pat
            dtype = value.schema.field(name).type
            numeric = pat.is_integer(dtype) or pat.is_floating(dtype)
        else:
            import numpy as np
            dtype = value[name].dtype
            # Nullable extension reductions can return object on empty input
            # but float on populated input (for example Int64.mean()).
            numeric = isinstance(dtype, np.dtype) and dtype.kind in "iuf"
        if not numeric:
            return False
    return bool(aggregates)

def _eager_schema_input(value: Any) -> bool:
    from mountainash.core.types import is_narwhals_dataframe, is_pandas_dataframe, is_pyarrow_table

    if is_narwhals_dataframe(value):
        value = value.to_native()
    return is_pandas_dataframe(value) or is_pyarrow_table(value)


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
        execution_context: "_ExecutionContext",
        metadata_session: "MetadataSession | None" = None,
        execution: Any = None,
        execution_key: str | None = None,
        transport: Any = None,
    ) -> None:
        self.backend = relation_system
        self.transport = transport
        self.expr_visitor = expression_visitor
        self.ref_resolver = ref_resolver
        self._resolved_refs_by_name: dict[str, Any] = {}
        # DAG-provided FK context (item 48 PR-D), +1 optional param
        # analogous to ref_resolver (relation-dag-orchestrator). None for a
        # standalone/frame-level compile (relation_base.py) -- apply_conform
        # then never assesses the keys dimension and ConformDrift.key_changes
        # stays None (not assessed).
        self.key_context = key_context
        self.identity_resolver = identity_resolver
        self.execution_context = execution_context
        self.metadata_session = metadata_session
        self.execution = execution
        self.execution_key = execution_key
        self._visiting_root = False
        self.reusable_lowering = True
        self.repeatable_result = True
        self.diagnostic_traces: dict[tuple[Any, Any], Any] = {}
        self.residue_checks: list[Any] = []
        self.residue_check_nodes: dict[str, str] = {}
        self.owned_residue_checks: list[Any] = []
        self._owned_checks_by_node: dict[int, tuple[Any, ...]] = {}
        self._local_checks_by_node: dict[int, tuple[Any, ...]] = {}
        # Accumulates one ConformDrift per apply_conform() call that actually
        # assessed something (item 48 Task 7). Populated in AST-traversal
        # order — visits are depth-first sequential, so node_id
        # f"conform:{len(self.drift_reports)}" is deterministic. Only
        # non-None drift reports are appended; a conform call with no
        # available_columns and no actual_dtypes evidence contributes
        # nothing (honest non-assessment, not "assessed clean").
        self.drift_reports: list["ConformDrift"] = []
        self._structured_plans_by_node: dict[int, Any] = {}
        self._conform_plans_by_node: dict[int, Any] = {}
        self._conform_metadata_by_node: dict[int, tuple[bool, frozenset[str], frozenset[str]]] = {}
        self._ref_plans_by_node: dict[int, Any] = {}
        self.structured_field_plans: Any = MappingProxyType({})

    @property
    def location(self):
        """The prepared execution location of the node being visited, if any."""
        if self.execution is None:
            return None
        return self.execution.prepared.locations[self.execution_key]

    @property
    def execution_phase(self):
        """Phase of the prepared traversal, or None for standalone visits."""
        if self.execution is None:
            return None
        return self.execution.prepared.phase


    def record_lowering(self, method, definition=None, *, value=None):
        from mountainash.core.lowering_reuse import deferred_value, fold_lowering, selected_lowering

        if self.expr_visitor is not None:
            self.reusable_lowering &= self.expr_visitor.reusable_lowering
            self.repeatable_result &= self.expr_visitor.repeatable_result
        fold_lowering(
            self, selected_lowering(method, definition),
            deferred=value is None or deferred_value(value),
        )
    def require_schema_execution(self, reason: str) -> None:
        """Fail closed before a schema-phase handler would evaluate rows."""
        from mountainash.relations.core.execution.preparation import ExecutionPhase
        from mountainash.relations.core.errors import CompileRequiresExecutionError

        if self.execution_phase is ExecutionPhase.SCHEMA:
            raise CompileRequiresExecutionError(reason, node_key=self.execution_key)


    def visit(self, node: RelationNode) -> Any:
        """Single dispatch site (spec §3.5): third-party visit-registry
        handler -> operation registry -> def handler or generic bind+call."""
        if self.execution is not None and self._visiting_root:
            return self.execution.child(self, node)
        self._visiting_root = True
        try:
            return self._visit_prepared(node)
        finally:
            self._visiting_root = False

    def _visit_prepared(self, node: RelationNode) -> Any:
        from .visit_registry import RelationVisitRegistry

        handler = RelationVisitRegistry.get(type(node))
        if (handler is not None and self.execution_phase is not None
                and self.execution_phase.name == "SCHEMA"
                and getattr(handler, "__module__", "")
                != "mountainash.relations.core.relation_system.relation_mapping.handlers"):
            self.require_schema_execution(
                f"Third-party visitor handler {handler.__qualname__} has no schema-phase contract"
            )
        if handler is not None:
            self.record_lowering(handler)
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
        """Reuse the AST-known gate shared with whole-tree preparation."""
        from mountainash.relations.core.execution.capabilities import check_ast_capabilities
        from mountainash.relations.core.execution.location import ExecutionLocation
        from mountainash.relations.core.materialization import ExecutionForm

        if self.execution is not None:
            check_ast_capabilities(
                node, self.execution.prepared.locations[self.execution_key],
                execution_context=self.execution_context,
            )
            return
        dialect = self._authoritative_dialect(node, op)
        if dialect is _UNRESOLVED:
            dialect = getattr(self.backend, "dialect", None)
        check_ast_capabilities(
            node,
            ExecutionLocation(self.backend.backend_type, dialect, ExecutionForm.DEFERRED, "bound"),
            execution_context=self.execution_context,
        )

    def _authoritative_dialect(self, node: RelationNode, op: Any):
        if self.execution is not None:
            return self.execution.prepared.locations[self.execution_key].dialect
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
            from mountainash.core.backend_detection import native_identity
            from mountainash.relations.core.relation_nodes import ReadRelNode
            from mountainash.relations.core.relation_nodes.extensions_mountainash import (
                RefRelNode, ResourceReadRelNode, SourceRelNode,
            )
            if isinstance(node, ReadRelNode):
                ident = native_identity(node.dataframe)
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

    def _transport_child_maps(self, node: RelationNode, op: Any) -> list[Any]:
        """Return completed transport maps for this node's relation inputs."""
        from mountainash.relations.core.relation_system.relation_mapping.registry import (
            ArgKind,
        )

        children: list[RelationNode] = []
        for binding in op.args:
            value = getattr(node, binding.field)
            if binding.kind is ArgKind.INPUT:
                children.append(value)
            elif binding.kind is ArgKind.INPUT_LIST:
                children.extend(value)
        if not children:
            children.extend(
                child
                for child in (
                    getattr(node, "left", None),
                    getattr(node, "right", None),
                    getattr(node, "input", None),
                )
                if child is not None
            )
        return [
            self._structured_plans_by_node.get(id(child), MappingProxyType({}))
            for child in children
        ]

    def _ref_output_names(self, node: RelationNode) -> list[str] | None:
        """Read already-resolved local evidence, in output order, without replaying a resolver."""
        if node.name not in self._resolved_refs_by_name:
            return None
        try:
            resolved = self._resolved_refs_by_name[node.name]
            if isinstance(resolved, Mapping):
                return list(resolved)
            collect_schema = getattr(resolved, "collect_schema", None)
            if callable(collect_schema):
                schema = collect_schema()
                names = getattr(schema, "names", None)
                if callable(names):
                    return list(names())
            columns = getattr(resolved, "columns", None)
            if columns is not None:
                return list(columns)
        except Exception:
            pass
        return None


    def _prepare_transport_lineage(self, node: RelationNode, op: Any | None = None) -> None:
        """Reject unsafe transport consumers before expression or backend dispatch."""
        from mountainash.relations.core.relation_system.relation_mapping.registry import (
            RelationOperationRegistry,
        )
        from mountainash.relations.core.structured_lineage import propagate_structured_plans

        operation = op or RelationOperationRegistry.get(node.operation_key)
        conform_plans = self._conform_plans_by_node.get(
            id(node), self._ref_plans_by_node.get(id(node), MappingProxyType({}))
        )
        propagate_structured_plans(
            node,
            self._transport_child_maps(node, operation),
            conform_plans,
            output_names_resolver=self._ref_output_names,
        )
        if self._owned_checks_by_node:
            from mountainash.relations.core.structured_lineage import propagate_owned_residue

            propagate_owned_residue(
                node,
                [self._owned_checks_by_node.get(id(child), ())
                 for child in self._relation_children(node, operation)],
                output_names_resolver=self._ref_output_names,
            )

    def _complete_transport_lineage(self, node: RelationNode, op: Any) -> None:
        """Record a node's transport output only after its native dispatch succeeds."""
        from mountainash.conform.structured_transport import (
            freeze_structured_field_plans,
        )
        from mountainash.relations.core.structured_lineage import (
            propagate_structured_plans,
        )
        plans = self._conform_plans_by_node.get(
            id(node), self._ref_plans_by_node.get(id(node), None)
        )
        metadata = self._conform_metadata_by_node.get(id(node))
        child_maps = self._transport_child_maps(node, op)
        if plans is None:
            plans = propagate_structured_plans(
                node,
                child_maps,
                MappingProxyType({}),
                output_names_resolver=self._ref_output_names,
            )
        elif metadata is not None and metadata[0]:
            _, overwritten, dropped = metadata
            incoming = child_maps[0] if child_maps else MappingProxyType({})
            carried = dict(incoming)
            for field_name in overwritten | dropped:
                carried.pop(field_name, None)
            carried.update(plans)
            plans = freeze_structured_field_plans(carried)
        self._structured_plans_by_node[id(node)] = plans
        self.structured_field_plans = plans
        if self._owned_checks_by_node or id(node) in self._local_checks_by_node:
            from mountainash.relations.core.structured_lineage import propagate_owned_residue

            child_checks = [self._owned_checks_by_node.get(id(child), ())
                            for child in self._relation_children(node, op)]
            carried = propagate_owned_residue(
                node, child_checks, output_names_resolver=self._ref_output_names,
            )
            output_checks = (*carried, *self._local_checks_by_node.get(id(node), ()))
            self._owned_checks_by_node[id(node)] = output_checks
            self.owned_residue_checks = list(output_checks)

    @staticmethod
    def _relation_children(node: RelationNode, op: Any) -> list[RelationNode]:
        from mountainash.relations.core.relation_system.relation_mapping.registry import ArgKind

        children = []
        for binding in op.args:
            value = getattr(node, binding.field)
            if binding.kind is ArgKind.INPUT:
                children.append(value)
            elif binding.kind is ArgKind.INPUT_LIST:
                children.extend(value)
        if not children:
            children = [child for child in (
                getattr(node, "left", None), getattr(node, "right", None),
                getattr(node, "input", None),
            ) if child is not None]
        return children

    def _dispatch(self, node: RelationNode, op: Any) -> Any:
        if self.execution_context.policy.has_demand(PolicyConsumer.GATE):
            self._gate_capabilities(node, op)

        from mountainash.core.limitations import enrich_materialization
        from mountainash.relations.core.execution.preparation import ExecutionPhase
        if self.execution_phase is ExecutionPhase.SCHEMA:
            if op.operation_key is RKEY_MOUNTAINASH_REL.PIVOT:
                self.require_schema_execution("Pivot output names depend on source values")
            if op.operation_key in {
                RKEY_MOUNTAINASH_REL.SAMPLE, RKEY_MOUNTAINASH_REL.TOP_K,
                RKEY_MOUNTAINASH_REL.FETCH_FROM_END,
                RKEY_MOUNTAINASH_REL.DROP_NULLS, RKEY_MOUNTAINASH_REL.DROP_NANS,
            }:
                return self.visit(node.input)

        if op.handler is not None:
            if (self.execution_phase is not None and self.execution_phase.name == "SCHEMA"
                    and getattr(op.handler, "__module__", "")
                    != "mountainash.relations.core.relation_system.relation_mapping.handlers"):
                self.require_schema_execution(
                    f"Third-party relation handler {op.handler.__qualname__} has no schema-phase contract"
                )
            # Handlers are third-party extension points; their dispatch must
            # still pass through this phase boundary and may explicitly reject
            # work that would evaluate or transfer rows.
            result = op.handler(node, self)
            self.record_lowering(op.handler, op.lowering, value=result)
            self._complete_transport_lineage(node, op)
            return result
        from mountainash.relations.core.relation_system.relation_mapping.registry import (
            ArgKind,
        )
        from mountainash.relations.core.aggregate_names import normalize_aggregate
        from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_SUBSTRAIT_REL

        aggregate_values = None
        if op.operation_key is RKEY_SUBSTRAIT_REL.AGGREGATE:
            keys, measures = normalize_aggregate(node.keys, node.measures)
            aggregate_values = {"keys": keys, "measures": measures}

        prepared_inputs = {
            binding.field: self._bind(node, binding)
            for binding in op.args
            if binding.kind in {ArgKind.INPUT, ArgKind.INPUT_LIST}
        }
        if self.execution_phase is ExecutionPhase.SCHEMA:
            eager = any(
                _eager_schema_input(value)
                for value in prepared_inputs.values()
                if not isinstance(value, (list, tuple))
            )
            if eager and op.operation_key is RKEY_SUBSTRAIT_REL.AGGREGATE:
                measures = aggregate_values["measures"]
                input_value = prepared_inputs.get("input")
                if not _numeric_schema_prototype_aggregate(
                    input_value, measures, grouped=bool(aggregate_values["keys"]),
                ):
                    self.require_schema_execution(
                        "Eager aggregate output typing is not established by a numeric empty prototype"
                    )
            if eager:
                for binding in op.args:
                    if aggregate_values is not None and binding.field == "measures":
                        continue  # Qualified against the native input above.
                    value = getattr(node, binding.field)
                    expressions = (
                        value if binding.kind is ArgKind.EXPRESSION_LIST
                        else [value] if binding.kind is ArgKind.EXPRESSION else []
                    )
                    if not all(_schema_prototype_expression(expr) for expr in expressions):
                        self.require_schema_execution(
                            "The eager expression has no value-independent schema-only typing contract"
                        )
        self._prepare_transport_lineage(node, op)
        method = getattr(self.backend, op.protocol_method.__name__)
        # Generic expression bindings belong to the operation's immediate input,
        # not the root source (projection and join may have changed its schema).
        with self.expr_visitor.input_scope(prepared_inputs.get("input")):
            args = []
            for binding in op.args:
                if binding.kind in {ArgKind.INPUT, ArgKind.INPUT_LIST}:
                    value = prepared_inputs[binding.field]
                elif aggregate_values is not None and binding.field in aggregate_values:
                    value = [self.compile_expression(expr) for expr in aggregate_values[binding.field]]
                else:
                    value = self._bind(node, binding)
                args.append(value)
            kwargs = self._bind_options(node, op)
        prefer = _present_operation_keys(node, op)
        d = self._authoritative_dialect(node, op)
        dialect = getattr(self.backend, "dialect", None) if d is _UNRESOLVED else d
        result = enrich_materialization(
            self.backend, lambda: method(*args, **kwargs),
            prefer_operation_keys=prefer,
            dialect=dialect,
            execution_context=self.execution_context,
        )
        self.record_lowering(method, op.lowering, value=result)
        self._complete_transport_lineage(node, op)
        return result

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
        result = enrich_materialization(
            self.backend, fn,
            prefer_operation_keys=frozenset({operation_key}),
            dialect=dialect,
            execution_context=self.execution_context,
        )
        if op.protocol_method is not None:
            self.record_lowering(
                getattr(self.backend, op.protocol_method.__name__), op.lowering, value=result,
            )
        return result

    def _bind(self, node: RelationNode, binding: Any) -> Any:
        from mountainash.relations.core.relation_system.relation_mapping.registry import (
            ArgKind,
        )
        value = getattr(node, binding.field)
        if isinstance(node, ReadRelNode) and binding.field == "dataframe":
            from mountainash.core.lowering_reuse import deferred_value

            # Native plans remain opaque: pass-through lowering is reusable,
            # but evaluating their output has no repeatability declaration.
            if deferred_value(value):
                self.repeatable_result = False
        if isinstance(node, ReadRelNode) and binding.field == "dataframe" \
                and self.execution_phase is not None and self.execution_phase.name == "SCHEMA":
            prototype = self.execution.schema_input(value)
            if (prototype is value and self.execution is not None
                    and self.execution.prepared.locations[self.execution_key].form.name == "EAGER"):
                from mountainash.relations.core.errors import CompileRequiresExecutionError

                raise CompileRequiresExecutionError(
                    f"Eager {type(value).__name__} has no dtype-faithful schema prototype",
                    node_key=self.execution_key,
                )
            value = prototype
        if binding.kind is ArgKind.INPUT:
            return self.visit(value)
        if binding.kind is ArgKind.INPUT_LIST:
            if self.execution is not None:
                # A prepared set has already resolved every operand and route.
                # Never reinterpret a child's native TypeError as coercion.
                return list(self.execution.operands(self, self.execution_key))
            anchor = self.visit(value[0])   # anchor must succeed; a TypeError propagates
            anchor_location = self._native_location(anchor)
            results = [anchor]
            for v in value[1:]:
                try:
                    results.append(self.visit(v))
                except TypeError:
                    # Cross-family operand: the shared visitor's read() rejected
                    # the operand's raw dataframe. Transfer it to the anchor's
                    # location -- the same catch-and-transfer shape
                    # _visit_and_coerce_right uses for joins. A derived
                    # (non-ReadRelNode) root re-raises: that is the join path's
                    # pre-existing direct-read-only boundary.
                    if not isinstance(v, ReadRelNode):
                        raise
                    results.append(self._transfer_native(v.dataframe, anchor_location))
            if len(results) > 1:
                results = [anchor] + [
                    self._align_narwhals(anchor, anchor_location, r) for r in results[1:]
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

    def _active_diagnostic_trace(self) -> Any:
        family = getattr(self.backend, "backend_type", None)
        dialect = getattr(self.backend, "dialect", None)
        key = (family, dialect)
        from mountainash.conform.diagnostics import OperationDiagnosticTrace
        trace = self.diagnostic_traces.get(key)
        if trace is None:
            trace = OperationDiagnosticTrace()
            self.diagnostic_traces[key] = trace
        return trace

    def terminal_residue_checks(self) -> tuple[Any, ...]:
        """Return only checks safe to evaluate at this visitor's native terminal.

        An adopted check belongs to its source and must be discharged there
        before a transfer or a terminal can hide/relabel its marker. Task 5
        supplies the source materialization boundary; until then fail closed.
        """
        from mountainash.relations.core.execution.metadata import _LocalResidue

        pending = self.owned_residue_checks
        if not pending and not self._owned_checks_by_node:
            return tuple(self.residue_checks)
        if self.execution is not None:
            destination = self.execution.prepared.locations[self.execution_key]
            if all(isinstance(owned, _LocalResidue) or
                   owned.source_location.key == destination.key for owned in pending):
                return tuple(owned.check for owned in pending)
        if any(not isinstance(owned, _LocalResidue) for owned in pending):
            raise RuntimeError(
                "A source-owned residue check must be discharged at its source "
                "before terminal materialization"
            )
        return tuple(owned.check for owned in pending)

    @staticmethod
    def _marker_alias(
        conform_node_id: str,
        residue_index: int,
        occupied: set[str],
    ) -> str:
        base = "__ma_residue_{}_{}".format(
            conform_node_id.replace(":", "_").replace("-", "_"),
            residue_index,
        )
        alias = base
        suffix = 1
        while alias in occupied:
            alias = f"{base}_{suffix}"
            suffix += 1
        occupied.add(alias)
        return alias

    def apply_conform(
        self,
        native: Any,
        schema: Any,
        *,
        empty_from_schema: bool = False,
        contract: Optional[Any] = None,
        resource_name: Optional[str] = None,
        owner_node: RelationNode | None = None,
        apply_value_transforms: bool = True,
    ) -> Any:
        """Apply conform from a TableSchema or raw Frictionless schema dict.

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
            schema: A TableSchema or raw Frictionless schema dict.
            empty_from_schema: Reconstruct an empty frame from the schema
                when the native object has zero columns (resource-read path).
            contract: Optional raw ``ConformRelNode.contract`` override
                (scalar string or dict) layered on top of ``schema.contract``
                and the ``fields_match`` preset via ``resolve_contract``.
            resource_name: The owning ``DataResource.name``, when this
                conform is being applied as part of a resource read. ``None``
                for a bare ``Relation.conform()`` call (no resource context).
        """
        from mountainash.core.lowering_reuse import REPEATABLE
        if isinstance(schema, dict):
            from mountainash.typespec.frictionless import table_schema_from_frictionless
            schema = table_schema_from_frictionless(schema)

        from mountainash.conform.contract import resolve_contract
        from mountainash.conform.expressions import _VALID_FIELDS_MATCH, _build_conform_exprs
        from mountainash.conform.errors import ConformError, ConformTransformError
        from mountainash.core.types import BackendCapabilityError
        from mountainash.typespec.source_shape import extract_source_shapes
        from mountainash.relations.schema_inference import _schema_from_dataframe
        from mountainash.typespec.converters import _execution_type_target
        type_target = _execution_type_target(self.execution_context.target.identity.family)

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

        from mountainash.relations.core.execution.preparation import ExecutionPhase
        schema_only = self.execution_phase is ExecutionPhase.SCHEMA
        fields_match = schema.fields_match
        # Validate before resolve_contract(): resolve_contract's
        # FIELDS_MATCH_PRESETS[fields_match] lookup deliberately raises
        try:
            actual_shapes = extract_source_shapes(native, target=type_target)
        except (TypeError, ImportError):
            actual_shapes = None
        # bare KeyError on an unknown preset name (pinned by
        # tests/conform/test_contract.py::
        # test_resolve_contract_unknown_fields_match_raises_keyerror) —
        # that behaviour is a contract.py invariant this call must not
        # disturb. resolve_conform_output performs this identical check
        # later too; duplicating it here preserves the typed ConformError
        # this entrypoint has always raised for a bad TableSchema.fields_match.
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
        if schema_only and not self.metadata_session.schema_complete and available is not None:
            missing = {
                (field.rename_from if field.rename_from is not None else name).split(".", 1)[0]
                for name, field in schema.fields.items()
            }.difference(available)
            if missing:
                self.require_schema_execution(
                    "Bounded resource discovery does not establish conform input fields: "
                    + ", ".join(sorted(missing))
                )

        # node_id captures the current report count *before* appending below
        # — deterministic since visits are depth-first sequential.
        node_id = (
            self.metadata_session.conform_id(owner_node if owner_node is not None else object())
            if self.metadata_session is not None
            else f"conform:{len(self.drift_reports)}"
        )

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
            actual_shapes=actual_shapes,
            contract=resolved_contract,
            node_identity=(node_id, resource_name, getattr(schema, "name", None)),
            key_fks=key_fks,
            key_resource_name=key_resource_name,
            schema_of=key_schema_of,
            apply_value_transforms=apply_value_transforms,
            type_target=type_target,
            raise_on_freeze=not schema_only,
        )
        if schema_only:
            if _eager_schema_input(native) and not all(
                _schema_prototype_expression(expr) for expr in conform_result.exprs
            ):
                self.require_schema_execution(
                    "Eager conform expressions do not establish value-independent output types"
                )
            if owner_node is not None:
                self._conform_plans_by_node[id(owner_node)] = conform_result.structured_field_plans
            if empty_from_schema and available == [] and schema.fields:
                self.record_lowering(self.backend.empty_frame, REPEATABLE)
                return self.backend.empty_frame(schema)
            with self.expr_visitor.input_scope(native):
                compiled_exprs = [
                    self.compile_expression(expr) for expr in conform_result.exprs
                ]
            self.record_lowering(self.backend.read, REPEATABLE, value=native)
            rel = self.backend.read(native)
            self.record_lowering(self.backend.project_with_columns, REPEATABLE, value=rel)
            rel = self.backend.project_with_columns(rel, compiled_exprs)
            self.record_lowering(self.backend.project_select, REPEATABLE, value=rel)
            rel = self.backend.project_select(rel, list(conform_result.output_schema))
            return rel
        if owner_node is not None:
            self._conform_plans_by_node[id(owner_node)] = (
                conform_result.structured_field_plans
            )
        if conform_result.drift is not None:
            self.drift_reports.append(conform_result.drift)

        # Zero-column reconstruction (resource-read path only).
        if empty_from_schema and available == [] and schema.fields:
            self.record_lowering(self.backend.empty_frame, REPEATABLE)
            return self.backend.empty_frame(schema)

        use_open = (
            resolved_contract.extra_columns == "evolve"
            and resolved_contract.mapping == "by_name"
        )
        if owner_node is not None:
            available_set = set(available) if available is not None else None
            overwritten = frozenset(
                name
                for name, field in schema.fields.items()
                if (
                    available_set is None
                    or (field.rename_from if field.rename_from is not None else name).split(".", 1)[0] in available_set
                    or resolved_contract.missing_columns == "null_fill"
                )
            )
            self._conform_metadata_by_node[id(owner_node)] = (
                use_open,
                overwritten,
                frozenset(conform_result.renamed_sources),
            )

        trace = self._active_diagnostic_trace()
        previous_trace = getattr(self.expr_visitor, "diagnostic_trace", None)
        previous_node_id = getattr(self.expr_visitor, "conform_node_id", None)
        self.expr_visitor.diagnostic_trace = trace
        self.expr_visitor.conform_node_id = node_id
        self.expr_visitor.raising_diagnostic = None
        try:
            with self.expr_visitor.input_scope(native):
                compiled_exprs = [
                    self.compile_expression(expr) for expr in conform_result.exprs
                ]
                compiled_filters = [
                    self.compile_expression(keep) for keep in conform_result.row_filters
                ]
                occupied = set(available or ())
                occupied.update(schema.fields)
                marker_exprs = []
                residue_checks = []
                result_protection_enabled = self.execution_context.policy.has_demand(
                    PolicyConsumer.RESULT_PROTECTION
                )
                if result_protection_enabled:
                    import dataclasses
                    from mountainash.core.capabilities import CapabilityRegistry, ResidueSignal
                    marker_trace = self.expr_visitor.diagnostic_trace
                    self.expr_visitor.diagnostic_trace = None
                    try:
                        for index, check in enumerate(conform_result.residue_checks):
                            facts = CapabilityRegistry.residue_candidates(
                                self.backend.backend_type,
                                getattr(self.backend, "dialect", None),
                                operation_key=check.function_key,
                                execution_context=self.execution_context,
                            )
                            if not any(fact.residue_signal is ResidueSignal.NON_NULL_TO_NULL for fact in facts):
                                continue
                            alias = self._marker_alias(node_id, index, occupied)
                            marker_expr = self.compile_expression(check.marker.name.alias(alias))
                            marker_exprs.append(marker_expr)
                            residue_checks.append(dataclasses.replace(check, marker=alias))
                            self.residue_check_nodes[alias] = node_id
                    finally:
                        self.expr_visitor.diagnostic_trace = marker_trace
                    self.residue_checks.extend(residue_checks)
                    if owner_node is not None and residue_checks:
                        from mountainash.relations.core.execution.metadata import _LocalResidue

                        self._local_checks_by_node[id(owner_node)] = tuple(
                            _LocalResidue(check) for check in residue_checks
                        )
        except (BackendCapabilityError, ConformError):
            raise
        except Exception as e:
            candidate = getattr(self.expr_visitor, "raising_diagnostic", None)
            candidates = (
                (candidate,)
                if candidate is not None
                and candidate.function_key in CONFORM_TRANSFORM_KEYS
                and candidate.failure_behavior == "throw"
                else ()
            )
            if candidates:
                raise ConformTransformError(
                    original_error=e,
                    candidates=candidates,
                ) from e
            raise
        finally:
            self.expr_visitor.diagnostic_trace = previous_trace
            self.expr_visitor.conform_node_id = previous_node_id

        try:
            self.record_lowering(self.backend.read, REPEATABLE, value=native)
            rel = self.backend.read(native)
            for predicate in compiled_filters:
                self.record_lowering(self.backend.filter, REPEATABLE, value=rel)
                rel = self.backend.filter(rel, predicate)

            # Conformance preserves cardinality even when every output is a
            # literal. Evaluate all bindings against the unchanged input, then
            # apply the contract's order and remove undeclared source columns.
            self.record_lowering(self.backend.project_with_columns, REPEATABLE, value=rel)
            rel = self.backend.project_with_columns(rel, compiled_exprs + marker_exprs)
            self.record_lowering(self.backend.project_select, REPEATABLE, value=rel)
            rel = self.backend.project_select(
                rel, list(conform_result.output_schema) + [check.marker for check in residue_checks],
            )
            return rel
        except (BackendCapabilityError, ConformError):
            raise
        except Exception as error:
            from mountainash.core.limitations import enrich_materialization

            def _raise_native(error=error):
                raise error

            return enrich_materialization(
                self.backend,
                _raise_native,
                diagnostic_trace=trace,
                execution_context=self.execution_context,
            )

    def _visit_and_coerce_right(self, right_node: RelationNode, left_result: Any) -> Any:
        """Visit the right side of a join, transferring it to the left's location if needed.

        If the right side produces a different backend type (e.g. pandas DataFrame
        when left is a Polars LazyFrame), move it to the left's location.
        This enables cross-type joins like ``relation(polars_df).join(pandas_df, ...)``.

        A same-family, different-dialect narwhals operand is also moved: narwhals'
        own read() never raises for a cross-dialect wrap, so both sides visit
        successfully and the mismatch is caught here, after both are visited.
        """
        left_location = self._native_location(left_result)
        try:
            right_result = self.visit(right_node)
        except TypeError:
            # The backend's read() rejected the right side's type.
            if isinstance(right_node, ReadRelNode):
                return self._transfer_native(right_node.dataframe, left_location)
            raise
        return self._align_narwhals(left_result, left_location, right_result)

    def _native_location(self, value: Any) -> Any:
        from mountainash.relations.core.execution.location import LocationResolver

        return LocationResolver(self._transport().tokens)._read(value)

    def _transport(self) -> Any:
        if self.transport is None:
            from mountainash.relations.core.execution.location import IdentityTokens
            from mountainash.relations.core.execution.transport import TransportSession

            self.transport = TransportSession(IdentityTokens())
        return self.transport

    def _transfer_native(self, value: Any, destination: Any) -> Any:
        return self._transport().transfer_native(value, destination)

    def _align_narwhals(self, anchor: Any, anchor_location: Any, value: Any) -> Any:
        """Give a narwhals operand its anchor's exact dialect and eager/lazy form."""
        from mountainash.core.types import is_narwhals_dataframe, is_narwhals_lazyframe

        if (is_narwhals_dataframe(anchor) or is_narwhals_lazyframe(anchor)) and (
            is_narwhals_dataframe(value) or is_narwhals_lazyframe(value)
        ):
            return self._transfer_native(value, anchor_location)
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
        if self.expr_visitor._is_backend_expression(expr):
            from mountainash.core.lowering_reuse import DEFERRED_ONLY, fold_lowering

            fold_lowering(self, DEFERRED_ONLY)
        return expr
