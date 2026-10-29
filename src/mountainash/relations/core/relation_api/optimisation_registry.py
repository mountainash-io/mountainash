"""Registry for relational AST optimisation passes.

Backends (e.g. pipelines) register their transforms here at import time.
RelationBase._apply_optimisations() consumes the registry without knowing
which packages registered into it — preserving dependency direction.
"""
from __future__ import annotations

from typing import Any, Callable

from mountainash.core.registries import KeyedRegistry

_passes: KeyedRegistry[type, Callable[[Any], Any]] = KeyedRegistry(
    "optimisation pass", multi=True
)


def register_optimisation(node_type: type, transform_fn: Callable[[Any], Any]) -> None:
    _passes.register(node_type, transform_fn)


def get_registered_node_types() -> set[type]:
    return set(_passes.list_keys())


def get_passes() -> list[tuple[type, Callable[[Any], Any]]]:
    return _passes.entries()


def _reset_registry() -> None:
    _passes.reset()
