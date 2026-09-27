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
from mountainash.relations.core.unified_visitor.relation_visitor import UnifiedRelationVisitor

if TYPE_CHECKING:
    from mountainash.relations.core.execution.preparation import PreparedExecution


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
        return UnifiedRelationVisitor(
            system, expression_visitor, execution_context=context,
            metadata_session=self.metadata, execution=self, execution_key=key,
            key_context=self.key_context,
            ref_resolver=(self.ref_resolver_factory(location) if self.ref_resolver_factory else None),
        )

    def compile(self, key: str):
        from mountainash.core.constants import CONST_BACKEND
        from mountainash.relations.core.errors import UnresolvedExecutionLocationError
        from mountainash.relations.core.relation_nodes import JoinRelNode

        visitor = self._visitor(key)
        with self.at(visitor, key):
            value = visitor.visit(self.prepared.nodes[key])
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
            propagate_owned_residue(
                owner, [checks], backend=parent.backend.backend_type,
            )
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
        from mountainash.relations.core.relation_nodes import ReadRelNode
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
            raw = node.dataframe
            if not isinstance(raw, dict) and raw and not isinstance(raw[0], dict):
                raise TypeError("Expected a mapping or a sequence of mappings")
            destination = self.prepared.locations[parent_key]
            if destination.family is CONST_BACKEND.IBIS:
                value = coerce_to_ibis(destination.prototype, raw)
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
        self.metadata.adopt(visitor, node, envelope)
        return envelope.value

    def operands(self, visitor: UnifiedRelationVisitor, owner_key: str) -> tuple[Any, ...]:
        return tuple(self.child(visitor, self.prepared.nodes[key])
                     for key in self.prepared.inputs[owner_key])

    def close(self, *, release_owned: bool) -> None:
        self.transport.close(release_owned=release_owned)
