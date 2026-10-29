"""Execution-scoped, non-materializing resolution of relation locations."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any

from mountainash.core.backend_detection import identify_backend, native_identity
from mountainash.core.capabilities.identity import KNOWN_DIALECTS, BackendIdentity
from mountainash.core.capabilities.policy import _CapabilityTarget
from mountainash.core.dtypes.targets import TypeTarget
from mountainash.core.types import is_ibis_backend
from mountainash.core.constants import CONST_BACKEND, ExecutionTarget
from mountainash.core.lazy_imports import import_ibis_expr_ops
from mountainash.relations.core.errors import UnresolvedExecutionLocationError
from mountainash.relations.core.materialization import ExecutionForm
from mountainash.relations.core.relation_nodes import JoinRelNode, ReadRelNode, SetRelNode, SourceRelNode
from mountainash.relations.core.relation_nodes.extensions_mountainash import RefRelNode, ResourceReadRelNode
from mountainash.relations.dag.errors import RelationDAGRequired, UnknownRelationRef

if TYPE_CHECKING:
    from collections.abc import Callable

    from mountainash.relations.core.relation_nodes import RelationNode


class IdentityTokens:
    """Stable local ordinals for retained objects, without value comparison."""

    def __init__(self) -> None:
        self._objects: list[object] = []

    def token(self, value: object) -> int:
        for index, candidate in enumerate(self._objects):
            if candidate is value:
                return index
        self._objects.append(value)
        return len(self._objects) - 1


@dataclass(frozen=True)
class ExecutionLocation:
    family: CONST_BACKEND | None
    dialect: str | None
    form: ExecutionForm
    binding: str
    connection_token: int | None = None
    connection: Any = field(default=None, compare=False, repr=False)
    prototype: Any = field(default=None, compare=False, repr=False)

    @property
    def key(self) -> tuple[CONST_BACKEND | None, str | None, ExecutionForm, str, int | None]:
        return self.family, self.dialect, self.form, self.binding, self.connection_token

    @property
    def capability_identity(self) -> BackendIdentity | None:
        return BackendIdentity(self.family, self.dialect) if self.family is not None else None

    @property
    def connection_label(self) -> str | None:
        return f"connection-{self.connection_token}" if self.connection_token is not None else None

    @property
    def type_target(self) -> TypeTarget:
        """The type-system target used to describe this location's native types."""
        if self.family is CONST_BACKEND.IBIS:
            return TypeTarget.IBIS
        if self.family is CONST_BACKEND.NARWHALS:
            return _NARWHALS_TYPE_TARGETS.get(self.dialect, TypeTarget.POLARS)
        return TypeTarget.POLARS

    def capability_target(self, default_owner: object | None = None) -> _CapabilityTarget | None:
        """The capability owner for this location: its connection, else its prototype."""
        if self.capability_identity is None:
            return None
        owner = self.connection if self.connection is not None else self.prototype
        if owner is None:
            owner = default_owner
        if owner is None:
            return None
        return _CapabilityTarget(self.capability_identity, owner)


_NARWHALS_TYPE_TARGETS = {
    "narwhals-pandas": TypeTarget.PANDAS,
    "narwhals-pyarrow": TypeTarget.PYARROW,
}

# Public ``target=`` family spellings; pandas and pyarrow are carriers that
# execute through Narwhals (``CONST_BACKEND_SYSTEM``), not execution families.
_TARGET_FAMILIES: dict[str, tuple[CONST_BACKEND, str | None]] = {
    "polars": (CONST_BACKEND.POLARS, "polars"),
    "narwhals": (CONST_BACKEND.NARWHALS, "narwhals-polars"),
    "pandas": (CONST_BACKEND.NARWHALS, "narwhals-pandas"),
    "pyarrow": (CONST_BACKEND.NARWHALS, "narwhals-pyarrow"),
    "ibis": (CONST_BACKEND.IBIS, None),
}


def schema_prototype(value: Any) -> Any:
    """Use a native lazy plan, or a dtype-faithful empty eager prototype."""
    from mountainash.core.types import (
        is_narwhals_dataframe, is_narwhals_lazyframe, is_pandas_dataframe,
        is_polars_dataframe, is_polars_lazyframe,
    )
    if isinstance(value, dict) or (
        isinstance(value, (list, tuple)) and all(isinstance(row, dict) for row in value)
    ):
        import polars as pl
        # Existing literal ingress, not evaluation or sampling of a lazy source.
        return pl.DataFrame(value, strict=False).lazy()

    if is_polars_dataframe(value):
        return value.lazy()
    if is_polars_lazyframe(value) or is_narwhals_lazyframe(value):
        return value
    if is_narwhals_dataframe(value):
        native = value.to_native()
        import narwhals as nw
        if is_polars_dataframe(native):
            # Narwhals' eager and lazy APIs admit different expressions.
            # Preserve the source's API while retaining only its dtype metadata.
            return nw.from_native(native.clear())
        return nw.from_native(schema_prototype(native))
    if is_pandas_dataframe(value):
        return value.iloc[:0]
    try:
        import pyarrow as pa
        if isinstance(value, (pa.Table, pa.RecordBatch)):
            return value.slice(0, 0)
    except ImportError:
        pass
    return value


