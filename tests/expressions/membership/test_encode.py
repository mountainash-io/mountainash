"""Tests for the coercion-free membership encoder (Task 4).

The encoder turns a classified member list (output of Task 3's
:classify_members>) into the (arguments, options) tuple that the
``is_in`` / ``t_is_in`` ScalarFunctionNode carries.

Two halves:

1. **to_member_node** — coercion-free converter (Codex#1). Unwraps a
   ``BaseExpressionAPI`` to its ``._node``; passes an ``ExpressionNode``
   through; wraps a raw scalar in ``LiteralNode``. **Never** calls
   ``_to_substrait_node`` / ``_coerce_if_needed`` — those wrap value
   members in ``TO_TERNARY``, which would corrupt a
   ``ScalarFunctionNode`` member such as ``ma.col("a").str.lower()``.

2. **encode_membership** — the (arguments, options) encoder.

   * all-scalar-literal members → ``arguments=[needle, COLLECT_VALUES(...)]``
   * any expression/mixed member → ``arguments=[needle, *map(to_member_node, members)]``
   * ``options={"member_unknown_values": tuple(...)}`` — positionally aligned
     with ``members``: each entry is the member's
     ``unknown_values`` frozenset (or ``None``).

The single most important correctness rule: encoding must **NEVER** coerce
value members. The test for ``ma.col("a").str.lower()`` as a member is the
canonical regression for that rule.

Round-trip / introspection (Codex#8) covers the new
``member_unknown_values`` option: the values are pydantic-serialisable
(a tuple of ``frozenset``/``None``) and introspectable (each entry
can be classified as a sentinel-set vs. no-sentinel). The full
``ScalarFunctionNode`` carries the option as a plain dict value
— pydantic's standard ``model_dump`` on the parent serialises
``arguments`` and ``options`` independently, which is the contract
that downstream Substrait exporters consume.
"""
from __future__ import annotations

from typing import Optional

import pytest
from pydantic import RootModel

import mountainash as ma
from mountainash.expressions.core.expression_api.api_base import BaseExpressionAPI
from mountainash.expressions.core.expression_nodes import (
    ExpressionNode,
    FieldReferenceNode,
    LiteralNode,
    ScalarFunctionNode,
)
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_TERNARY,
    FKEY_SUBSTRAIT_SCALAR_STRING,
)
from mountainash.expressions.membership.encode import (
    _member_unknown,
    encode_membership,
    to_member_node,
)


# =========================================================================
# Test helpers
# =========================================================================


def _is_collect_values(node: ExpressionNode) -> bool:
    """True iff ``node`` is a ``COLLECT_VALUES`` ScalarFunctionNode."""
    return (
        isinstance(node, ScalarFunctionNode)
        and node.function_key == FKEY_MOUNTAINASH_SCALAR_TERNARY.COLLECT_VALUES
    )


def _is_to_ternary(node: ExpressionNode) -> bool:
    """True iff ``node`` is a ``TO_TERNARY`` ScalarFunctionNode."""
    return (
        isinstance(node, ScalarFunctionNode)
        and node.function_key == FKEY_MOUNTAINASH_SCALAR_TERNARY.TO_TERNARY
    )


# =========================================================================
# to_member_node — coercion-free converter (Codex#1)
# =========================================================================


class TestToMemberNodeBaseExpressionAPI:
    """BaseExpressionAPI → m._node (unwrapped)."""

    def test_ma_col_unwraps_to_field_reference(self) -> None:
        col = ma.col("a")
        result = to_member_node(col)
        assert isinstance(result, FieldReferenceNode)
        assert result.field == "a"

    def test_ma_lit_unwraps_to_literal(self) -> None:
        lit = ma.lit(5)
        result = to_member_node(lit)
        assert isinstance(result, LiteralNode)
        assert result.value == 5

    def test_ma_t_col_unwraps_to_field_reference_with_unknown(self) -> None:
        col = ma.t_col("c", unknown={"?"})
        result = to_member_node(col)
        assert isinstance(result, FieldReferenceNode)
        assert result.field == "c"
        assert result.unknown_values == {"?"}

    def test_ma_col_str_lower_preserves_scalar_function_node(self) -> None:
        """The canonical Codex#1 case: a value-producing expression
        (ScalarFunctionNode) MUST round-trip as itself, NOT wrapped in
        TO_TERNARY (the ternary builder's _coerce_if_needed hook would
        corrupt it).
        """
        expr = ma.col("a").str.lower()
        # Sanity: confirm this is a ScalarFunctionNode with LOWER
        assert isinstance(expr, BaseExpressionAPI)
        assert isinstance(expr._node, ScalarFunctionNode)
        assert expr._node.function_key == FKEY_SUBSTRAIT_SCALAR_STRING.LOWER

        result = to_member_node(expr)
        # Returns the same ScalarFunctionNode — identity preserved
        assert result is expr._node
        # Crucially, NOT wrapped in TO_TERNARY
        assert not _is_to_ternary(result)
        assert isinstance(result, ScalarFunctionNode)
        assert result.function_key == FKEY_SUBSTRAIT_SCALAR_STRING.LOWER


