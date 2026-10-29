"""Nonexecuting, occurrence-based placement and transfer recipe."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum, auto
from typing import TYPE_CHECKING, Any

from mountainash.core.capabilities.policy import (
    _prepare_capability_context, _resolve_policy,
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
    SCHEMA = auto()
    EXPLAIN = auto()
    EXECUTE = auto()


@dataclass(frozen=True)
class TransferRequirement:
    source_key: str
    destination: ExecutionLocation
    requires_execution: bool
    owned: bool = False


@dataclass
class PreparedExecution:
    root_key: str
    nodes: Mapping[str, RelationNode]
    locations: Mapping[str, ExecutionLocation]
    inputs: Mapping[str, tuple[str, ...]]
    transfers: dict[str, TransferRequirement]
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
            target = location.capability_target(default_owner=self.nodes[self.root_key])
            prior = self.execution_context
            if (prior is not None and prior.target.identity == target.identity
                    and prior.target.owner is target.owner):
                context = prior
            else:
                context = _prepare_capability_context(
                    self._policy, target, package_versions=self._package_versions,
                )
            self._contexts[location.key] = context
        return self._contexts[location.key]


def _label(location: ExecutionLocation) -> str:
    binding = "unresolved binding" if location.family is CONST_BACKEND.IBIS and location.binding != "bound" else location.binding
    return f"{location.dialect or (location.family.value if location.family else 'unknown')} ({binding})"


def _compiled_form(location: ExecutionLocation) -> ExecutionLocation:
    """Polars compiles every plan lazily, whatever its leaf's eager/lazy form."""
    if location.family is CONST_BACKEND.POLARS and location.form is not ExecutionForm.LAZY:
        return replace(location, form=ExecutionForm.LAZY)
    return location


def _requirement(
    key: str, source: ExecutionLocation, target: ExecutionLocation, *,
    derived: bool, raw_ingress: bool = False, memory_payload: bool = False,
) -> TransferRequirement | None:
    """The boundary a value crosses to reach ``target``; ``None`` when it needs none."""
    target = _compiled_form(target)
    # Polars read() produces a lazy compiled plan even for an eager native leaf.
    compiled_form = ExecutionForm.LAZY if source.family is CONST_BACKEND.POLARS else source.form
    if source.family == target.family and source.dialect == target.dialect \
            and (source.family is not CONST_BACKEND.IBIS or source.connection_token == target.connection_token):
        return None
    if target.family is CONST_BACKEND.NARWHALS and target.form is ExecutionForm.LAZY:
        # The destination family decides which lazy implementations it can
        # produce; preparation never exports to ask it.
        from mountainash.relations.core.execution.transport import import_refusal
        from mountainash.relations.core.relation_protocols.relsys_base import get_relation_system

        try:
            get_relation_system(target.family)().check_import(_no_payload, location=target)
        except ValueError as exc:
            raise import_refusal(source, target, exc) from exc
    if source.family is CONST_BACKEND.IBIS and source.binding == "memory" \
            and target.family is CONST_BACKEND.IBIS:
        return TransferRequirement(key, target, derived)
    if source.family is CONST_BACKEND.IBIS and source.binding == "memory" \
            and target.family in (CONST_BACKEND.POLARS, CONST_BACKEND.NARWHALS) \
            and memory_payload:
        return TransferRequirement(key, target, False)
    if source.family is CONST_BACKEND.IBIS:
        return TransferRequirement(key, target, True)
    if target.family is CONST_BACKEND.IBIS:
        if raw_ingress:
            return TransferRequirement(key, target, False)
        return TransferRequirement(key, target, compiled_form is not ExecutionForm.EAGER or derived)
    if target.family not in (CONST_BACKEND.POLARS, CONST_BACKEND.NARWHALS) or source.family is None:
        raise _refusal(source, target)
    return TransferRequirement(key, target, derived or compiled_form is not ExecutionForm.EAGER)


def _no_payload() -> Any:
    raise AssertionError("preparation-time check_import must not request the payload")


def _refusal(source: ExecutionLocation, target: ExecutionLocation) -> UnsupportedRelationTransportError:
    from mountainash.relations.core.execution.transport import import_refusal

    return import_refusal(source, target, None)


def _is_raw_read(node: ReadRelNode) -> bool:
    data = node.dataframe
    return isinstance(data, dict) or (
        isinstance(data, (list, tuple)) and (not data or isinstance(data[0], dict))
    )


def _is_borrowed_leaf(node: Any, location: ExecutionLocation, resolver: LocationResolver) -> bool:
    """A native in-memory payload whose prepared location borrows a connection.

    The single provenance predicate for anchor planning; ``location.binding``
    alone is descriptive and cannot distinguish borrowed from physical.
    """
    if isinstance(node, ReadRelNode):
        return resolver._read(node.dataframe).binding == "memory" and location.binding == "bound"
    if isinstance(node, ResourceReadRelNode):
        return location.family is CONST_BACKEND.IBIS and location.binding == "memory"
    return False


