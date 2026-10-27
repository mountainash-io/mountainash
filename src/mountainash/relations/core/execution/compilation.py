"""Contextual compilation through the existing relation and expression visitors."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import replace
from typing import TYPE_CHECKING, Any

from mountainash.expressions.core.expression_system.expsys_base import get_expression_system
from mountainash.expressions.core.unified_visitor import UnifiedExpressionVisitor
from mountainash.relations.core.errors import CompileRequiresExecutionError
from mountainash.relations.core.execution.metadata import MetadataSession
from mountainash.relations.core.execution.preparation import ExecutionPhase
from mountainash.relations.core.execution.transport import TransportSession
from mountainash.relations.core.relation_protocols.relsys_base import get_relation_system

if TYPE_CHECKING:
    from mountainash.relations.core.execution.location import ExecutionLocation
    from mountainash.relations.core.execution.preparation import PreparedExecution
    from mountainash.relations.core.unified_visitor.relation_visitor import UnifiedRelationVisitor


class CompilationSession:
    """Use one prepared recipe and one transport scope for all native subtrees."""

    def __init__(self, prepared: PreparedExecution, *, ref_resolver_factory=None,
                 key_context=None, transport=None, metadata=None) -> None:
        self.prepared = prepared
        self.ref_resolver_factory = ref_resolver_factory
        self.key_context = key_context
        self.metadata = metadata or MetadataSession(prepared.tokens)
        self.transport = transport or TransportSession(
            prepared.tokens, execution_context=prepared.execution_context,
            context_for=prepared.context_for,
        )
        self._schema_prototypes: dict[int, Any] = {}
        self._compiled = {}
        self._root_envelope = None

    def schema_input(self, value: Any) -> Any:
        from mountainash.relations.core.execution.location import schema_prototype

        key = id(value)
        if key not in self._schema_prototypes:
            self._schema_prototypes[key] = schema_prototype(value)
        return self._schema_prototypes[key]

    @contextmanager
    def at(self, visitor: UnifiedRelationVisitor, key: str):
        previous = visitor.execution_key
        visitor.execution_key = key
        try:
            yield
        finally:
            visitor.execution_key = previous

    def _visitor(self, key: str, location: ExecutionLocation | None = None) -> UnifiedRelationVisitor:
        from mountainash.relations.core.unified_visitor import relation_visitor

        location = location if location is not None else self.prepared.locations[key]
        family = location.family
        context = self.prepared.context_for(location)
        system = get_relation_system(family)(dialect=location.dialect)
        expression_system = get_expression_system(family)(
            dialect=location.dialect, execution_context=context,
        )
        prototype = location.prototype
        if self.prepared.phase is ExecutionPhase.SCHEMA and prototype is not None:
            prototype = self.schema_input(prototype)
        expression_visitor = UnifiedExpressionVisitor(
            expression_system, input_data=prototype, execution_context=context,
        )
        resolver = None
        if self.ref_resolver_factory:
            from mountainash.relations.core.relation_nodes.extensions_mountainash import RefRelNode

            # The recorded boundary between a named plan and the ref that uses it.
            requirement, inherited, placement = None, None, None
            if isinstance(self.prepared.nodes[key], RefRelNode):
                child_key = self.prepared.inputs[key][0]
                requirement = self.prepared.transfers.get(child_key)
                placement = self.prepared.locations[child_key]
                # This plan's decisions under the ref are the named plan's own.
                inherited = {
                    f"root{other[len(child_key):]}": replace(
                        found, source_key=f"root{found.source_key[len(child_key):]}",
                    )
                    for other, found in self.prepared.transfers.items()
                    if other.startswith(f"{child_key}/")
                }
            resolver = self.ref_resolver_factory(location, requirement, inherited, placement)
        return relation_visitor.UnifiedRelationVisitor(
            system, expression_visitor, execution_context=context,
            metadata_session=self.metadata, execution=self, execution_key=key,
            key_context=self.key_context,
            ref_resolver=resolver,
        )

    def compile(self, key: str):
        identity = (id(self.prepared.nodes[key]), self.prepared.locations[key].key)
        if identity not in self._compiled:
            result = self._compile_once(key)
            if not result[0].reusable_lowering:
                return result
            self._compiled[identity] = result
        return self._compiled[identity]

    def compile_root(self):
        root_key = self.prepared.root_key
        try:
            envelope, visitor = self.compile(root_key)
            self._root_envelope = envelope
            requirement = self.prepared.transfers.get(root_key)
            if requirement is not None:
                node = self.prepared.nodes[root_key]
                envelope = self.transport.transfer(envelope, requirement)
                # The terminal consumes the root where it now lives.
                visitor = self._visitor(root_key, requirement.destination)
                self.metadata.adopt(visitor, node, envelope)
            return envelope, visitor
        finally:
            self._compiled.clear()

    def egress(self, location: ExecutionLocation, *, arrow: Any = None) -> Any:
        """The compiled root value, moved to ``location`` (a terminal representation change).

        ``arrow`` is an already-resolved logical Arrow table standing in for the
        root: it is transferred as its own source, with only the terminal
        requirement -- the compiled root's prepared transfer and residue
        discharge have already happened at logical resolution.
        """
        from mountainash.core.constants import CONST_BACKEND
        from mountainash.relations.core.execution.location import ExecutionLocation as _Location
        from mountainash.relations.core.execution.metadata import CompilationMetadata, CompiledSubtree
        from mountainash.relations.core.execution.preparation import TransferRequirement
        from mountainash.relations.core.materialization import ExecutionForm

        root_key = self.prepared.root_key
        terminal = TransferRequirement(root_key, location, requires_execution=True)
        if arrow is not None:
            source = _Location(CONST_BACKEND.NARWHALS, "narwhals-pyarrow", ExecutionForm.EAGER, "bound")
            envelope = CompiledSubtree(
                arrow, source, self.prepared.tokens.token(arrow), CompilationMetadata(),
            )
            return self.transport.transfer(envelope, terminal).value
        envelope = self._root_envelope
        if envelope is None:
            envelope, _ = self.compile(root_key)
        requirement = self.prepared.transfers.get(root_key)
        if requirement is not None:
            envelope = self.transport.transfer(envelope, requirement)
        return self.transport.transfer(envelope, terminal).value

    def _compile_once(self, key: str):
        from mountainash.core.constants import CONST_BACKEND
        from mountainash.core.lazy_imports import import_ibis_expr_ops
        
        from mountainash.relations.core.errors import UnresolvedExecutionLocationError
        from mountainash.relations.core.execution.metadata import CompiledSubtree, CompilationMetadata
        from mountainash.relations.core.relation_nodes import JoinRelNode, ReadRelNode
        from polars.exceptions import ColumnNotFoundError

        node = self.prepared.nodes[key]
        location = self.prepared.locations[key]
        if self.prepared.phase is not ExecutionPhase.SCHEMA and isinstance(node, ReadRelNode) \
                and location.family is CONST_BACKEND.IBIS and hasattr(node.dataframe, "op"):
            op = node.dataframe.op()
            if isinstance(op, import_ibis_expr_ops().InMemoryTable):
                self.transport.validate(
                    CompiledSubtree(node.dataframe, location, self.prepared.tokens.token(node), CompilationMetadata()),
                    location,
                )

        visitor = self._visitor(key)
        with self.at(visitor, key):
            try:
                value = self.prepared.nodes[key].accept(visitor)
            except ColumnNotFoundError as error:
                if self.prepared.phase is ExecutionPhase.SCHEMA:
                    self.metadata.raise_if_bounded(error)
                raise
        location = self.prepared.locations[key]
        if isinstance(self.prepared.nodes[key], JoinRelNode) and location.family is CONST_BACKEND.IBIS:
            try:
                actual = value._find_backend(use_default=False)
            except (AttributeError, ValueError) as exc:
                raise UnresolvedExecutionLocationError(
                    f"Compiled join at {key} has no selected physical binding", node_key=key,
                ) from exc
            if actual is not location.connection:
                raise UnresolvedExecutionLocationError(
                    f"Compiled join at {key} did not use its selected physical binding",
                    node_key=key,
                )
        envelope = self.metadata.capture(
            visitor, owner_key=key, location=self.prepared.locations[key], value=value,
        )
        from dataclasses import replace

        envelope = replace(
            envelope,
            reusable_lowering=visitor.reusable_lowering and visitor.expr_visitor.reusable_lowering,
            repeatable_result=visitor.repeatable_result and visitor.expr_visitor.repeatable_result,
        )
        from mountainash.relations.core.relation_nodes.extensions_mountainash import RefRelNode

        if isinstance(node, RefRelNode) and self.ref_resolver_factory is not None:
            from dataclasses import replace

            # A ref is an alias of its named source, not a new materialization.
            # Keep the captured metadata but reuse the source's transport identity.
            captured = visitor.ref_resolver.envelope(node.name)
            envelope = replace(
                envelope, source_token=captured.source_token,
                reusable_lowering=envelope.reusable_lowering and captured.reusable_lowering,
                repeatable_result=envelope.repeatable_result and captured.repeatable_result,
            )
        return envelope, visitor

    def _discharge_before_loss(self, parent: UnifiedRelationVisitor, child_key: str, envelope):
        """Execute source-owned checks before an output projection loses their markers."""
        from mountainash.relations.core.structured_lineage import propagate_owned_residue

        checks = envelope.metadata.owned_checks
        if not checks:
            return envelope
        owner = self.prepared.nodes[parent.execution_key]
        if len(self.prepared.inputs[parent.execution_key]) != 1:
            return envelope
        try:
            propagate_owned_residue(owner, [checks])
        except ValueError:
            if self.prepared.phase is not ExecutionPhase.EXECUTE:
                raise CompileRequiresExecutionError(
                    f"Boundary {child_key} must discharge a source residue check; use .collect()",
                    node_key=child_key,
                ) from None
            # The parent must consume exactly the checked rows, not rerun the
            # original deferred source after the marker has been dropped.
            return self.transport.discharge(envelope)
        return envelope

    def child(self, visitor: UnifiedRelationVisitor, node: Any):
        from mountainash.relations.core.relation_nodes import ReadRelNode, SetRelNode
        from mountainash.core.constants import CONST_BACKEND

        parent_key = visitor.execution_key
        keys = self.prepared.inputs[parent_key]
        key = next((candidate for candidate in keys
                    if self.prepared.nodes[candidate] is node), None)
        if key is None:
            raise RuntimeError(f"Unprepared child of {parent_key}")
        if (self.prepared.phase is not ExecutionPhase.SCHEMA
                and isinstance(node, ReadRelNode) and isinstance(node.dataframe, (dict, list, tuple))):
            from mountainash.relations.core.execution.metadata import CompiledSubtree, CompilationMetadata

            raw = node.dataframe
            if not isinstance(raw, dict) and raw and not isinstance(raw[0], dict):
                raise TypeError("Expected a mapping or a sequence of mappings")
            from mountainash.pydata.ingress.pydata_ingress import repeatable_ingress_value

            destination = self.prepared.locations[parent_key]
            repeatable = repeatable_ingress_value(raw)
            source = CompiledSubtree(
                raw, self.prepared.locations[key], self.prepared.tokens.token(node),
                CompilationMetadata(), reusable_lowering=repeatable, repeatable_result=repeatable,
            )
            envelope = self.transport.transfer(source, self.prepared.transfers[key])
            visitor.reusable_lowering &= envelope.reusable_lowering
            visitor.repeatable_result &= envelope.repeatable_result
            if destination.family is CONST_BACKEND.POLARS:
                from mountainash.core.lowering_reuse import REPEATABLE

                visitor.record_lowering(visitor.backend.read, REPEATABLE)
                return visitor.backend.read(envelope.value)
            return envelope.value
        envelope, _ = self.compile(key)
        requirement = self.prepared.transfers.get(key)
        if requirement is not None:
            envelope = self.transport.transfer(envelope, requirement)
        envelope = self._discharge_before_loss(visitor, key, envelope)
        if isinstance(self.prepared.nodes[parent_key], SetRelNode) and envelope.metadata.owned_checks:
            # A set cannot align inputs while one carries a private residue
            # marker. Check the source snapshot before stripping those columns.
            if self.prepared.phase is not ExecutionPhase.EXECUTE:
                raise CompileRequiresExecutionError(
                    f"Boundary {key} must discharge a source residue check; use .collect()",
                    node_key=key,
                )
            # discharge() uses the source enrichment path, which removes
            # checked markers from the returned native snapshot itself.
            envelope = self.transport.discharge(envelope)
        visitor.reusable_lowering &= envelope.reusable_lowering
        visitor.repeatable_result &= envelope.repeatable_result
        self.metadata.adopt(visitor, node, envelope)
        return envelope.value

    def operands(self, visitor: UnifiedRelationVisitor, owner_key: str) -> tuple[Any, ...]:
        return tuple(self.child(visitor, self.prepared.nodes[key])
                     for key in self.prepared.inputs[owner_key])

    def close(self, *, release_owned: bool) -> None:
        try:
            self.transport.close(release_owned=release_owned)
        finally:
            self._compiled.clear()
            self._root_envelope = None
