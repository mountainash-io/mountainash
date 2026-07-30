"""Task 6: .list.t_contains — null-aware ternary per-row list-membership.

Acceptance criteria (from task-6 brief):
  * cross-backend: definite ``[1,-1]`` on array cols (polars, ibis)
  * null list row → UNKNOWN(0)
  * ``t_col`` unknown-sentinel needle → UNKNOWN
  * narwhals asserts the declared NW-LIST-01 outcome (BackendCapabilityError)
  * classification (§12.3): ``node.is_ternary`` True; default compile booleanizes;
    ``booleanizer=None`` gives ``-1/0/1``; composes with ``t_and``/``t_or`` WITHOUT
    a spurious ``TO_TERNARY`` wrapper
  * frozenset audit (GLM I6/Codex#11): the (LIST.T_CONTAINS, "item") entry is
    registered in ``test_arg_types_list.TESTED_PARAMS`` and the coverage guard
    remains green
"""
from __future__ import annotations

import pytest

import mountainash as ma
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_nodes import ScalarFunctionNode
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_LIST,
    FKEY_MOUNTAINASH_SCALAR_TERNARY,
)

T_TRUE = 1
T_UNKNOWN = 0
T_FALSE = -1


# Backends that support list/array columns. Polars + ibis-duckdb are the
# references for this op; narwhals is gated by the NW-LIST-01 wildcard fact
# (whole-op BackendCapabilityError at compile time).
LIST_T_CONTAINS_BACKENDS = ["polars", "polars-lazy", "ibis-duckdb"]


# ============================================================================
# Classification (§12.3) — single-backend, AST shape only
# ============================================================================


class TestListTContainsClassification:
    """``list.t_contains`` AST classification and ternary envelope wiring."""

    def test_node_is_ternary(self) -> None:
        """node.is_ternary is True (fkey is in MOUNTAINASH_TERNARY_NON_TERMINAL)."""
        node = ma.col("tags").list.t_contains(2)._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_LIST.T_CONTAINS
        assert node.is_ternary is True

    def test_arguments_shape(self) -> None:
        """AST: arguments are [list-col, item]; no spurious options when no sentinel."""
        node = ma.col("tags").list.t_contains(2)._node
        assert isinstance(node, ScalarFunctionNode)
        assert len(node.arguments) == 2
        assert node.options == {}

    def test_item_unknown_values_propagates_to_options(self) -> None:
        """t_col(needle, unknown={s}) needle propagates ``item_unknown_values`` option."""
        expr = ma.col("tags").list.t_contains(ma.t_col("needle", unknown={-999, None}))
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.options.get("item_unknown_values") == frozenset({-999, None})

    def test_node_is_ternary_non_terminal(self) -> None:
        """``is_ternary_non_terminal`` is True (T_CONTAINS is non-terminal, needs booleanization)."""
        node = ma.col("tags").list.t_contains(2)._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.is_ternary_non_terminal is True

    def test_compose_with_t_and_no_spurious_to_ternary(self) -> None:
        """list.t_contains(...).t_and(...) must NOT wrap the LHS in TO_TERNARY.

        The LHS is already ternary (is_ternary=True), so the ternary builder's
        coercion hook must not double-wrap it. A spurious TO_TERNARY would show
        up as a chain ``t_and(to_ternary(list_t_contains), right)``.
        """
        lhs = ma.col("tags").list.t_contains(2)
        rhs = ma.col("active").t_eq(ma.lit(True))
        composed = lhs.t_and(rhs)
        nodes_with_to_ternary = _find_to_ternary(composed._node)
        assert nodes_with_to_ternary == [], (
            f"Unexpected TO_TERNARY wrapping in t_and chain: {nodes_with_to_ternary}"
        )

    def test_compose_with_t_or_no_spurious_to_ternary(self) -> None:
        """list.t_contains(...).t_or(...) must NOT wrap the LHS in TO_TERNARY."""
        lhs = ma.col("tags").list.t_contains(2)
        rhs = ma.col("active").t_eq(ma.lit(True))
        composed = lhs.t_or(rhs)
        nodes_with_to_ternary = _find_to_ternary(composed._node)
        assert nodes_with_to_ternary == [], (
            f"Unexpected TO_TERNARY wrapping in t_or chain: {nodes_with_to_ternary}"
        )


