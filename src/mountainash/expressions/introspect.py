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


def walk(
    expr: Any,
    *,
    order: Literal["depth_first", "breadth_first"] = "depth_first",
) -> Iterator[ExpressionNode]:
    """Yield every node in ``expr``'s tree, root first.

    ``order="depth_first"`` (default): pre-order DFS, left-to-right — root,
    then each child's full subtree in ``iter_child_nodes`` order.
    ``order="breadth_first"``: level-order BFS (mirrors ``ast.walk``).

    The input is unwrapped and type-checked (``TypeError`` on a non-node)
    **before** ``order`` is validated (``ValueError`` on an unknown order), so
    a bad input is reported ahead of a bad order. Both checks are eager (they
    fire on the call, not on first iteration).

    Expression ASTs are acyclic (frozen, bottom-up-constructed nodes), so this
    always terminates; a shared subtree is yielded once per edge (no de-dup).
    """
    root = _unwrap(expr)
    if order not in _ORDERS:
        raise ValueError(f"order must be one of {_ORDERS}, got {order!r}")
    if order == "depth_first":
        return _walk_depth_first(root)
    return _walk_breadth_first(root)


def _walk_depth_first(node: ExpressionNode) -> Iterator[ExpressionNode]:
    yield node
    for child in iter_child_nodes(node):
        yield from _walk_depth_first(child)


def _walk_breadth_first(root: ExpressionNode) -> Iterator[ExpressionNode]:
    queue: deque[ExpressionNode] = deque([root])
    while queue:
        node = queue.popleft()
        yield node
        queue.extend(iter_child_nodes(node))


def collect_field_references(expr: Any) -> set[str]:
    """Every source-column name referenced by ``expr``, de-duplicated.

    Returns the ``field`` of every :class:`FieldReferenceNode` in the tree
    (window ``partition_by`` refs included). A literal-only expression yields
    the empty set; repeated columns collapse to one entry.

    Limitation: surfaces only node-form references. Raw-string column
    shortcuts that never become nodes — notably window ``order_by`` columns
    (``SortField.column``) — are not included; a node-based collector cannot
    see a non-node, and a string-based one cannot tell a column name from an
    arbitrary option string.
    """
    return {
        node.field
        for node in walk(expr)
        if isinstance(node, FieldReferenceNode)
    }
