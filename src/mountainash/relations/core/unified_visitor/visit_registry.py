"""Registry for extension relation node visit handlers.

External packages register handlers for custom node types so the
UnifiedRelationVisitor can dispatch to them without hardcoding
visit methods in core.
"""
from __future__ import annotations

from typing import Any, Callable, Optional, TYPE_CHECKING

from mountainash.core.registries import KeyedRegistry

if TYPE_CHECKING:
    from .relation_visitor import UnifiedRelationVisitor

RelationVisitHandler = Callable[[Any, "UnifiedRelationVisitor"], Any]

_PROTECTED_NODE_TYPES: set[type] = set()


def _protect(*node_types: type) -> None:
    _PROTECTED_NODE_TYPES.update(node_types)


def _validate_registration(node_type: type, handler: RelationVisitHandler) -> None:
    if node_type in _PROTECTED_NODE_TYPES:
        raise TypeError(
            f"{node_type.__name__} is a protected Substrait-aligned node type "
            f"and cannot be overridden via the registry"
        )


def _init_core_handlers() -> None:
    from ._core_handlers import _register_core_handlers
    _register_core_handlers()


_registry: KeyedRegistry[type, RelationVisitHandler] = KeyedRegistry(
    "visit handler",
    initializer=_init_core_handlers,
    validator=_validate_registration,
)


class RelationVisitRegistry:
    """Type-keyed node -> visit-handler registry (third-party extension surface)."""

    @classmethod
    def register(cls, node_type: type, handler: RelationVisitHandler) -> None:
        try:
            _registry.register(node_type, handler)
        except ValueError:
            raise ValueError(
                f"{node_type.__name__} already has a registered visit handler"
            ) from None

    @classmethod
    def get(cls, node_type: type) -> Optional[RelationVisitHandler]:
        return _registry.get_optional(node_type)

    @classmethod
    def unregister(cls, node_type: type) -> None:
        _registry.unregister(node_type)


def _protect_substrait_nodes() -> None:
    from ..relation_nodes import (
        ReadRelNode, ProjectRelNode, FilterRelNode, SortRelNode,
        FetchRelNode, JoinRelNode, AggregateRelNode, SetRelNode,
    )
    from ..relation_nodes.extensions_mountainash import ExtensionRelNode
    _protect(
        ReadRelNode, ProjectRelNode, FilterRelNode, SortRelNode,
        FetchRelNode, JoinRelNode, AggregateRelNode, SetRelNode,
        ExtensionRelNode,
    )

_protect_substrait_nodes()