def _find_to_ternary(node, _found=None):
    """Walk the AST and return every ScalarFunctionNode whose function_key is TO_TERNARY."""
    if _found is None:
        _found = []
    if isinstance(node, ScalarFunctionNode):
        if node.function_key == FKEY_MOUNTAINASH_SCALAR_TERNARY.TO_TERNARY:
            _found.append(node)
        for arg in node.arguments:
            _find_to_ternary(arg, _found)
    return _found


# ============================================================================
# Cross-backend semantics — polars/ibis correct
# ============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", LIST_T_CONTAINS_BACKENDS)
class TestListTContainsCrossBackend:
    """Cross-backend semantics: TRUE/FALSE on definite rows, UNKNOWN on nulls."""

    def test_t_contains_definite_hit_miss(
        self, backend_name, backend_factory, collect_expr
    ):
        """``[1,2,3]`` contains 2 → TRUE(1); misses → FALSE(-1).

        ``collect_expr`` (relation path) returns raw -1/0/1 sentinels — the
        relation visitor does NOT apply auto-booleanize. ``compile()`` does.
        """
        data = {"tags": [[1, 2, 3], [4, 5, 6], [7, 8, 9]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("tags").list.t_contains(2))
        assert actual == [T_TRUE, T_FALSE, T_FALSE], f"[{backend_name}] {actual}"

    def test_t_contains_all_present(self, backend_name, backend_factory, collect_expr):
        """All lists contain 2 → all TRUE(1)."""
        data = {"tags": [[1, 2], [2, 4], [2, 8]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("tags").list.t_contains(2))
        assert actual == [T_TRUE, T_TRUE, T_TRUE], f"[{backend_name}] {actual}"

    def test_t_contains_null_list_row_is_unknown(
        self, backend_name, backend_factory, select_and_extract
    ):
        """Null list row → UNKNOWN(0)."""
        data = {"tags": [[1, 2, 3], None, [4, 5]]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("tags").list.t_contains(2)
        compiled = expr.compile(df, booleanizer=None)
        actual = select_and_extract(df, compiled, "result", backend_name)
        assert actual == [T_TRUE, T_UNKNOWN, T_FALSE], f"[{backend_name}] {actual}"

    def test_t_contains_null_needle_is_unknown(
        self, backend_name, backend_factory, select_and_extract
    ):
        """``ma.col(needle)`` null row → UNKNOWN(0). Uses raw-sentinel inspection."""
        data = {
            "tags": [[1, 2, 3], [1, 2, 3], [1, 2, 3], [1, 2, 3]],
            "needle": [1, None, 2, None],
        }
        df = backend_factory.create(data, backend_name)
        expr = ma.col("tags").list.t_contains(ma.col("needle"))
        compiled = expr.compile(df, booleanizer=None)
        actual = select_and_extract(df, compiled, "result", backend_name)
        assert actual == [T_TRUE, T_UNKNOWN, T_TRUE, T_UNKNOWN], f"[{backend_name}] {actual}"

    def test_t_contains_t_col_sentinel_needle_is_unknown(
        self, backend_name, backend_factory, select_and_extract
    ):
        """``t_col(needle, unknown={s})`` sentinel value → UNKNOWN(0).

        ``t_col`` carries the ``unknown_values`` set on its FieldReferenceNode;
        the ``.list.t_contains`` builder copies it into the
        ``item_unknown_values`` option, which the backend's ternary envelope
        consumes to drive UNKNOWN for sentinel values.
        """
        data = {
            "tags": [[1, 2, 3], [1, 2, 3], [1, 2, 3], [1, 2, 3]],
            "needle": [1, -999, 2, -999],
        }
        df = backend_factory.create(data, backend_name)
        expr = ma.col("tags").list.t_contains(ma.t_col("needle", unknown={-999, None}))
        compiled = expr.compile(df, booleanizer=None)
        actual = select_and_extract(df, compiled, "result", backend_name)
        # Row 0: 1 ∈ [1,2,3] → TRUE(1)
        # Row 1: -999 declared unknown → UNKNOWN(0)
        # Row 2: 2 ∈ [1,2,3] → TRUE(1)
        # Row 3: -999 declared unknown → UNKNOWN(0)
        assert actual == [T_TRUE, T_UNKNOWN, T_TRUE, T_UNKNOWN], f"[{backend_name}] {actual}"

    def test_t_contains_null_needle_with_sentinel_only_is_unknown(
        self, backend_name, backend_factory, select_and_extract
    ):
        """Null needle row → UNKNOWN even when sentinel set omits None.

        Regression for fix #1: the null-needle UNKNOWN trigger is
        unconditional, not gated by the ``item_unknown_values`` set. A
        ``t_col(needle, unknown={-999})`` set that omits ``None`` must still
        mark a null needle row UNKNOWN — the brief states ``UNKNOWN(0) for
        a null list row OR null/declared-unknown needle``.
        """
        data = {
            "tags": [[1, 2, 3], [1, 2, 3], [1, 2, 3], [1, 2, 3], [1, 2, 3]],
            "needle": [1, -999, 2, None, -999],
        }
        df = backend_factory.create(data, backend_name)
        # Sentinel set omits None — but a null needle row must still be UNKNOWN.
        expr = ma.col("tags").list.t_contains(ma.t_col("needle", unknown={-999}))
        compiled = expr.compile(df, booleanizer=None)
        actual = select_and_extract(df, compiled, "result", backend_name)
        # Row 0: 1 ∈ [1,2,3] → TRUE(1)
        # Row 1: -999 declared unknown → UNKNOWN(0)
        # Row 2: 2 ∈ [1,2,3] → TRUE(1)
        # Row 3: NULL → UNKNOWN(0)  (the fix; was incorrectly a match-or-miss)
        # Row 4: -999 declared unknown → UNKNOWN(0)
        assert actual == [T_TRUE, T_UNKNOWN, T_TRUE, T_UNKNOWN, T_UNKNOWN], (
            f"[{backend_name}] {actual}"
        )

    def test_t_contains_null_needle_with_sentinel_set_via_kwarg(
        self, backend_name, backend_factory, select_and_extract
    ):
        """Null needle row → UNKNOWN when item_unknown_values is set with no None.

        Same as the above but constructs the expression via the raw API
        builder option (no t_col, just `col("needle")` with a hand-set
        item_unknown_values option on the node) to prove the
        ``Optional[FrozenSet[Any]]`` kwarg path also handles the null needle.
        """
        data = {
            "tags": [[1, 2, 3], [1, 2, 3], [1, 2, 3]],
            "needle": [1, None, 2],
        }
        df = backend_factory.create(data, backend_name)
        from mountainash.expressions.core.expression_nodes import (
            ScalarFunctionNode,
        )
        from mountainash.expressions.core.expression_system.function_keys.enums import (
            FKEY_MOUNTAINASH_SCALAR_LIST,
        )

        list_node = ma.col("tags")._node
        needle_node = ma.col("needle")._node
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.T_CONTAINS,
            arguments=[list_node, needle_node],
            options={"item_unknown_values": frozenset({-999})},
        )
        from mountainash.expressions.core.expression_api import BooleanExpressionAPI
        expr = BooleanExpressionAPI(node)
        compiled = expr.compile(df, booleanizer=None)
        actual = select_and_extract(df, compiled, "result", backend_name)
        # Row 0: 1 ∈ [1,2,3] → TRUE(1)
        # Row 1: NULL → UNKNOWN(0)  (the fix; set has no None, null is still UNKNOWN)
        # Row 2: 2 ∈ [1,2,3] → TRUE(1)
        assert actual == [T_TRUE, T_UNKNOWN, T_TRUE], f"[{backend_name}] {actual}"

    def test_t_contains_booleanizer_none_returns_raw_sentinels(
        self, backend_name, backend_factory, select_and_extract
    ):
        """``booleanizer=None`` returns the raw -1/0/1 sentinel triple."""
        data = {"tags": [[1, 2, 3], [4, 5, 6], [7, 8, 9]]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("tags").list.t_contains(2)
        compiled = expr.compile(df, booleanizer=None)
        actual = select_and_extract(df, compiled, "result", backend_name)
        assert actual == [T_TRUE, T_FALSE, T_FALSE], f"[{backend_name}] {actual}"

    def test_t_contains_string_lists(self, backend_name, backend_factory, collect_expr):
        """``list.t_contains`` works on string-element lists."""
        data = {"tags": [["python", "rust"], ["python"], ["go", "rust", "python"]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("tags").list.t_contains("python"))
        assert actual == [T_TRUE, T_TRUE, T_TRUE], f"[{backend_name}] {actual}"

    def test_t_contains_t_and_chain(self, backend_name, backend_factory, select_and_extract):
        """``.list.t_contains(...).t_and(boolean_expr)`` composes without TO_TERNARY.

        The list op is already ternary, so ``t_and`` must consume it directly.
        """
        data = {
            "tags": [[1, 2, 3], [1, 2, 3], [4, 5, 6]],
            "active": [True, False, True],
        }
        df = backend_factory.create(data, backend_name)
        expr = ma.col("tags").list.t_contains(2).t_and(ma.col("active").t_eq(ma.lit(True)))
        compiled = expr.compile(df, booleanizer=None)
        actual = select_and_extract(df, compiled, "result", backend_name)
        # Row 0: TRUE(1) AND TRUE(1) = TRUE(1)
        # Row 1: TRUE(1) AND FALSE(-1) = FALSE(-1)
        # Row 2: FALSE(-1) AND TRUE(1) = FALSE(-1)
        assert actual == [T_TRUE, T_FALSE, T_FALSE], f"[{backend_name}] {actual}"


# ============================================================================
# Narwhals — NW-LIST-01 item gate & execution
# ============================================================================


@pytest.mark.parametrize("backend_name", ["narwhals-polars"])
class TestListTContainsNarwhalsGate:
    """``list.t_contains`` item expression argument is gated on narwhals (NW-LIST-01)."""

    def test_t_contains_dynamic_item_raises_backend_capability_error(
        self, backend_name, backend_factory
    ):
        """Narwhals raises ``BackendCapabilityError`` for dynamic item expressions (NW-LIST-01)."""
        data = {"tags": [[1, 2, 3], [4, 5, 6]], "item": [2, 5]}
        df = backend_factory.create(data, backend_name)
        with pytest.raises(BackendCapabilityError) as excinfo:
            ma.col("tags").list.t_contains(ma.col("item")).compile(df)
        msg = str(excinfo.value)
        assert (
            "NW-LIST-01" in msg
            or "literal item" in msg.lower()
            or "list.contains" in msg.lower()
            or "list_t_contains" in msg
        ), f"[{backend_name}] unexpected message: {msg}"

    def test_t_contains_literal_item_executes_on_narwhals_polars(
        self, backend_name, backend_factory
    ):
        """Narwhals-polars permits literal item arguments for list.t_contains."""
        data = {"tags": [[1, 2, 3], [4, 5, 6]]}
        df = backend_factory.create(data, backend_name)
        compiled = ma.col("tags").list.t_contains(2).alias("result").compile(df, booleanizer=None)
        res = df.select(compiled).to_native()
        import polars as pl
        actual = res["result"].to_list() if isinstance(res, pl.DataFrame) else list(res["result"])
        assert actual == [T_TRUE, T_FALSE]
