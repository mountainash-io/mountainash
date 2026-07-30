"""Coercion-free membership encoder (Task 4).

Turns a canonical member list (output of Task 3's :func:`classify_members`)
into the (arguments, options) tuple that the ``is_in`` / ``t_is_in``
``ScalarFunctionNode`` carries.

The single most important correctness rule: encoding must **NEVER**
coerce value members. The ternary builder's :func:`_to_substrait_node`
calls :func:`_coerce_if_needed` which wraps non-ternary
``ScalarFunctionNode`` operands in ``TO_TERNARY`` — that hook is
**exactly** what would corrupt a member like
``ma.col("a").str.lower()`` (a boolean-typed ScalarFunctionNode
that must stay as itself, not get booleanised).

Public surface:

* :func:`to_member_node` — coercion-free converter (Codex#1). Unwraps a
  ``BaseExpressionAPI`` to its ``._node``; passes an ``ExpressionNode``
  through; wraps a raw scalar in ``LiteralNode``. **Never** calls
  ``_to_substrait_node`` / ``_coerce_if_needed``.

* :func:`encode_membership` — produces the (arguments, options) tuple
  used to build the membership ``ScalarFunctionNode``:

    * all-scalar-literal members → ``arguments=[needle, COLLECT_VALUES(LiteralNode…)]``
    * any expression member (or mixed) → ``arguments=[needle, *map(to_member_node, members)]``
    * always ``options={"member_unknown_values": tuple(_member_unknown(m) for m in members)}``
      — positionally aligned (each entry = that member's ``unknown_values``
      frozenset, or ``None``).

Private helper:

* :func:`_member_unknown` — extracts ``unknown_values`` from a member
  (returns a ``frozenset`` or ``None``).
"""
from __future__ import annotations

from typing import Any

from mountainash.expressions.core.expression_api.api_base import BaseExpressionAPI
from mountainash.expressions.core.expression_nodes import (
    ExpressionNode,
    LiteralNode,
    ScalarFunctionNode,
)
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_TERNARY,
)


def _is_scalar_member(m: Any) -> bool:
    """True iff ``m`` is a raw Python scalar (not a ``BaseExpressionAPI``
    or ``ExpressionNode``).

    A scalar member is anything the existing
    ``api_bldr_ext_ma_scalar_ternary.t_is_in`` literal-collection path
    accepts: ``int``, ``float``, ``str``, ``bytes``, ``bool``, ``None``,
    plus out-of-table scalars (``Decimal``/``date``/``datetime``/``enum``/
    NumPy scalar / custom objects). Practically: anything that is not
    an ``ExpressionNode``-bearing object.
    """
    return not isinstance(m, (BaseExpressionAPI, ExpressionNode))


def _member_unknown(m: Any) -> frozenset | None:
    """Return the member's ``unknown_values`` as a frozenset, or ``None``.

    For ``BaseExpressionAPI`` members, unwrap ``._node`` and read its
    ``unknown_values``. For ``ExpressionNode`` members, read directly.
    For raw scalars, return ``None`` (no sentinel semantics).

    The returned frozenset is what the ``member_unknown_values`` option
    carries; pydantic handles it as a set-equivalent on round-trip.
    """
    node: ExpressionNode | None
    if isinstance(m, BaseExpressionAPI):
        node = m._node
    elif isinstance(m, ExpressionNode):
        node = m
    else:
        return None

    unknown = getattr(node, "unknown_values", None)
    if unknown is None:
        return None
    return frozenset(unknown)


def to_member_node(m: Any) -> ExpressionNode:
    """Coercion-free member-to-node converter (Codex#1).

    * ``BaseExpressionAPI`` → ``m._node`` (unwrapped, identity preserved
      for the inner ``ExpressionNode``).
    * ``ExpressionNode`` → returned as-is (identity preserved).
    * raw scalar → wrapped in ``LiteralNode``.

    **Crucially, this function does NOT call
    :func:`api_bldr_ext_ma_scalar_ternary._to_substrait_node` /
    :func:`_coerce_if_needed`** — those wrap a non-ternary
    ``ScalarFunctionNode`` member in ``TO_TERNARY`` (e.g. they would
    corrupt ``ma.col("a").str.lower()`` if it were used as a value
    member). The encoder passes the member's node through unchanged
    so that backend visitors see the actual value-producing
    expression, not a booleanised proxy.
    """
    if isinstance(m, BaseExpressionAPI):
        return m._node
    if isinstance(m, ExpressionNode):
        return m
    return LiteralNode(value=m)


def encode_membership(
    needle_node: ExpressionNode,
    members: list,
) -> tuple[list[ExpressionNode], dict[str, tuple]]:
    """Encode a classified member list into the (arguments, options) pair
    that the ``is_in`` / ``t_is_in`` ``ScalarFunctionNode`` carries.

    Args:
        needle_node: The left-hand-side expression (the value being
            tested for membership). Appears as ``arguments[0]``.
        members: A canonical member list from
            :func:`mountainash.expressions.membership.classify.classify_members`.
            Each entry is either a raw scalar or a ``BaseExpressionAPI``
            / ``ExpressionNode`` — no backend-native expressions, no
            containers, no nested structures (Task 3 guarantees this).

    Returns:
        A 2-tuple ``(arguments, options)``:

        * ``arguments`` is a ``list[ExpressionNode]``:
            * all-scalar-literal members → ``[needle, COLLECT_VALUES(LiteralNode…)]``
              (the COLLECT_VALUES node carries the literal collection;
              mirrors ``api_bldr_ext_ma_scalar_ternary.t_is_in``)
            * any expression/mixed member → ``[needle, *map(to_member_node, members)]``
              (flat positional args; no wrapper)

        * ``options`` is a ``dict`` with exactly one key:
          ``"member_unknown_values"`` → a ``tuple`` of length ``len(members)``
          aligned positionally with ``members``. Each entry is the
          member's ``unknown_values`` as a ``frozenset`` (or ``None``
          if the member has no sentinel semantics). A raw scalar
          always contributes ``None``.

    Raises:
        ValueError: if ``members`` is empty (defensive — Task 3's
            :func:`classify_members` already rejects empty collections,
            but a malformed-length argument should still surface a
            descriptive error at the encoder boundary rather than
            silently producing a degenerate ``ScalarFunctionNode``).
    """
    if not members:
        raise ValueError(
            "encode_membership requires at least one member; "
            "callers must run classify_members first (it rejects empty collections)."
        )

    options = {
        "member_unknown_values": tuple(_member_unknown(m) for m in members),
    }

    if all(_is_scalar_member(m) for m in members):
        # All-scalar-literal path — wrap in COLLECT_VALUES (mirrors
        # api_bldr_ext_ma_scalar_ternary.t_is_in, lines ~205-245).
        literal_nodes: list[ExpressionNode] = [LiteralNode(value=v) for v in members]
        collection_arg: ExpressionNode = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.COLLECT_VALUES,
            arguments=literal_nodes,
        )
        return [needle_node, collection_arg], options

    # Expression / mixed path — flat positional args; coercion-free
    # conversion (no TO_TERNARY wrap).
    return [needle_node, *map(to_member_node, members)], options