def _plan_anchors(p: PreparedExecution, borrowed: frozenset[str]) -> None:
    """Set owned=True on at most one transfer into the root connection; manufacture it for a borrowed anchor."""
    root_key = p.root_key
    root = p.transfers[root_key].destination if root_key in p.transfers else p.locations[root_key]
    if root.family is not CONST_BACKEND.IBIS or root.binding != "bound":
        return
    token = root.connection_token
    candidates: list[str] = []
    survives = False

    def visit(key: str) -> None:
        nonlocal survives
        req = p.transfers.get(key)
        if req is not None and req.destination.connection_token == token:
            candidates.append(key)  # crossing boundary: its subtree does not survive
            return
        if key in borrowed:
            candidates.append(key)
            return
        children = p.inputs.get(key, ())
        if not children:
            loc = p.locations[key]
            if loc.binding == "bound" and loc.connection_token == token:
                survives = True
            return
        for child in children:
            visit(child)

    visit(root_key)
    if survives or not candidates:
        return
    anchor = candidates[0]
    req = p.transfers.get(anchor)
    destination = req.destination if req else root
    p.transfers[anchor] = TransferRequirement(anchor, destination, requires_execution=True, owned=True)


def _apply_target(selected: ExecutionLocation, requested: ExecutionLocation) -> ExecutionLocation:
    """Overlay only the dimensions a terminal target actually specifies."""
    if requested.family is not selected.family:
        return requested
    if requested.connection is not None:
        return requested
    if requested.dialect is not None and requested.dialect != selected.dialect:
        return requested
    return selected


def _conflicts(explicit: ExecutionLocation, requested: ExecutionLocation) -> bool:
    """Whether a terminal target contradicts an explicit join placement."""
    if explicit.family is None:
        return False
    if requested.family is not explicit.family:
        return True
    if requested.dialect is not None and requested.dialect != explicit.dialect:
        return True
    return requested.connection_token is not None and requested.connection_token != explicit.connection_token


