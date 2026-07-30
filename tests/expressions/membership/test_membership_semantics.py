"""Task 5: Membership semantics tests (build-only + cross-backend).

These tests encode the acceptance criteria from the task-5 brief:
  - build-only: is_in(col), t_is_in(col), t_is_in(ma.lit([1,2])) raise typed errors
  - variadic t_is_in(1,2) == t_is_in([1,2]) (AST)
  - is_in([1,3]) == booleanize(t_is_in([1,3]))
  - expression OR-chain is_in([col_a, col_b])
  - fast-path taken for all-literal members (AST assertion)
  - t_col(needle, unknown={s}) → is_in→False, t_is_in→UNKNOWN
"""
from __future__ import annotations

import pytest

from mountainash import col as ma_col, t_col as ma_t_col
from mountainash.expressions.membership.errors import (
    BareExpressionCollectionError,
)
from mountainash.expressions.core.expression_nodes import (
    LiteralNode,
    ScalarFunctionNode,
)
from fixtures.backend_registry import ALL_BACKENDS


# ============================================================================
# Build-only error tests
# ============================================================================


class TestMembershipBuildErrors:
    """Build-time rejection of bare expression as entire collection."""

    def test_is_in_bare_col_raises(self) -> None:
        with pytest.raises(BareExpressionCollectionError):
            ma_col("x").is_in(ma_col("y"))

    def test_is_not_in_bare_col_raises(self) -> None:
        with pytest.raises(BareExpressionCollectionError):
            ma_col("x").is_not_in(ma_col("y"))

    def test_t_is_in_bare_col_raises(self) -> None:
        with pytest.raises(BareExpressionCollectionError):
            ma_t_col("x").t_is_in(ma_col("y"))

    def test_t_is_in_ma_lit_list_raises(self) -> None:
        import mountainash as ma
        with pytest.raises(BareExpressionCollectionError):
            ma_t_col("x").t_is_in(ma.lit([1, 2]))

    def test_is_in_empty_raises(self) -> None:
        from mountainash.expressions.membership.errors import EmptyMembershipError
        with pytest.raises(EmptyMembershipError):
            ma_col("x").is_in()

    def test_t_is_in_empty_raises(self) -> None:
        from mountainash.expressions.membership.errors import EmptyMembershipError
        with pytest.raises(EmptyMembershipError):
            ma_t_col("x").t_is_in()


class TestMembershipBuildOk:
    """Build-time happy-path: valid invocations produce expression objects."""

    def test_is_in_list_builds(self) -> None:
        import mountainash as ma
        expr = ma_col("x").is_in([1, 2, 3])
        assert isinstance(expr, ma.BaseExpressionAPI)

    def test_is_in_variadic_builds(self) -> None:
        import mountainash as ma
        expr = ma_col("x").is_in(1, 2, 3)
        assert isinstance(expr, ma.BaseExpressionAPI)

    def test_t_is_in_list_builds(self) -> None:
        import mountainash as ma
        expr = ma_col("x").t_is_in([1, 2, 3])
        assert isinstance(expr, ma.BaseExpressionAPI)

    def test_t_is_in_variadic_builds(self) -> None:
        import mountainash as ma
        expr = ma_col("x").t_is_in(1, 2, 3)
        assert isinstance(expr, ma.BaseExpressionAPI)

    def test_t_is_in_variadic_ast_matches_list(self) -> None:
        """Variadic t_is_in(1, 2) produces same AST as t_is_in([1, 2]).

        Both should route through classify_members → encode_membership and
        yield a COLLECT_VALUES wrapper for all-literal collections.
        """
        v = ma_col("x").t_is_in(1, 2)._node
        l = ma_col("x").t_is_in([1, 2])._node
        assert v.arguments == l.arguments
        assert v.options == l.options
        assert v.function_key == l.function_key

    def test_is_in_fast_path_all_literal(self) -> None:
        """All-literal members produce a COLLECT_VALUES wrapper in the AST.

        When there are no expression members, encode_membership wraps literals
        in COLLECT_VALUES. The backend then takes the fast path.
        """
        node = ma_col("x").is_in([1, 2, 3])._node
        assert isinstance(node, ScalarFunctionNode)
        # argument[1] should be a COLLECT_VALUES ScalarFunctionNode
        assert len(node.arguments) == 2
        assert isinstance(node.arguments[1], ScalarFunctionNode)
        assert all(
            isinstance(a, LiteralNode) for a in node.arguments[1].arguments
        )

    def test_is_in_expression_member_no_coll_values(self) -> None:
        """Expression member → no COLLECT_VALUES wrapper; flat positional args."""
        node = ma_col("x").is_in([1, ma_col("y"), 3])._node
        assert isinstance(node, ScalarFunctionNode)
        # arg[0] is needle, arg[1:] are member nodes (not COLLECT_VALUES)
        assert len(node.arguments) == 1 + 3  # needle + 3 members

    def test_is_not_in_list_builds(self) -> None:
        import mountainash as ma
        expr = ma_col("x").is_not_in([1, 2, 3])
        assert isinstance(expr, ma.BaseExpressionAPI)

    def test_is_not_in_variadic_builds(self) -> None:
        import mountainash as ma
        expr = ma_col("x").is_not_in(1, 2, 3)
        assert isinstance(expr, ma.BaseExpressionAPI)

    def test_t_is_not_in_list_builds(self) -> None:
        import mountainash as ma
        expr = ma_col("x").t_is_not_in([1, 2, 3])
        assert isinstance(expr, ma.BaseExpressionAPI)

    def test_t_is_not_in_variadic_builds(self) -> None:
        import mountainash as ma
        expr = ma_col("x").t_is_not_in(1, 2, 3)
        assert isinstance(expr, ma.BaseExpressionAPI)


