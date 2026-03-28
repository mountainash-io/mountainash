"""Base RelationSystem interface and backend registry.

This module defines the abstract interface that all backend-specific
RelationSystem implementations must follow, and provides the registration
mechanism for discovering relation systems by backend type.

Mirrors the pattern in ``mountainash.expressions.core.expression_system.expsys_base``.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Any, Dict, Type

from mountainash.core.constants import CONST_BACKEND

# Import all protocols used for class inheritance (must be at runtime)
from .relation_systems.substrait import (
    SubstraitReadRelationSystemProtocol,
    SubstraitProjectRelationSystemProtocol,
    SubstraitFilterRelationSystemProtocol,
    SubstraitSortRelationSystemProtocol,
    SubstraitFetchRelationSystemProtocol,
    SubstraitJoinRelationSystemProtocol,
    SubstraitAggregateRelationSystemProtocol,
    SubstraitSetRelationSystemProtocol,
)
from .relation_systems.extensions_mountainash import (
    MountainashExtensionRelationSystemProtocol,
)


class RelationSystem(
    SubstraitReadRelationSystemProtocol,
    SubstraitProjectRelationSystemProtocol,
    SubstraitFilterRelationSystemProtocol,
    SubstraitSortRelationSystemProtocol,
    SubstraitFetchRelationSystemProtocol,
    SubstraitJoinRelationSystemProtocol,
    SubstraitAggregateRelationSystemProtocol,
    SubstraitSetRelationSystemProtocol,
    MountainashExtensionRelationSystemProtocol,
):
    """Abstract base class for backend-specific relation systems.

    RelationSystem encapsulates all backend-specific relational operations,
    providing a uniform interface for the relation visitor to use regardless
    of the underlying DataFrame library.
    """

    @property
    @abstractmethod
    def backend_type(self) -> CONST_BACKEND: ...


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_relation_system_registry: Dict[str, Type[RelationSystem]] = {}


def register_relation_system(backend: CONST_BACKEND):
    """Decorator for registering RelationSystem classes.

    Usage::

        @register_relation_system(CONST_BACKEND.POLARS)
        class PolarsRelationSystem(RelationSystem):
            ...
    """

    def decorator(cls: Type[RelationSystem]) -> Type[RelationSystem]:
        _relation_system_registry[backend.value] = cls
        return cls

    return decorator


def get_relation_system(backend: CONST_BACKEND) -> Type[RelationSystem]:
    """Get the RelationSystem class for a backend.

    Raises:
        KeyError: If no RelationSystem is registered for the backend.
    """
    if backend.value not in _relation_system_registry:
        raise KeyError(
            f"No RelationSystem registered for backend '{backend.value}'. "
            f"Registered: {list(_relation_system_registry.keys())}"
        )
    return _relation_system_registry[backend.value]