class TestToMemberNodeExpressionNode:
    """ExpressionNode → passed through unchanged (identity)."""

    def test_literal_node_passthrough(self) -> None:
        node = LiteralNode(value=5)
        result = to_member_node(node)
        assert result is node

    def test_field_reference_node_passthrough(self) -> None:
        node = FieldReferenceNode(field="a", unknown_values={-1})
        result = to_member_node(node)
        assert result is node

    def test_scalar_function_node_passthrough(self) -> None:
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.LOWER,
            arguments=[FieldReferenceNode(field="a")],
        )
        result = to_member_node(node)
        assert result is node
        # No TO_TERNARY wrap
        assert not _is_to_ternary(result)


class TestToMemberNodeRawScalar:
    """Raw scalar → wrapped in LiteralNode (no coercion)."""

    def test_int(self) -> None:
        result = to_member_node(5)
        assert isinstance(result, LiteralNode)
        assert result.value == 5

    def test_float(self) -> None:
        result = to_member_node(3.14)
        assert isinstance(result, LiteralNode)
        assert result.value == 3.14

    def test_str(self) -> None:
        result = to_member_node("hello")
        assert isinstance(result, LiteralNode)
        assert result.value == "hello"

    def test_bytes(self) -> None:
        result = to_member_node(b"abc")
        assert isinstance(result, LiteralNode)
        assert result.value == b"abc"

    def test_bool(self) -> None:
        result = to_member_node(True)
        assert isinstance(result, LiteralNode)
        assert result.value is True

    def test_none(self) -> None:
        result = to_member_node(None)
        assert isinstance(result, LiteralNode)
        assert result.value is None


# =========================================================================
# _member_unknown — extraction of unknown_values per member
# =========================================================================


class TestMemberUnknown:
    """_member_unknown(m) — returns the member's unknown_values frozenset or None."""

    def test_raw_scalar_returns_none(self) -> None:
        assert _member_unknown(5) is None
        assert _member_unknown("hello") is None
        assert _member_unknown(None) is None

    def test_ma_col_returns_none(self) -> None:
        """ma.col("x") has no unknown_values (FieldReferenceNode default)."""
        assert _member_unknown(ma.col("x")) is None

    def test_ma_t_col_returns_frozenset(self) -> None:
        result = _member_unknown(ma.t_col("c", unknown={"?"}))
        assert result == frozenset({"?"})
        assert isinstance(result, frozenset)

    def test_ma_t_col_default_returns_none(self) -> None:
        """t_col default unknown=None → no unknown_values set on node."""
        # t_col with no `unknown` argument passes unknown=None to FieldReferenceNode;
        # FieldReferenceNode stores None for unknown_values.
        result = _member_unknown(ma.t_col("c"))
        assert result is None

    def test_field_reference_node_with_unknown(self) -> None:
        node = FieldReferenceNode(field="c", unknown_values={-1, -2})
        result = _member_unknown(node)
        assert result == frozenset({-1, -2})

    def test_field_reference_node_without_unknown(self) -> None:
        node = FieldReferenceNode(field="c")
        assert _member_unknown(node) is None

    def test_scalar_function_node_without_unknown_attribute(self) -> None:
        """A plain ScalarFunctionNode has no unknown_values → returns None."""
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.LOWER,
            arguments=[FieldReferenceNode(field="a")],
        )
        assert _member_unknown(node) is None

    def test_ma_col_str_lower_returns_none(self) -> None:
        """A ScalarFunctionNode wrapped in a BaseExpressionAPI still has
        no unknown_values → returns None.
        """
        assert _member_unknown(ma.col("a").str.lower()) is None


# =========================================================================
# encode_membership — AST-shape
# =========================================================================


