"""Public expression-AST introspection (item 226a).

A supported surface for walking an expression AST, modelled on Python's
stdlib ``ast`` module:

- :func:`iter_child_nodes` — direct ``ExpressionNode`` children, one level.
- :func:`walk` — full-tree generator, DFS (default) or BFS.
- :func:`collect_field_references` — every referenced source-column name.

This module is ``expressions``-scoped: it imports only from
``expressions.core.expression_nodes`` (plus ``pydantic``/stdlib) and must
never import from ``mountainash.validation`` — ``validation`` consumes this
module, not the reverse.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Iterator, Literal

from pydantic import BaseModel

from mountainash.expressions.core.expression_nodes import (
    ExpressionNode,
    FieldReferenceNode,
)

_ORDERS = ("depth_first", "breadth_first")


def _unwrap(expr: Any) -> ExpressionNode:
    """Unwrap a ``._node`` API wrapper and enforce the node input contract.

    Accepts a built expression (a ``ma.col(...)`` wrapper) or a raw
    ``ExpressionNode``. Raises ``TypeError`` (naming the received type) for
    anything else — bare strings, ``None`` and bare literals are not valid
    introspection inputs (bare-string column handling is a relations concern).
    """
    node = expr._node if hasattr(expr, "_node") else expr
    if not isinstance(node, ExpressionNode):
        raise TypeError(
            "expression introspection requires an ExpressionNode or a built "
            f"expression, got {type(expr).__name__}"
        )
    return node


def iter_child_nodes(node: Any) -> list[ExpressionNode]:
    """Direct ``ExpressionNode`` children of ``node``, one level deep.

    Descends *through* transparent non-node containers to the nearest node
    edges: a non-node ``pydantic.BaseModel`` (e.g. ``WindowSpec``, whose
    ``partition_by`` holds the window's partition ``FieldReferenceNode``s),
    ``dict`` values, and ``list``/``tuple``/``set``/``frozenset`` elements are
    all transparent. Any other value (str, int, enum, ``SortField`` dataclass,
    ``None``) is inert.

    ``node`` may be a raw node or a ``._node``-bearing wrapper. Mirrors
    ``ast.iter_child_nodes``, generalized for these container shapes.
    """
    node = _unwrap(node)
    children: list[ExpressionNode] = []

    def _collect(value: Any) -> None:
        if isinstance(value, ExpressionNode):
            # Node edge — collect and stop; its own fields are its children,
            # surfaced one level down by the caller of iter_child_nodes.
            children.append(value)
        elif isinstance(value, BaseModel):
            # Transparent non-node model (e.g. WindowSpec) — recurse through it.
            for name in type(value).model_fields:
                _collect(getattr(value, name))
        elif isinstance(value, dict):
            for item in value.values():
                _collect(item)
        elif isinstance(value, (list, tuple, set, frozenset)):
            for item in value:
                _collect(item)

    for name in type(node).model_fields:
        _collect(getattr(node, name))
    return children
