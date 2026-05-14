"""Registry for extension relation node visit handlers.

External packages register handlers for custom node types so the
UnifiedRelationVisitor can dispatch to them without hardcoding
visit methods in core.
"""
from __future__ import annotations

from typing import Any, Callable, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .relation_visitor import UnifiedRelationVisitor

RelationVisitHandler = Callable[[Any, "UnifiedRelationVisitor"], Any]

_PROTECTED_NODE_TYPES: set[type] = set()


def _protect(*node_types: type) -> None:
    _PROTECTED_NODE_TYPES.update(node_types)


class RelationVisitRegistry:
    _handlers: dict[type, RelationVisitHandler] = {}
    _initialized: bool = False

    @classmethod
    def _ensure_initialized(cls) -> None:
        if not cls._initialized:
            cls._initialized = True
            from ._core_handlers import _register_core_handlers
            _register_core_handlers()

    @classmethod
    def register(cls, node_type: type, handler: RelationVisitHandler) -> None:
        if node_type in _PROTECTED_NODE_TYPES:
            raise TypeError(
                f"{node_type.__name__} is a protected Substrait-aligned node type "
                f"and cannot be overridden via the registry"
            )
        if node_type in cls._handlers:
            raise ValueError(
                f"{node_type.__name__} already has a registered visit handler"
            )
        cls._handlers[node_type] = handler

    @classmethod
    def get(cls, node_type: type) -> Optional[RelationVisitHandler]:
        cls._ensure_initialized()
        return cls._handlers.get(node_type)

    @classmethod
    def unregister(cls, node_type: type) -> None:
        cls._handlers.pop(node_type, None)
