"""Registry for relational AST optimisation passes.

Backends (e.g. pipelines) register their transforms here at import time.
RelationBase._apply_optimisations() consumes the registry without knowing
which packages registered into it — preserving dependency direction.
"""
from __future__ import annotations

from typing import Any, Callable

_PASSES: list[tuple[type, Callable[[Any], Any]]] = []
_NODE_TYPES: set[type] = set()


def register_optimisation(node_type: type, transform_fn: Callable[[Any], Any]) -> None:
    _PASSES.append((node_type, transform_fn))
    _NODE_TYPES.add(node_type)


def get_registered_node_types() -> set[type]:
    return _NODE_TYPES.copy()


def get_passes() -> list[tuple[type, Callable[[Any], Any]]]:
    return list(_PASSES)


def _reset_registry() -> None:
    _PASSES.clear()
    _NODE_TYPES.clear()
