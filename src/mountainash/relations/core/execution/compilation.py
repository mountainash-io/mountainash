"""Contextual compilation through the existing relation and expression visitors."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

from mountainash.expressions.core.expression_system.expsys_base import get_expression_system
from mountainash.expressions.core.unified_visitor import UnifiedExpressionVisitor
from mountainash.relations.core.errors import CompileRequiresExecutionError
from mountainash.relations.core.execution.metadata import MetadataSession
from mountainash.relations.core.execution.preparation import ExecutionPhase
from mountainash.relations.core.execution.transport import TransportSession
from mountainash.relations.core.relation_protocols.relsys_base import get_relation_system

if TYPE_CHECKING:
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

    @contextmanager
    def at(self, visitor: UnifiedRelationVisitor, key: str):
        previous = visitor.execution_key
        visitor.execution_key = key
        try:
            yield
        finally:
            visitor.execution_key = previous

    def _visitor(self, key: str) -> UnifiedRelationVisitor:
        from mountainash.relations.core.unified_visitor import relation_visitor

        location = self.prepared.locations[key]
        family = location.family
        context = self.prepared.context_for(location)
        system = get_relation_system(family)(dialect=location.dialect)
        expression_system = get_expression_system(family)(
            dialect=location.dialect, execution_context=context,
        )
        expression_visitor = UnifiedExpressionVisitor(
            expression_system, input_data=location.prototype, execution_context=context,
        )
        resolver = self.ref_resolver_factory(location) if self.ref_resolver_factory else None
        return relation_visitor.UnifiedRelationVisitor(
            system, expression_visitor, execution_context=context,
            metadata_session=self.metadata, execution=self, execution_key=key,
            key_context=self.key_context,
            ref_resolver=resolver,
        )

    def compile(self, key: str):
        from mountainash.core.constants import CONST_BACKEND
        from mountainash.core.lazy_imports import import_ibis_expr_ops
        from mountainash.core.transit import BoundaryKey, transit_call
        from mountainash.relations.core.errors import UnresolvedExecutionLocationError
        from mountainash.relations.core.execution.metadata import CompiledSubtree, CompilationMetadata
        from mountainash.relations.core.execution.preparation import TransferRequirement
        from mountainash.relations.core.relation_nodes import JoinRelNode, ReadRelNode

        node = self.prepared.nodes[key]
        location = self.prepared.locations[key]
        if isinstance(node, ReadRelNode) and location.dialect == "ibis-sqlite" \
                and hasattr(node.dataframe, "op"):
            op = node.dataframe.op()
            if isinstance(op, import_ibis_expr_ops().InMemoryTable):
                payload = transit_call(
                    BoundaryKey.IBIS_MEMORY_PAYLOAD_TO_ARROW,
                    op.data.to_pyarrow, node.dataframe.schema(),
                )
                source = CompiledSubtree(payload, location, self.prepared.tokens.token(node), CompilationMetadata())
                requirement = TransferRequirement(key, location, "ibis_memory_ibis", False)
                self.transport._validate_ibis_storage(source, requirement, payload)

        visitor = self._visitor(key)
        with self.at(visitor, key):
            value = self.prepared.nodes[key].accept(visitor)
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
        from mountainash.relations.core.relation_nodes.extensions_mountainash import RefRelNode

        if isinstance(node, RefRelNode) and self.ref_resolver_factory is not None:
            from dataclasses import replace

            # A ref is an alias of its named source, not a new materialization.
            # Keep the captured metadata but reuse the source's transport identity.
            envelope = replace(envelope, source_token=visitor.ref_resolver.envelope(node.name).source_token)
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
        from mountainash.relations.core.materialization import (
            coerce_to_ibis, coerce_to_narwhals, coerce_to_polars,
        )
        from mountainash.core.constants import CONST_BACKEND

        parent_key = visitor.execution_key
        keys = self.prepared.inputs[parent_key]
        key = next((candidate for candidate in keys
                    if self.prepared.nodes[candidate] is node), None)
        if key is None:
            raise RuntimeError(f"Unprepared child of {parent_key}")
        if isinstance(node, ReadRelNode) and isinstance(node.dataframe, (dict, list, tuple)):
            from mountainash.relations.core.execution.metadata import CompiledSubtree, CompilationMetadata
            from mountainash.relations.core.execution.preparation import TransferRequirement

            raw = node.dataframe
            if not isinstance(raw, dict) and raw and not isinstance(raw[0], dict):
                raise TypeError("Expected a mapping or a sequence of mappings")
            destination = self.prepared.locations[parent_key]
            if destination.family is CONST_BACKEND.IBIS:
                source = CompiledSubtree(raw, self.prepared.locations[key],
                                         self.prepared.tokens.token(node), CompilationMetadata())
                requirement = TransferRequirement(key, destination, "mapping_to_ibis", False)
                value = self.transport._adapt(source, requirement, coerce_to_ibis,
                                              destination.prototype, raw)
            elif destination.family is CONST_BACKEND.NARWHALS:
                value = coerce_to_narwhals(destination.prototype, raw)
            else:
                value = coerce_to_polars(destination.prototype, raw)
                value = visitor.backend.read(value)
            return value
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
        self.metadata.adopt(visitor, node, envelope)
        return envelope.value

    def operands(self, visitor: UnifiedRelationVisitor, owner_key: str) -> tuple[Any, ...]:
        return tuple(self.child(visitor, self.prepared.nodes[key])
                     for key in self.prepared.inputs[owner_key])

    def close(self, *, release_owned: bool) -> None:
        self.transport.close(release_owned=release_owned)