class TestEncodeAllScalarLiteral:
    """All-scalar-literal members → COLLECT_VALUES wrapper, all None unknowns."""

    def test_arguments_length(self) -> None:
        needle = ma.col("x")._node
        members = [1, 2, 3]
        arguments, options = encode_membership(needle, members)
        # 1 needle + 1 COLLECT_VALUES node = 2 arguments
        assert len(arguments) == 2
        assert arguments[0] is needle

    def test_collect_values_wrapper_present(self) -> None:
        needle = ma.col("x")._node
        arguments, _ = encode_membership(needle, [1, 2, 3])
        assert _is_collect_values(arguments[1])

    def test_collect_values_wraps_literal_nodes(self) -> None:
        needle = ma.col("x")._node
        arguments, _ = encode_membership(needle, [1, 2, 3])
        collect = arguments[1]
        assert isinstance(collect, ScalarFunctionNode)
        # Children of the COLLECT_VALUES node
        assert len(collect.arguments) == 3
        assert all(isinstance(arg, LiteralNode) for arg in collect.arguments)
        assert [arg.value for arg in collect.arguments] == [1, 2, 3]

    def test_member_unknown_values_all_none(self) -> None:
        needle = ma.col("x")._node
        _, options = encode_membership(needle, [1, 2, 3])
        assert "member_unknown_values" in options
        assert options["member_unknown_values"] == (None, None, None)

    def test_single_scalar_uses_collect_values(self) -> None:
        """1-element all-literal collection → still COLLECT_VALUES (1 child)."""
        needle = ma.col("x")._node
        arguments, options = encode_membership(needle, [5])
        assert _is_collect_values(arguments[1])
        assert options["member_unknown_values"] == (None,)

    def test_empty_collection_encodes_to_empty_collect_values(self) -> None:
        """An empty members list encodes to an empty COLLECT_VALUES node."""
        needle = ma.col("x")._node
        arguments, options = encode_membership(needle, [])
        assert len(arguments) == 2
        assert arguments[0] is needle
        assert _is_collect_values(arguments[1])
        assert len(arguments[1].arguments) == 0
        assert options["member_unknown_values"] == ()


class TestEncodeExpressionMember:
    """Any expression member → no COLLECT_VALUES wrapper; members flat in args."""

    def test_single_ma_col_member_no_collect_values(self) -> None:
        needle = ma.col("x")._node
        members = [ma.col("y")]
        arguments, options = encode_membership(needle, members)
        # 1 needle + 1 member node = 2 arguments, no COLLECT_VALUES
        assert len(arguments) == 2
        assert arguments[0] is needle
        assert not _is_collect_values(arguments[1])
        assert isinstance(arguments[1], FieldReferenceNode)
        assert arguments[1].field == "y"

    def test_single_ma_lit_member_no_collect_values(self) -> None:
        needle = ma.col("x")._node
        members = [ma.lit(5)]
        arguments, _ = encode_membership(needle, members)
        assert len(arguments) == 2
        assert not _is_collect_values(arguments[1])
        assert isinstance(arguments[1], LiteralNode)

    def test_scalar_function_node_member_preserved_unchanged(self) -> None:
        """THE canonical correctness test: a ScalarFunctionNode member
        (e.g. ma.col("a").str.lower()) MUST appear as the raw node,
        NOT wrapped in TO_TERNARY or any other wrapper.
        """
        needle = ma.col("x")._node
        lower_expr = ma.col("a").str.lower()
        arguments, _ = encode_membership(needle, [lower_expr])
        member_node = arguments[1]
        # Identity preserved
        assert member_node is lower_expr._node
        # Not wrapped
        assert not _is_to_ternary(member_node)
        assert isinstance(member_node, ScalarFunctionNode)
        assert member_node.function_key == FKEY_SUBSTRAIT_SCALAR_STRING.LOWER

    def test_raw_expression_node_member_passthrough(self) -> None:
        """An ExpressionNode member (not a BaseExpressionAPI) → passthrough."""
        needle = ma.col("x")._node
        node = FieldReferenceNode(field="a")
        arguments, _ = encode_membership(needle, [node])
        assert arguments[1] is node


