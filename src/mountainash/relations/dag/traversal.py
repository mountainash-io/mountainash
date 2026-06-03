"""Traversal helpers for RelationDAG relation trees."""
from __future__ import annotations

from typing import Any

from mountainash.relations.core.relation_nodes.extensions_mountainash import RefRelNode


def relation_children(node: Any) -> tuple[Any, ...]:
    """Return structural relation children for DAG traversal."""
    children = getattr(node, "children", None)
    if callable(children):
        return tuple(children())

    found: list[Any] = []
    for attr in ("input", "left", "right", "inputs"):
        child = getattr(node, attr, None)
        if child is None:
            continue
        if isinstance(child, list):
            found.extend(child)
        else:
            found.append(child)
    return tuple(found)


def walk_refs(node: Any) -> set[str]:
    """Recursively collect names of all RefRelNode descendants under ``node``."""
    found: set[str] = set()
    if node is None:
        return found
    if isinstance(node, RefRelNode):
        found.add(node.name)
    for child in relation_children(node):
        found |= walk_refs(child)
    return found


_walk_refs = walk_refs