def prepare_execution(
    root: RelationNode, *, phase: ExecutionPhase, target: Any = None,
    identity_resolver: Callable[[str], RelationNode] | None = None,
    execution_context: Any = None,
    tokens: IdentityTokens | None = None,
    binding: ExecutionLocation | None = None,
    inherited: Mapping[str, TransferRequirement] | None = None,
) -> PreparedExecution:
    """Resolve the entire graph, preflight all gates, then reject unsafe phases.

    ``target`` is the public execution-target vocabulary (family, dialect
    identifier or Ibis connection); see ``LocationResolver.resolve_target``.

    ``inherited`` are transfer decisions an enclosing plan already made for
    this plan's occurrences (keyed as this plan's own); they replace what
    preparation would record for the same keys.
    """
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

    def bare_memory(node: RelationNode, refs: frozenset[str] = frozenset()) -> bool:
        if isinstance(node, RefRelNode) and identity_resolver is not None and node.name not in refs:
            return bare_memory(identity_resolver(node.name), refs | {node.name})
        if not isinstance(node, ReadRelNode):
            return False
        source = resolver.resolve(node)
        if source.family is not CONST_BACKEND.IBIS or source.binding != "memory":
            return False
        from mountainash.core.lazy_imports import import_ibis_expr_ops

        return isinstance(node.dataframe.op(), import_ibis_expr_ops().InMemoryTable)

    requested = resolver.resolve_target(target)
    # A resource without a physical Ibis peer has its own declared/default
    # Polars read location. An Ibis family override alone is not a binding;
    # retain the resource's existing fallback instead of manufacturing one.
    resource_ibis_fallback = (
        requested is not None and requested.family is CONST_BACKEND.IBIS
        and requested.connection is None and resource_only(root)
    )

    resolved: dict[str, ExecutionLocation] = {}

    def walk(node: RelationNode, key: str, binding: ExecutionLocation | None = None) -> None:
        location = resolver.resolve(node, binding=binding)
        resolved[key] = location  # before any terminal-target overlay
        if isinstance(node, JoinRelNode) and requested is not None and node.execute_on is not None:
            if _conflicts(location, requested):
                raise ConflictingExecutionTargetError(
                    f"Explicit target at {key} is {_label(location)}, not {_label(requested)}",
                    node_key=key, source=_label(requested), destination=_label(location),
                )
        if key == "root" and requested is not None and not resource_ibis_fallback:
            # A terminal target is a root placement request, not a source
            # identity. Descendants retain their own native dialects.
            retargeted = _apply_target(location, requested)
            if isinstance(node, ReadRelNode) and retargeted is not location:
                # A native read is compiled where it lives; the move to the
                # target is a recorded boundary, not a relabelling.
                requirement = _requirement(key, location, retargeted, derived=False,
                                           raw_ingress=_is_raw_read(node),
                                           memory_payload=bare_memory(node))
                if requirement is not None:
                    transfers[key] = requirement
            else:
                location = retargeted
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
                requirement = _requirement(child_key, locations[child_key], location,
                                           derived=not isinstance(child, ReadRelNode),
                                           memory_payload=bare_memory(child))
                if requirement is not None:
                    transfers[child_key] = requirement
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
            child_binding = location if location.family in (CONST_BACKEND.IBIS, CONST_BACKEND.NARWHALS) else None
            walk(child, child_key, binding=child_binding)
        boundary = isinstance(node, (JoinRelNode, SetRelNode)) or key == "root"
        for child_key in child_keys:
            source = locations[child_key]
            child = nodes[child_key]
            raw_ingress = isinstance(child, ReadRelNode) and _is_raw_read(child)
            if not boundary and not raw_ingress:
                continue
            requirement = _requirement(child_key, source, location,
                                       derived=not isinstance(child, ReadRelNode), raw_ingress=raw_ingress,
                                       memory_payload=bare_memory(child))
            if requirement is None and raw_ingress:
                # Raw rows always cross into the parent's native form.
                requirement = TransferRequirement(child_key, _compiled_form(location), False)
            if requirement is not None:
                transfers[child_key] = requirement

    root_binding = binding
    if (root_binding is None and requested is not None and resource_only(root)
            and ((requested.family is CONST_BACKEND.IBIS and requested.binding == "bound")
                 or requested.family is CONST_BACKEND.NARWHALS)):
        root_binding = requested
    walk(root, "root", binding=root_binding)
    transfers.update(inherited or {})
    prepared = PreparedExecution("root", nodes, locations, inputs, transfers, phase, tokens,
                                 execution_context, policy)
    if binding is None:
        # A consumer-supplied binding means the consumer's own plan owns the anchor.
        _plan_anchors(prepared, frozenset(
            key for key, node in nodes.items() if _is_borrowed_leaf(node, resolved[key], resolver)
        ))
    # Gate every reachable occurrence before phase rejection or any transfer.
    preflight_capabilities(prepared)
    if phase not in (ExecutionPhase.EXPLAIN, ExecutionPhase.SCHEMA):
        for key, occurrence in locations.items():
            if occurrence.family is CONST_BACKEND.IBIS and occurrence.binding == "unbound":
                raise UnresolvedExecutionLocationError(
                    f"Unbound Ibis source at {key} requires an explicit binding",
                    node_key=key, source=_label(occurrence),
                )
    selected = transfers["root"].destination if "root" in transfers else locations["root"]
    if phase not in (ExecutionPhase.EXPLAIN, ExecutionPhase.SCHEMA) \
            and selected.family is CONST_BACKEND.IBIS and selected.binding != "bound" \
            and not (selected.binding == "memory" and selected.connection is not None):
        raise UnresolvedExecutionLocationError(
            f"Selected execution location at root has unresolved Ibis binding: {_label(selected)}",
            node_key="root", destination=_label(selected),
        )
    if phase in (ExecutionPhase.COMPILE, ExecutionPhase.SCHEMA):
        for requirement in transfers.values():
            origin = locations[requirement.source_key]
            if (not requirement.owned and not requirement.requires_execution
                    and (origin.family, origin.dialect, origin.connection_token)
                    == (requirement.destination.family, requirement.destination.dialect,
                        requirement.destination.connection_token)):
                continue  # raw rows entering their own family's native form: no boundary
            # Schema compilation may not export or materialize rows, even on
            # routes whose ordinary compile contract happens to be row-free.
            if phase is ExecutionPhase.SCHEMA or requirement.requires_execution:
                raise CompileRequiresExecutionError(
                    f"Boundary {requirement.source_key} requires execution; use .collect()",
                    node_key=requirement.source_key, destination=_label(requirement.destination),
                )
    if phase is ExecutionPhase.COMPILE:
        _require_no_native_setup(prepared)
    return prepared


def _require_no_native_setup(p: PreparedExecution) -> None:
    """Compile may reuse ready native-read setup but never create it.

    Creating engine setup (a DuckDB temporary secret for a remote source) is
    execution work. EXPLAIN and SCHEMA never reach read_resource, so only COMPILE
    asks; the Ibis system answers from engine metadata without changing it."""
    from mountainash.relations.core.relation_protocols.relsys_base import get_relation_system

    for key, node in p.nodes.items():
        location = p.locations[key]
        if (isinstance(node, ResourceReadRelNode) and location.family is CONST_BACKEND.IBIS
                and location.binding == "bound" and location.connection is not None
                and get_relation_system(CONST_BACKEND.IBIS)().native_setup_required(
                    node.resource, location=location)):
            raise CompileRequiresExecutionError(
                f"Resource read at {key} needs native storage setup; use .collect()",
                node_key=key, destination=_label(location),
            )


def render_execution(prepared: PreparedExecution) -> str:
    """Render safe placement labels without touching native rows or SQL."""
    lines = [f"{key}: {type(node).__name__} on {_label(prepared.locations[key])}"
             for key, node in prepared.nodes.items()]
    lines.extend(f"transfer {key}: {_label(prepared.locations[requirement.source_key])} -> "
                 f"{_label(requirement.destination)}{' (owned)' if requirement.owned else ''}"
                 for key, requirement in prepared.transfers.items())
    return "\n".join(lines)