class TestEncodeMixed:
    """Mixed scalar/expr members → no COLLECT_VALUES; flat positional args."""

    def test_mixed_scalar_and_ma_col(self) -> None:
        needle = ma.col("x")._node
        members = [1, ma.col("y"), 3]
        arguments, _ = encode_membership(needle, members)
        # 1 needle + 3 members = 4 arguments
        assert len(arguments) == 4
        assert arguments[0] is needle
        # No COLLECT_VALUES anywhere
        for arg in arguments[1:]:
            assert not _is_collect_values(arg)
        # Per-position: LiteralNode, FieldReferenceNode, LiteralNode
        assert isinstance(arguments[1], LiteralNode)
        assert arguments[1].value == 1
        assert isinstance(arguments[2], FieldReferenceNode)
        assert arguments[2].field == "y"
        assert isinstance(arguments[3], LiteralNode)
        assert arguments[3].value == 3

    def test_mixed_preserves_order(self) -> None:
        """Member order is preserved in arguments (positional)."""
        needle = ma.col("x")._node
        members = [3, ma.col("a"), 1, ma.col("b")]
        arguments, _ = encode_membership(needle, members)
        assert arguments[0] is needle
        assert arguments[1].value == 3
        assert arguments[2].field == "a"
        assert arguments[3].value == 1
        assert arguments[4].field == "b"


class TestEncodeAllExpression:
    """All-expression members → no COLLECT_VALUES; flat positional args."""

    def test_two_ma_col_members(self) -> None:
        needle = ma.col("x")._node
        members = [ma.col("a"), ma.col("b")]
        arguments, _ = encode_membership(needle, members)
        assert len(arguments) == 3
        assert arguments[0] is needle
        for arg in arguments[1:]:
            assert isinstance(arg, FieldReferenceNode)
            assert not _is_collect_values(arg)


# =========================================================================
# encode_membership — member_unknown_values alignment
# =========================================================================


class TestEncodeMemberUnknownAlignment:
    """member_unknown_values is positionally aligned with members."""

    def test_all_scalar_unknowns_all_none(self) -> None:
        needle = ma.col("x")._node
        _, options = encode_membership(needle, [1, 2, 3])
        assert options["member_unknown_values"] == (None, None, None)

    def test_mixed_alignment_scalar_then_t_col(self) -> None:
        """Position 0: scalar → None. Position 1: t_col with sentinel → frozenset."""
        needle = ma.col("x")._node
        members = [1, ma.t_col("c", unknown={"?"})]
        _, options = encode_membership(needle, members)
        muv = options["member_unknown_values"]
        assert muv[0] is None
        assert muv[1] == frozenset({"?"})

    def test_mixed_alignment_t_col_then_scalar(self) -> None:
        """Position 0: t_col with sentinel → frozenset. Position 1: scalar → None."""
        needle = ma.col("x")._node
        members = [ma.t_col("c", unknown={-1}), 5]
        _, options = encode_membership(needle, members)
        muv = options["member_unknown_values"]
        assert muv[0] == frozenset({-1})
        assert muv[1] is None

    def test_multiple_independently_different_sentinel_sets(self) -> None:
        """Each member's unknown_values is independent; alignment is per-position."""
        needle = ma.col("x")._node
        members = [
            ma.t_col("a", unknown={"?"}),
            ma.t_col("b", unknown={-1, -2}),
            ma.t_col("c", unknown={None, "NA", "<MISSING>"}),
        ]
        _, options = encode_membership(needle, members)
        muv = options["member_unknown_values"]
        assert muv[0] == frozenset({"?"})
        assert muv[1] == frozenset({-1, -2})
        assert muv[2] == frozenset({None, "NA", "<MISSING>"})

    def test_mixed_scalar_expr_unknown(self) -> None:
        """A 3-member mix with one t_col sentinel in the middle."""
        needle = ma.col("x")._node
        members = [1, ma.t_col("c", unknown={"?"}), 3]
        _, options = encode_membership(needle, members)
        muv = options["member_unknown_values"]
        assert muv == (None, frozenset({"?"}), None)

    def test_member_unknown_values_is_tuple(self) -> None:
        """The container type is tuple, not list — aligned with options value semantics."""
        needle = ma.col("x")._node
        _, options = encode_membership(needle, [1, 2])
        assert isinstance(options["member_unknown_values"], tuple)

    def test_only_member_unknown_values_option_key(self) -> None:
        """The options dict contains exactly one key: member_unknown_values."""
        needle = ma.col("x")._node
        _, options = encode_membership(needle, [1, 2, 3])
        assert set(options.keys()) == {"member_unknown_values"}


# =========================================================================
# encode_membership — return value types
# =========================================================================