class LocationResolver:
    """Resolve outputs in a supplied binding context without reading rows."""

    def __init__(
        self, tokens: IdentityTokens, *,
        identity_resolver: Callable[[str], RelationNode] | None = None,
    ) -> None:
        self.tokens = tokens
        self.identity_resolver = identity_resolver
        self._cache: dict[tuple[int, tuple | None], ExecutionLocation] = {}
        self._active_refs: set[str] = set()

    def resolve(
        self, node: RelationNode, *, binding: ExecutionLocation | None = None,
    ) -> ExecutionLocation:
        key = (self.tokens.token(node), binding.key if binding is not None else None)
        if key not in self._cache:
            self._cache[key] = self._resolve(node, binding)
        return self._cache[key]

    def resolve_target(self, target: Any) -> ExecutionLocation | None:
        """Resolve a public ``target=`` value: family, dialect identifier or Ibis connection."""
        if target is None:
            return None
        if isinstance(target, str):
            name = target.lower()
            if name in _TARGET_FAMILIES:
                family, dialect = _TARGET_FAMILIES[name]
            else:
                family = next((f for f, names in KNOWN_DIALECTS.items() if name in names), None)
                if family is None or family in (CONST_BACKEND.PANDAS, CONST_BACKEND.PYARROW):
                    raise ValueError(f"unknown target: {target!r}")
                dialect = name
            if family is CONST_BACKEND.IBIS:
                return ExecutionLocation(family, dialect, ExecutionForm.DEFERRED, "unresolved")
            if family is CONST_BACKEND.POLARS:
                return ExecutionLocation(family, dialect, ExecutionForm.LAZY, "bound")
            form = ExecutionForm.LAZY if dialect == "narwhals-lazy" else ExecutionForm.EAGER
            return ExecutionLocation(family, dialect, form, "bound")
        if is_ibis_backend(target):
            return ExecutionLocation(
                CONST_BACKEND.IBIS, f"ibis-{target.name}", ExecutionForm.DEFERRED, "bound",
                self.tokens.token(target), target,
            )
        raise TypeError("target must be a backend family, dialect identifier, or Ibis connection")

    def _resolve(self, node: RelationNode, binding: ExecutionLocation | None) -> ExecutionLocation:
        if isinstance(node, ReadRelNode):
            result = self._read(node.dataframe)
            return self._borrow(result, binding)
        if isinstance(node, SourceRelNode):
            return ExecutionLocation(CONST_BACKEND.POLARS, "polars", ExecutionForm.LAZY, "bound")
        if isinstance(node, ResourceReadRelNode):
            if binding is not None and binding.family is CONST_BACKEND.IBIS and binding.connection is not None:
                from mountainash.relations.core.relation_protocols.relsys_base import get_relation_system

                native = get_relation_system(CONST_BACKEND.IBIS)().native_scan_eligible(
                    node.resource, location=binding)
                return replace(binding, binding="bound" if native else "memory")
            if binding is not None and binding.family is CONST_BACKEND.NARWHALS:
                return binding
            return ExecutionLocation(CONST_BACKEND.POLARS, "polars", ExecutionForm.LAZY, "bound")
        if isinstance(node, RefRelNode):
            if self.identity_resolver is None:
                raise RelationDAGRequired(f"Reference {node.name!r} requires a RelationDAG resolver")
            if node.name in self._active_refs:
                raise UnresolvedExecutionLocationError(f"Cyclic relation reference {node.name!r}")
            self._active_refs.add(node.name)
            try:
                try:
                    target = self.identity_resolver(node.name)
                except KeyError as exc:
                    raise UnknownRelationRef(f"Unknown relation reference {node.name!r}") from exc
                return self.resolve(target, binding=binding)
            finally:
                self._active_refs.remove(node.name)
        if isinstance(node, JoinRelNode):
            selected_node = node.right if node.execute_on is ExecutionTarget.RIGHT else node.left
            peer_node = node.left if selected_node is node.right else node.right
            # Resolve the selected subtree's own peer authority before using
            # a binding supplied by an enclosing consumer.
            selected = self.resolve(selected_node)
            if selected.binding == "memory":
                peer = self.resolve(peer_node)
                selected = self._borrow(selected, peer)
                if selected.binding == "memory":
                    selected = self._borrow(selected, binding)
                if selected.binding == "bound":
                    selected = self.resolve(selected_node, binding=selected)
            return selected
        if isinstance(node, SetRelNode):
            if not node.inputs:
                return ExecutionLocation(None, None, ExecutionForm.DEFERRED, "unresolved")
            first = self.resolve(node.inputs[0])
            if first.binding == "memory":
                for peer_node in node.inputs[1:]:
                    first = self._borrow(first, self.resolve(peer_node))
                    if first.binding == "bound":
                        return self.resolve(node.inputs[0], binding=first)
                first = self._borrow(first, binding)
                if first.binding == "bound":
                    return self.resolve(node.inputs[0], binding=first)
            return first
        children = node.children()
        if len(children) == 1:
            return self.resolve(children[0], binding=binding)
        if node._leaf_backend is not None:
            family = node._leaf_backend
            dialect = "polars" if family is CONST_BACKEND.POLARS else None
            return ExecutionLocation(family, dialect, ExecutionForm.LAZY, "bound" if family is not CONST_BACKEND.IBIS else "unresolved")
        return ExecutionLocation(None, None, ExecutionForm.DEFERRED, "unresolved")

    @staticmethod
    def _borrow(selected: ExecutionLocation, peer: ExecutionLocation | None) -> ExecutionLocation:
        if (selected.family is CONST_BACKEND.IBIS and selected.binding == "memory"
                and peer is not None and peer.family is CONST_BACKEND.IBIS
                and peer.binding == "bound" and peer.connection is not None):
            return replace(selected, dialect=peer.dialect, binding="bound",
                           connection_token=peer.connection_token, connection=peer.connection,
                           prototype=peer.prototype)
        return selected

    def _read(self, value: Any) -> ExecutionLocation:
        # A column/row mapping has no native backend to detect. It is local
        # ingress data: the existing default family is Polars, not a binding
        # borrowed from an Ibis sibling. No frame construction is needed here.
        if isinstance(value, dict) or (isinstance(value, (list, tuple))
                                        and (not value or isinstance(value[0], dict))):
            return ExecutionLocation(CONST_BACKEND.POLARS, "polars", ExecutionForm.EAGER,
                                      "bound", prototype=value)
        if isinstance(value, (list, tuple)):
            raise TypeError(f"Cannot coerce {type(value).__name__} to Polars: expected mappings")
        family = identify_backend(value)
        # The shared dialect probe deliberately raises for mixed Ibis graphs.
        # Inspect all source nodes ourselves before identifying a single source.
        identity = native_identity(value) if family is not CONST_BACKEND.IBIS else None
        form = ExecutionForm.DEFERRED if family is CONST_BACKEND.IBIS else (
            ExecutionForm.LAZY if type(value).__name__ == "LazyFrame" else ExecutionForm.EAGER
        )
        if family is not CONST_BACKEND.IBIS:
            return ExecutionLocation(family, identity.dialect, form, "bound", prototype=value)
        ops = import_ibis_expr_ops()
        seen: set[int] = set()
        sources: list[Any] = []
        has_memory = False
        has_unbound = False

        def walk(item: Any) -> None:
            nonlocal has_memory, has_unbound
            if id(item) in seen:
                return
            seen.add(id(item))
            if isinstance(item, (ops.DatabaseTable, ops.SQLQueryResult)):
                if not any(item.source is source for source in sources):
                    sources.append(item.source)
            elif isinstance(item, ops.UnboundTable):
                has_unbound = True
            elif isinstance(item, ops.InMemoryTable):
                has_memory = True
            if isinstance(item, ops.Node):
                for arg in item.__args__:
                    walk(arg)
            elif isinstance(item, (tuple, list)):
                for arg in item:
                    walk(arg)
            elif isinstance(item, dict):
                for arg in item.values():
                    walk(arg)

        walk(value.op())
        if has_unbound or len(sources) > 1:
            return ExecutionLocation(family, None, form, "unbound" if has_unbound else "unresolved", prototype=value)
        if sources:
            connection = sources[0]
            return ExecutionLocation(family, f"ibis-{connection.name}", form, "bound",
                                     self.tokens.token(connection), connection, value)
        return ExecutionLocation(family, None, form, "memory" if has_memory else "unresolved", prototype=value)