# ============================================================================
# Cross-backend semantics
# ============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestMembershipCrossBackend:
    """Semantics tests that must produce identical results across all backends."""

    def test_is_in_basic_false_true_false(self, backend_name, backend_factory, collect_expr):
        data = {"val": [1, 2, 3, 4, 5]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma_col("val").is_in([1, 3]))
        assert actual == [True, False, True, False, False], (
            f"[{backend_name}] {actual}"
        )

    def test_is_not_in_basic(self, backend_name, backend_factory, collect_expr):
        data = {"val": [1, 2, 3, 4, 5]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma_col("val").is_not_in([1, 3]))
        assert actual == [False, True, False, True, True], (
            f"[{backend_name}] {actual}"
        )

    def test_is_in_booleanize_equals_t_is_in(self, backend_name, backend_factory, collect_expr):
        """is_in([1,3]) == booleanize(t_is_in([1,3])) under t_is_true."""
        data = {"val": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)
        bool_result = collect_expr(df, ma_col("val").is_in([1, 3]))
        ternary_result = collect_expr(df, ma_col("val").t_is_in([1, 3]))
        # booleanize: TRUE(1)→True, UNKNOWN(0)→False, FALSE(-1)→False
        booleanized = [v == 1 for v in ternary_result]
        assert bool_result == booleanized, (
            f"[{backend_name}] bool={bool_result}, booleanized={booleanized}"
        )

    def test_is_in_with_null_needle(self, backend_name, backend_factory, collect_expr):
        data = {"val": [1, None, 3, None, 5]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma_col("val").is_in([1, 3]))
        # null needle → is_unknown → is_in→False
        assert actual[0] is True
        assert actual[1] is False, f"[{backend_name}] null row expected False, got {actual[1]}"
        assert actual[2] is True
        assert actual[3] is False, f"[{backend_name}] null row expected False, got {actual[3]}"
        assert actual[4] is False

    def test_t_is_in_with_null_needle(self, backend_name, backend_factory, collect_expr):
        data = {"val": [1, None, 3, None, 5]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma_col("val").t_is_in([1, 3]))
        # null → UNKNOWN=0; match→TRUE=1; no match→FALSE=-1
        assert actual[0] == 1
        assert actual[1] == 0, f"[{backend_name}] null row expected UNKNOWN(0), got {actual[1]}"
        assert actual[2] == 1
        assert actual[3] == 0
        assert actual[4] == -1

    def test_is_in_expression_or_chain(self, backend_name, backend_factory, collect_expr):
        """Expression member OR-chain: is_in([col_a, col_b]).

        needle in {col_a, col_b} → needle == col_a OR needle == col_b.
        """
        data = {"needle": [1, 2, 3, 4, 5], "a": [1, 3, 5, 7, 9], "b": [2, 4, 6, 8, 10]}
        df = backend_factory.create(data, backend_name)
        import mountainash as ma
        actual = collect_expr(df, ma_col("needle").is_in([ma_col("a"), ma_col("b")]))
        # row 0: needle=1, a=1 match → True
        # row 1: needle=2, a=3 no, b=4 no → False
        # row 2: needle=3, a=5 no, b=6 no → False
        # row 3: needle=4, a=7 no, b=8 no → False
        # row 4: needle=5, a=9 no, b=10 no → False
        assert actual == [True, False, False, False, False], (
            f"[{backend_name}] {actual}"
        )

    def test_t_is_in_expression_or_chain(self, backend_name, backend_factory, collect_expr):
        """Ternary OR-chain: t_is_in([col_a, col_b])."""
        data = {"needle": [1, 2, 3, 4, 5], "a": [1, 3, 5, 7, 9], "b": [2, 4, 6, 8, 10]}
        df = backend_factory.create(data, backend_name)
        import mountainash as ma
        actual = collect_expr(df, ma_col("needle").t_is_in([ma_col("a"), ma_col("b")]))
        # TRUE=1, FALSE=-1
        assert actual == [1, -1, -1, -1, -1], (
            f"[{backend_name}] {actual}"
        )

    def test_is_in_sentinel_unknown(self, backend_name, backend_factory, collect_expr):
        """t_col with unknown_values → sentinel values treated as UNKNOWN.

        t_col(needle, unknown={s}) → is_in should return False for the
        sentinel row (booleanize of UNKNOWN → False).
        """
        data = {"val": ["a", "s", "b", None, "c"]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma_t_col("val", unknown={"s"}).is_in(["a", "b"]))
        assert actual == [True, False, True, False, False], (
            f"[{backend_name}] {actual}"
        )

    def test_t_is_in_sentinel_unknown(self, backend_name, backend_factory, collect_expr):
        """t_col with unknown_values → sentinel row → t_is_in → UNKNOWN(0)."""
        data = {"val": ["a", "s", "b", None, "c"]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma_t_col("val", unknown={"s"}).t_is_in(["a", "b"]))
        # TRUE=1, UNKNOWN=0, FALSE=-1
        assert actual == [1, 0, 1, 0, -1], (
            f"[{backend_name}] {actual}"
        )

    def test_is_in_variadic_equivalent_to_list(self, backend_name, backend_factory, collect_expr):
        """is_in(1, 2, 3) produces same result as is_in([1, 2, 3])."""
        data = {"val": [1, 2, 3, 4, 5]}
        df = backend_factory.create(data, backend_name)
        list_result = collect_expr(df, ma_col("val").is_in([1, 2, 3]))
        variadic_result = collect_expr(df, ma_col("val").is_in(1, 2, 3))
        assert list_result == variadic_result, (
            f"[{backend_name}] list={list_result}, variadic={variadic_result}"
        )

    def test_is_not_in_with_null_needle(self, backend_name, backend_factory, collect_expr):
        """is_not_in: null needle → is_unknown → False (never "not False")."""
        data = {"val": [1, None, 3]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma_col("val").is_not_in([1, 3]))
        # row 0: 1 is in set → is_in=True, is_not_in=False
        # row 1: null → unknown → is_not_in=False
        # row 2: 3 is in set → is_in=True, is_not_in=False
        assert actual == [False, False, False], (
            f"[{backend_name}] {actual}"
        )

    def test_is_not_in_no_match(self, backend_name, backend_factory, collect_expr):
        """is_not_in with no matches → all True (except null)."""
        data = {"val": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma_col("val").is_not_in([99, 100]))
        assert actual == [True, True, True], (
            f"[{backend_name}] {actual}"
        )

    def test_is_in_with_null_in_members(self, backend_name, backend_factory, collect_expr):
        """Member list contains None: null member treated as unknown."""
        data = {"val": [1, None, 3, 4]}
        df = backend_factory.create(data, backend_name)
        # needle=1, members=[None, 3]
        # row 0: 1 is not None, not 3 → not in → False
        # row 1: null→is_unknown→False
        # row 2: 3==3→True
        # row 3: 4 matches nothing→False
        actual = collect_expr(df, ma_col("val").is_in([None, 3]))
        assert actual == [False, False, True, False], (
            f"[{backend_name}] {actual}"
        )