class TestEncodeReturnTypes:
    """encode_membership returns (list, dict)."""

    def test_arguments_is_list(self) -> None:
        needle = ma.col("x")._node
        arguments, _ = encode_membership(needle, [1, 2, 3])
        assert isinstance(arguments, list)

    def test_options_is_dict(self) -> None:
        needle = ma.col("x")._node
        _, options = encode_membership(needle, [1, 2, 3])
        assert isinstance(options, dict)

    def test_first_argument_is_needle_node(self) -> None:
        """The first argument is always the needle node (identity preserved)."""
        needle = ma.col("needle_col")._node
        arguments, _ = encode_membership(needle, [1, 2])
        assert arguments[0] is needle


# =========================================================================
# encode_membership — round-trip / introspection (Codex#8)
# =========================================================================


class TestEncodeRoundTrip:
    """The (arguments, options) output survives a pydantic round-trip.

    The Codex#8 requirement is that the new ``member_unknown_values``
    option be both serialisable and introspectable. We test it directly
    with a ``RootModel`` (a tuple of ``frozenset | None``) rather than
    threading through ``ScalarFunctionNode.model_validate`` (which
    requires a discriminator to re-pick the abstract
    ``ExpressionNode`` subclass — not how this codebase round-trips
    nodes). The full node's ``model_dump`` does serialise the options
    dict natively; we verify that path too.
    """

    def test_scalar_function_node_preserved(self) -> None:
        """Re-constructing the ScalarFunctionNode from (arguments, options)
        yields a node with the same arguments/options/function_key.
        """
        needle = ma.col("x")._node
        members = [ma.col("a").str.lower(), 5]
        arguments, options = encode_membership(needle, members)

        # Pydantic round-trip on a hypothetical parent node — but our
        # immediate contract is (arguments, options). Instead, assert
        # that the argument and option values themselves are pydantic-
        # serialisable (i.e. types are JSON-friendly / pydantic-friendly).
        assert all(
            isinstance(arg, ExpressionNode) for arg in arguments
        )
        # Tuple of (frozenset | None) — pydantic can handle frozenset
        # (treated as a set) and None.
        for entry in options["member_unknown_values"]:
            assert entry is None or isinstance(entry, frozenset)

    def test_options_member_unknown_values_introspectable(self) -> None:
        """The new ``member_unknown_values`` tuple round-trips through
        ``model_dump`` and ``model_validate`` (the standard pydantic
        introspection contract for serialisable options).
        """
        needle = ma.col("x")._node
        members = [ma.t_col("c", unknown={"?"}), 1]
        _, options = encode_membership(needle, members)

        class MuvTuple(RootModel):
            root: tuple[Optional[frozenset], ...]

        muv = options["member_unknown_values"]
        dumped = MuvTuple(muv).model_dump()
        restored = MuvTuple.model_validate(dumped)
        # The first entry's frozenset survives the round-trip
        assert restored.root[0] == frozenset({"?"})
        assert restored.root[1] is None

    def test_options_round_trip_empty_unknowns(self) -> None:
        """All-None unknowns survive the round-trip (no frozenset to lose)."""
        needle = ma.col("x")._node
        _, options = encode_membership(needle, [1, 2, 3])
        muv = options["member_unknown_values"]

        class MuvTuple(RootModel):
            root: tuple[Optional[frozenset], ...]

        dumped = MuvTuple(muv).model_dump()
        restored = MuvTuple.model_validate(dumped)
        assert restored.root == (None, None, None)

    def test_options_round_trip_multiple_distinct_frozensets(self) -> None:
        """Per-position frozenset values survive independently."""
        needle = ma.col("x")._node
        members = [
            ma.t_col("a", unknown={"?"}),
            ma.t_col("b", unknown={-1, -2}),
            ma.t_col("c", unknown={None, "NA"}),
        ]
        _, options = encode_membership(needle, members)
        muv = options["member_unknown_values"]

        class MuvTuple(RootModel):
            root: tuple[Optional[frozenset], ...]

        dumped = MuvTuple(muv).model_dump()
        restored = MuvTuple.model_validate(dumped)
        assert restored.root[0] == frozenset({"?"})
        assert restored.root[1] == frozenset({-1, -2})
        assert restored.root[2] == frozenset({None, "NA"})

    def test_options_introspectable_via_classification(self) -> None:
        """Each entry can be classified as a sentinel-set or no-sentinel.

        This is what downstream tools (the per-backend visitor in Task 5)
        need: an introspection-friendly shape where each position can
        be asked 'does this member carry an unknown-values set, and
        which values?'. A pydantic-friendly tuple of ``frozenset | None``
        is the natural shape.
        """
        needle = ma.col("x")._node
        members = [1, ma.t_col("c", unknown={"?"}), ma.col("y")]
        _, options = encode_membership(needle, members)
        muv = options["member_unknown_values"]

        # Walk positionally and classify each entry
        classified: list[tuple[int, str]] = []
        for i, entry in enumerate(muv):
            if entry is None:
                classified.append((i, "no_sentinel"))
            else:
                classified.append((i, "sentinel"))

        assert classified == [
            (0, "no_sentinel"),
            (1, "sentinel"),
            (2, "no_sentinel"),
        ]

    def test_scalar_function_node_model_dump_preserves_options(self) -> None:
        """The full ``ScalarFunctionNode`` carrying these options dumps
        cleanly (Codex#8 introspection contract for the options dict).
        """
        needle = ma.col("x")._node
        members = [ma.t_col("c", unknown={"?"}), 1]
        arguments, options = encode_membership(needle, members)

        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.T_IS_IN,
            arguments=arguments,
            options=options,
        )
        dumped = node.model_dump()
        # Options dict serialises with the tuple intact
        assert "member_unknown_values" in dumped["options"]
        muv = dumped["options"]["member_unknown_values"]
        assert muv[0] == frozenset({"?"})
        assert muv[1] is None


