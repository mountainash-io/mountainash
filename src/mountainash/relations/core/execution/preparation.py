"""Nonexecuting, occurrence-based placement and transfer recipe."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Any

from mountainash.core.capabilities.policy import (
    _CapabilityTarget, _prepare_capability_context, _resolve_policy,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.relations.core.errors import (
    CompileRequiresExecutionError, ConflictingExecutionTargetError,
    UnresolvedExecutionLocationError, UnsupportedRelationTransportError,
)
from mountainash.relations.core.execution.capabilities import preflight_capabilities
from mountainash.relations.core.execution.location import (
    ExecutionLocation, IdentityTokens, LocationResolver,
)
from mountainash.relations.core.materialization import ExecutionForm
from mountainash.relations.core.relation_nodes import JoinRelNode, ReadRelNode, SetRelNode
from mountainash.relations.core.relation_nodes.extensions_mountainash import RefRelNode, ResourceReadRelNode

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from mountainash.relations.core.relation_nodes import RelationNode


class ExecutionPhase(Enum):
    COMPILE = auto()
    EXPLAIN = auto()
    EXECUTE = auto()


@dataclass(frozen=True)
class TransferRequirement:
    source_key: str
    destination: ExecutionLocation
    route: str
    requires_execution: bool


@dataclass
class PreparedExecution:
    root_key: str
    nodes: Mapping[str, RelationNode]
    locations: Mapping[str, ExecutionLocation]
    inputs: Mapping[str, tuple[str, ...]]
    transfers: Mapping[str, TransferRequirement]
    phase: ExecutionPhase
    tokens: IdentityTokens
    execution_context: Any = None
    _policy: Any = field(default=None, repr=False)
    _contexts: dict[tuple, Any] = field(default_factory=dict, repr=False)
    _package_versions: dict[str, str | None] = field(default_factory=dict, repr=False)

    def context_for(self, location: ExecutionLocation) -> Any:
        if location.capability_identity is None:
            return None
        if location.key not in self._contexts:
            owner = location.connection if location.connection is not None else location.prototype
            if owner is None:
                owner = self.nodes[self.root_key]
            prior = self.execution_context
            if (prior is not None and prior.target.identity == location.capability_identity
                    and prior.target.owner is owner):
                context = prior
            else:
                context = _prepare_capability_context(
                    self._policy,
                    _CapabilityTarget(location.capability_identity, owner),
                    package_versions=self._package_versions,
                )
            self._contexts[location.key] = context
        return self._contexts[location.key]


def _label(location: ExecutionLocation) -> str:
    binding = "unresolved binding" if location.family is CONST_BACKEND.IBIS and location.binding != "bound" else location.binding
    return f"{location.dialect or (location.family.value if location.family else 'unknown')} ({binding})"


def _unsupported(key: str, source: ExecutionLocation, target: ExecutionLocation) -> UnsupportedRelationTransportError:
    return UnsupportedRelationTransportError(
        f"No declared transport for {key}: {_label(source)} -> {_label(target)}",
        boundary_key=None, source_family=source.family.value if source.family else None,
        source_dialect=source.dialect,
        destination_family=target.family.value if target.family else None,
        destination_dialect=target.dialect,
        source_type="RelationNode", route="unsupported", reason="no declared adapter",
    )


def _route(
    key: str, source: ExecutionLocation, target: ExecutionLocation, *,
    derived: bool, raw_ingress: bool = False,
) -> TransferRequirement | None:
    # Polars read() produces a lazy compiled plan even for an eager native leaf.
    compiled_form = ExecutionForm.LAZY if source.family is CONST_BACKEND.POLARS else source.form
    if source.family == target.family and source.dialect == target.dialect \
            and (source.family is not CONST_BACKEND.IBIS or source.connection_token == target.connection_token):
        return None
    if target.family is CONST_BACKEND.NARWHALS and target.form is ExecutionForm.LAZY:
        raise _unsupported(key, source, target)
    if source.family is CONST_BACKEND.IBIS and source.binding == "memory" \
            and target.family is CONST_BACKEND.IBIS:
        return TransferRequirement(key, target, "ibis_memory_ibis", derived)
    if source.family is CONST_BACKEND.IBIS and target.family is CONST_BACKEND.IBIS:
        return TransferRequirement(key, target, "ibis_arrow_ibis", True)
    if source.family is CONST_BACKEND.IBIS:
        route = "ibis_to_polars" if target.family is CONST_BACKEND.POLARS else "ibis_to_narwhals"
        return TransferRequirement(key, target, route, True)
    if target.family is CONST_BACKEND.IBIS:
        if raw_ingress:
            return TransferRequirement(key, target, "mapping_to_ibis", False)
        route = "polars_to_ibis" if source.family is CONST_BACKEND.POLARS else "narwhals_to_ibis"
        return TransferRequirement(key, target, route, compiled_form is not ExecutionForm.EAGER or derived)
    if source.family is CONST_BACKEND.NARWHALS and target.family is CONST_BACKEND.NARWHALS:
        return TransferRequirement(key, target, "narwhals_dialect",
                                   derived or compiled_form is not ExecutionForm.EAGER)
    if target.family not in (CONST_BACKEND.POLARS, CONST_BACKEND.NARWHALS) or source.family is None:
        raise _unsupported(key, source, target)
    route = "to_polars" if target.family is CONST_BACKEND.POLARS else "to_narwhals"
    return TransferRequirement(key, target, route, derived or compiled_form is not ExecutionForm.EAGER)


def prepare_execution(
    root: RelationNode, *, phase: ExecutionPhase, backend: str | None = None,
    identity_resolver: Callable[[str], RelationNode] | None = None,
    execution_context: Any = None,
    tokens: IdentityTokens | None = None,
    binding: ExecutionLocation | None = None,
) -> PreparedExecution:
    """Resolve the entire graph, preflight all gates, then reject unsafe phases."""
    policy = execution_context.policy if execution_context is not None else _resolve_policy()
    tokens = tokens if tokens is not None else IdentityTokens()
    resolver = LocationResolver(tokens, identity_resolver=identity_resolver)
    nodes: dict[str, RelationNode] = {}
    locations: dict[str, ExecutionLocation] = {}
    inputs: dict[str, tuple[str, ...]] = {}
    transfers: dict[str, TransferRequirement] = {}
    active_refs: set[str] = set()

    def resource_only(node: RelationNode, refs: frozenset[str] = frozenset()) -> bool:
        if isinstance(node, ResourceReadRelNode):
            return True
        if isinstance(node, RefRelNode):
            if identity_resolver is None or node.name in refs:
                return False
            try:
                resolved = identity_resolver(node.name)
            except KeyError:
                return False  # The location resolver reports the typed missing-ref error.
            return resource_only(resolved, refs | {node.name})
        children = node.children()
        return len(children) == 1 and resource_only(children[0], refs)

    requested_family = None
    if backend is not None:
        try:
            requested_family = CONST_BACKEND(backend.lower()) if isinstance(backend, str) else CONST_BACKEND(backend)
        except (AttributeError, ValueError) as exc:
            raise ValueError(f"unknown backend: {backend!r}") from exc
    # A resource without a physical Ibis peer has its own declared/default
    # Polars read location. An Ibis family override alone is not a binding;
    # retain the resource's existing fallback instead of manufacturing one.
    resource_ibis_fallback = requested_family is CONST_BACKEND.IBIS and resource_only(root)

    def walk(node: RelationNode, key: str, binding: ExecutionLocation | None = None) -> None:
        location = resolver.resolve(node, binding=binding)
        if isinstance(node, JoinRelNode) and requested_family is not None and node.execute_on is not None:
            if location.family is not None and requested_family is not location.family:
                raise ConflictingExecutionTargetError(
                    f"Explicit target at {key} is {_label(location)}, not {requested_family.value}",
                    node_key=key, source=requested_family.value, destination=_label(location),
                )
        if (key == "root" and requested_family is not None
                and requested_family is not location.family and not resource_ibis_fallback):
            # A terminal override is a root placement request, not a source
            # identity. Descendants retain their own native dialects.
            if requested_family is CONST_BACKEND.IBIS:
                location = ExecutionLocation(requested_family, None, ExecutionForm.DEFERRED, "unresolved")
            elif requested_family is CONST_BACKEND.POLARS:
                location = ExecutionLocation(requested_family, "polars", ExecutionForm.LAZY, "bound")
            else:
                location = ExecutionLocation(requested_family, None, ExecutionForm.EAGER, "bound")
        nodes[key] = node
        locations[key] = location
        if isinstance(node, RefRelNode) and identity_resolver is not None:
            if node.name in active_refs:
                raise UnresolvedExecutionLocationError(f"Cyclic relation reference {node.name!r}", node_key=key)
            active_refs.add(node.name)
            try:
                child = identity_resolver(node.name)
                child_key = f"{key}/ref/{node.name}"
                walk(child, child_key, binding=location)
                inputs[key] = (child_key,)
            finally:
                active_refs.remove(node.name)
            return
        if isinstance(node, JoinRelNode):
            children = (("left", node.left), ("right", node.right))
        elif isinstance(node, SetRelNode):
            children = tuple((f"inputs/{i}", child) for i, child in enumerate(node.inputs))
        else:
            children = tuple(("input" if len(node.children()) == 1 else f"inputs/{i}", child)
                             for i, child in enumerate(node.children()))
        child_keys = tuple(f"{key}/{part}" for part, _ in children)
        inputs[key] = child_keys
        for (part, child), child_key in zip(children, child_keys):
            # Only connectionless local data may inherit the consuming binding.
            child_binding = location if location.family is CONST_BACKEND.IBIS else None
            walk(child, child_key, binding=child_binding)
        if isinstance(node, (JoinRelNode, SetRelNode)) or key == "root" and child_keys:
            for child_key in child_keys:
                source = locations[child_key]
                child = nodes[child_key]
                raw_ingress = isinstance(child, ReadRelNode) and (
                    isinstance(child.dataframe, dict) or
                    isinstance(child.dataframe, (list, tuple)) and (
                        not child.dataframe or isinstance(child.dataframe[0], dict)
                    )
                )
                requirement = _route(child_key, source, location,
                                     derived=not isinstance(child, ReadRelNode), raw_ingress=raw_ingress)
                if requirement is not None:
                    transfers[child_key] = requirement

    walk(root, "root", binding=binding)
    prepared = PreparedExecution("root", nodes, locations, inputs, transfers, phase, tokens,
                                 execution_context, policy)
    # Gate every reachable occurrence before phase rejection or any transfer.
    preflight_capabilities(prepared)
    if phase is not ExecutionPhase.EXPLAIN:
        for key, occurrence in locations.items():
            if occurrence.family is CONST_BACKEND.IBIS and occurrence.binding == "unbound":
                raise UnresolvedExecutionLocationError(
                    f"Unbound Ibis source at {key} requires an explicit binding",
                    node_key=key, source=_label(occurrence),
                )
    selected = locations["root"]
    if phase is not ExecutionPhase.EXPLAIN and selected.family is CONST_BACKEND.IBIS \
            and selected.binding != "bound":
        raise UnresolvedExecutionLocationError(
            f"Selected execution location at root has unresolved Ibis binding: {_label(selected)}",
            node_key="root", destination=_label(selected),
        )
    if phase is ExecutionPhase.COMPILE:
        for requirement in transfers.values():
            if requirement.requires_execution:
                raise CompileRequiresExecutionError(
                    f"Boundary {requirement.source_key} requires execution; use .collect()",
                    node_key=requirement.source_key, destination=_label(requirement.destination),
                )
    return prepared


def render_execution(prepared: PreparedExecution) -> str:
    """Render safe placement labels without touching native rows or SQL."""
    lines = [f"{key}: {type(node).__name__} on {_label(prepared.locations[key])}"
             for key, node in prepared.nodes.items()]
    lines.extend(f"transfer {key}: {requirement.route} -> {_label(requirement.destination)}"
                 for key, requirement in prepared.transfers.items())
    return "\n".join(lines)
