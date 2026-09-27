"""Execution-scoped envelopes for native values and source-owned metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

from mountainash.conform.diagnostics import OperationDiagnosticTrace
from mountainash.conform.structured_transport import freeze_structured_field_plans

if TYPE_CHECKING:
    from mountainash.conform.structured_transport import StructuredFieldPlanMap
    from mountainash.relations.core.execution.location import ExecutionLocation, IdentityTokens
    from mountainash.relations.core.relation_nodes import RelationNode


@dataclass(frozen=True)
class OwnedResidue:
    check: Any
    owner_key: str
    source_location: ExecutionLocation


@dataclass(frozen=True)
class CompilationMetadata:
    diagnostic_records: tuple = ()
    owned_checks: tuple[OwnedResidue, ...] = ()
    drift_reports: tuple = ()
    structured_field_plans: StructuredFieldPlanMap = field(
        default_factory=lambda: MappingProxyType({})
    )
    resources: tuple = ()


@dataclass(frozen=True)
class CompiledSubtree:
    value: Any
    location: ExecutionLocation
    source_token: int
    metadata: CompilationMetadata


def _unique_identity(items: Any) -> tuple:
    seen: set[int] = set()
    result = []
    for item in items:
        if id(item) not in seen:
            seen.add(id(item))
            result.append(item)
    return tuple(result)


class MetadataSession:
    """Share conform identities across otherwise independent native visitors."""

    def __init__(self, tokens: IdentityTokens) -> None:
        self.tokens = tokens

    def conform_id(self, owner: object) -> str:
        return f"conform:{self.tokens.token(owner)}"

    def capture(
        self, visitor: Any, *, owner_key: str, location: ExecutionLocation, value: Any,
    ) -> CompiledSubtree:
        records = _unique_identity(
            record for trace in visitor.diagnostic_traces.values() for record in trace.records
        )
        local_checks = (
            OwnedResidue(check, owner_key, location) for check in visitor.residue_checks
        )
        checks = _unique_identity_owned(
            (*getattr(visitor, "owned_residue_checks", ()), *local_checks)
        )
        metadata = CompilationMetadata(
            diagnostic_records=records,
            owned_checks=checks,
            drift_reports=_unique_identity(visitor.drift_reports),
            structured_field_plans=freeze_structured_field_plans(visitor.structured_field_plans),
            resources=tuple(getattr(visitor, "owned_resources", ())),
        )
        # The native value may be the same object for two distinct compilations.
        return CompiledSubtree(value, location, self.tokens.token(object()), metadata)

    def adopt(self, visitor: Any, child_node: RelationNode, child: CompiledSubtree) -> None:
        visitor._structured_plans_by_node[id(child_node)] = child.metadata.structured_field_plans
        checks_by_node = getattr(visitor, "_owned_checks_by_node", None)
        if checks_by_node is None:
            checks_by_node = visitor._owned_checks_by_node = {}
        checks_by_node[id(child_node)] = child.metadata.owned_checks
        seen_records = {id(record) for trace in visitor.diagnostic_traces.values()
                        for record in trace.records}
        for record in child.metadata.diagnostic_records:
            if id(record) in seen_records:
                continue
            seen_records.add(id(record))
            key = (record.backend_family, record.dialect)
            visitor.diagnostic_traces.setdefault(key, OperationDiagnosticTrace()).extend((record,))
        checks = getattr(visitor, "owned_residue_checks", None)
        if checks is None:
            checks = visitor.owned_residue_checks = []
        seen_checks = {id(owned.check) for owned in checks}
        for owned in child.metadata.owned_checks:
            if id(owned.check) not in seen_checks:
                checks.append(owned)
                seen_checks.add(id(owned.check))
        seen_drifts = {id(drift) for drift in visitor.drift_reports}
        for drift in child.metadata.drift_reports:
            if id(drift) not in seen_drifts:
                visitor.drift_reports.append(drift)
                seen_drifts.add(id(drift))
        resources = getattr(visitor, "owned_resources", None)
        if resources is None:
            resources = visitor.owned_resources = []
        known = {id(resource) for resource in resources}
        for resource in child.metadata.resources:
            if id(resource) not in known:
                resources.append(resource)
                known.add(id(resource))


def _unique_identity_owned(checks: Any) -> tuple[OwnedResidue, ...]:
    seen: set[int] = set()
    result = []
    for owned in checks:
        if id(owned.check) not in seen:
            seen.add(id(owned.check))
            result.append(owned)
    return tuple(result)