# =========================================================================
# §12.1 — encoding rule summary (consolidated)
# =========================================================================


class TestEncodeInvariants:
    """Cross-cutting invariants that the brief requires (Codex#1, §12.1)."""

    def test_ma_col_str_lower_not_to_ternary_wrapped(self) -> None:
        """The single most important correctness test.

        A ScalarFunctionNode member (``ma.col("a").str.lower()``) used as
        a membership value MUST NOT be wrapped in TO_TERNARY. The
        existing ternary builder's ``_to_substrait_node`` would
        wrap it — we explicitly avoid that path.
        """
        needle = ma.col("x")._node
        lower_expr = ma.col("a").str.lower()
        arguments, _ = encode_membership(needle, [lower_expr])
        member_node = arguments[1]
        # Raw ScalarFunctionNode, not TO_TERNARY-wrapped
        assert not _is_to_ternary(member_node)
        assert isinstance(member_node, ScalarFunctionNode)
        assert member_node.function_key == FKEY_SUBSTRAIT_SCALAR_STRING.LOWER
        # Walk the tree and assert no TO_TERNARY anywhere
        def _walk(n: ExpressionNode) -> None:
            assert not _is_to_ternary(n), f"unexpected TO_TERNARY in: {n!r}"
            for child in getattr(n, "arguments", []):
                if isinstance(child, ExpressionNode):
                    _walk(child)
        _walk(member_node)

    def test_ma_t_col_member_preserves_sentinel_in_options(self) -> None:
        needle = ma.col("x")._node
        members = [ma.t_col("c", unknown={"?"})]
        _, options = encode_membership(needle, members)
        assert options["member_unknown_values"] == (frozenset({"?"}),)

    def test_ma_t_col_member_node_preserves_sentinel_on_node(self) -> None:
        """The sentinel set must also survive on the member's node itself
        (so backend visitors can read it from the node, not just from the
        options dict).
        """
        needle = ma.col("x")._node
        members = [ma.t_col("c", unknown={"?"})]
        arguments, _ = encode_membership(needle, members)
        member_node = arguments[1]
        assert isinstance(member_node, FieldReferenceNode)
        assert member_node.unknown_values == {"?"}

    def test_all_literal_with_t_col_in_members_uses_no_collect_values(self) -> None:
        """If ANY member is an expression (even a t_col), we do NOT use
        COLLECT_VALUES — the all-scalar-literal path is strictly all
        raw scalars.
        """
        needle = ma.col("x")._node
        members = [1, ma.t_col("c", unknown={"?"}), 3]
        arguments, options = encode_membership(needle, members)
        # 1 needle + 3 members = 4 arguments
        assert len(arguments) == 4
        # No COLLECT_VALUES anywhere
        for arg in arguments[1:]:
            assert not _is_collect_values(arg)
        # Sentinel alignment preserved
        assert options["member_unknown_values"] == (
            None, frozenset({"?"}), None,
        )
