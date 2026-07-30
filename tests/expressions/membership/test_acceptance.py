"""Task 8: Consolidated cross-backend acceptance suite for membership unification.

Proves the end-to-end membership guarantees across all backends:
  1. NEVER-SILENT build-raise for bare expressions, empty, nested, or native members.
  2. Migration paths correct (.list.contains, .list.t_contains, NW-LIST-01 gate on narwhals).
  3. FULL §7 null truth table for all four ops (is_in/is_not_in/t_is_in/t_is_not_in)
     INCLUDING the SQL-critical row x="a", members=["b", None] → t_is_not_in=UNKNOWN, is_not_in=False.
  4. INVARIANT is_in ≡ booleanize(t_is_in) AND is_not_in ≡ booleanize(t_is_not_in) over shapes × backends.
  5. FAST-PATH EQUIVALENCE property test (Codex#12): literal COLLECT_VALUES path vs ma.lit(...) path.
  6. Regressions: is_in([...]) and t_col(...).is_in(...) continue working.
"""
from __future__ import annotations

import math
import polars as pl
import pytest

import mountainash as ma
from mountainash import col as ma_col, lit as ma_lit, t_col as ma_t_col
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.membership.errors import (
    BareExpressionCollectionError,
    EmptyMembershipError,
    NativeExprMemberError,
    NestedCollectionError,
    UnsupportedCollectionError,
)

from fixtures.backend_registry import ALL_BACKENDS

T_TRUE = 1
T_UNKNOWN = 0
T_FALSE = -1

LIST_BACKENDS = ["polars", "polars-lazy", "ibis-duckdb"]


# ============================================================================
# 1. NEVER-SILENT build-time raise tests
# ============================================================================


class TestNeverSilentBuildRaise:
    """Assert typed error is raised at BUILD for invalid membership invocations."""

    def test_is_in_bare_col_raises(self) -> None:
        with pytest.raises(BareExpressionCollectionError):
            ma_col("x").is_in(ma_col("y"))

    def test_t_is_in_bare_col_raises(self) -> None:
        with pytest.raises(BareExpressionCollectionError):
            ma_t_col("x").t_is_in(ma_col("y"))

    def test_is_in_scalar_col_raises(self) -> None:
        with pytest.raises(BareExpressionCollectionError):
            ma_col("x").is_in(ma_col("y"))

    def test_is_in_ma_lit_list_raises(self) -> None:
        with pytest.raises(BareExpressionCollectionError):
            ma_col("x").is_in(ma_lit([1, 2]))

    def test_t_is_in_ma_lit_list_raises(self) -> None:
        with pytest.raises(BareExpressionCollectionError):
            ma_t_col("x").t_is_in(ma_lit([1, 2]))

    def test_is_not_in_bare_col_raises(self) -> None:
        with pytest.raises(BareExpressionCollectionError):
            ma_col("x").is_not_in(ma_col("y"))

    def test_t_is_not_in_bare_col_raises(self) -> None:
        with pytest.raises(BareExpressionCollectionError):
            ma_t_col("x").t_is_not_in(ma_col("y"))

    def test_is_in_empty_raises(self) -> None:
        with pytest.raises(EmptyMembershipError):
            ma_col("x").is_in([])

    def test_t_is_in_empty_raises(self) -> None:
        with pytest.raises(EmptyMembershipError):
            ma_t_col("x").t_is_in([])

    def test_is_in_nested_collection_raises(self) -> None:
        with pytest.raises(NestedCollectionError):
            ma_col("x").is_in([[1, 2], [3, 4]])

    def test_is_in_unsupported_type_raises(self) -> None:
        with pytest.raises(UnsupportedCollectionError):
            ma_col("x").is_in(range(5))

        with pytest.raises(UnsupportedCollectionError):
            ma_col("x").is_in({"a": 1})

    def test_is_in_native_expr_member_raises(self) -> None:
        with pytest.raises(NativeExprMemberError):
            ma_col("x").is_in([pl.col("y")])


# ============================================================================
# 2. Migration paths (.list.contains & .list.t_contains)
# ============================================================================


class TestMigrationPaths:
    """Verify migration paths .list.contains (boolean) and .list.t_contains (ternary)."""

    @pytest.mark.cross_backend
    @pytest.mark.parametrize("backend_name", LIST_BACKENDS)
    def test_list_contains_boolean_cross_backend(
        self, backend_name, backend_factory, collect_expr
    ):

        data = {"tags": [[1, 2, 3], [4, 5, 6], [7, 8, 9]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma_col("tags").list.contains(2))
        assert actual == [True, False, False], f"[{backend_name}] {actual}"

    @pytest.mark.cross_backend
    @pytest.mark.parametrize("backend_name", LIST_BACKENDS)
    def test_list_t_contains_ternary_cross_backend(
        self, backend_name, backend_factory, select_and_extract
    ):
        data = {"tags": [[1, 2, 3], None, [4, 5, 6]]}
        df = backend_factory.create(data, backend_name)
        expr = ma_col("tags").list.t_contains(2)
        compiled = expr.compile(df, booleanizer=None)
        actual = select_and_extract(df, compiled, "result", backend_name)
        assert actual == [T_TRUE, T_UNKNOWN, T_FALSE], f"[{backend_name}] {actual}"

    @pytest.mark.parametrize("backend_name", ["narwhals-polars"])
    def test_list_contains_narwhals_nw_list_01_gate(
        self, backend_name, backend_factory
    ):
        data = {"tags": [[1, 2, 3], [4, 5, 6]], "item": [2, 5]}
        df = backend_factory.create(data, backend_name)
        with pytest.raises(BackendCapabilityError) as excinfo:
            ma_col("tags").list.contains(ma_col("item")).compile(df)
        assert "NW-LIST-01" in str(excinfo.value) or "literal item" in str(
            excinfo.value
        ).lower()

    @pytest.mark.parametrize("backend_name", ["narwhals-polars"])
    def test_list_t_contains_narwhals_nw_list_01_gate(
        self, backend_name, backend_factory
    ):
        data = {"tags": [[1, 2, 3], [4, 5, 6]], "item": [2, 5]}
        df = backend_factory.create(data, backend_name)
        with pytest.raises(BackendCapabilityError) as excinfo:
            ma_col("tags").list.t_contains(ma_col("item")).compile(df)
        assert "NW-LIST-01" in str(excinfo.value) or "literal item" in str(
            excinfo.value
        ).lower()


# ============================================================================
# 3. FULL §7 Null Truth Table for all four ops
# ============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestFullNullTruthTable:
    """Full §7 null truth table across all 4 ops (is_in, is_not_in, t_is_in, t_is_not_in)."""

    def test_null_truth_table_literal_members(
        self, backend_name, backend_factory, select_and_extract, collect_expr
    ):
        """Tests the full truth table including the SQL-critical row x='a', members=['b', None].

        Table rows:
          Row 0: needle="a", members=["a", "b"]       → t_is_in=TRUE,  t_is_not_in=FALSE, is_in=True,  is_not_in=False
          Row 1: needle="c", members=["a", "b"]       → t_is_in=FALSE, t_is_not_in=TRUE,  is_in=False, is_not_in=True
          Row 2: needle="a", members=["b", None]      → t_is_in=UNKN,  t_is_not_in=UNKN,  is_in=False, is_not_in=False (SQL-CRITICAL!)
          Row 3: needle=None, members=["a", "b"]      → t_is_in=UNKN,  t_is_not_in=UNKN,  is_in=False, is_not_in=False
          Row 4: needle=None, members=["a", None]     → t_is_in=UNKN,  t_is_not_in=UNKN,  is_in=False, is_not_in=False
        """
        # Testing against members=["b", None] for row 2 (SQL-critical)
        data = {"val": ["a", "c", "a", None, None]}
        df = backend_factory.create(data, backend_name)

        # 1. t_is_in on members=["b", None]
        expr_t_in = ma_col("val").t_is_in([ "b", None ])
        t_in_res = select_and_extract(
            df, expr_t_in.compile(df, booleanizer=None), "res", backend_name
        )
        # Row 0: "a" in ["b", None] → 0 (UNKNOWN)
        # Row 1: "c" in ["b", None] → 0 (UNKNOWN)
        # Row 2: "a" in ["b", None] → 0 (UNKNOWN, SQL-critical)
        # Row 3: None in ["b", None] → 0 (UNKNOWN)
        # Row 4: None in ["b", None] → 0 (UNKNOWN)
        assert t_in_res == [T_UNKNOWN, T_UNKNOWN, T_UNKNOWN, T_UNKNOWN, T_UNKNOWN], (
            f"[{backend_name}] t_is_in: {t_in_res}"
        )

        # 2. t_is_not_in on members=["b", None]
        expr_t_not_in = ma_col("val").t_is_not_in([ "b", None ])
        t_not_in_res = select_and_extract(
            df, expr_t_not_in.compile(df, booleanizer=None), "res", backend_name
        )
        assert t_not_in_res == [
            T_UNKNOWN,
            T_UNKNOWN,
            T_UNKNOWN,
            T_UNKNOWN,
            T_UNKNOWN,
        ], f"[{backend_name}] t_is_not_in: {t_not_in_res}"

        # 3. is_in on members=["b", None]
        is_in_res = collect_expr(df, ma_col("val").is_in(["b", None]))
        assert is_in_res == [False, False, False, False, False], (
            f"[{backend_name}] is_in: {is_in_res}"
        )

        # 4. is_not_in on members=["b", None] -- SQL-CRITICAL: "a" not in ["b", None] is FALSE!
        is_not_in_res = collect_expr(df, ma_col("val").is_not_in(["b", None]))
        assert is_not_in_res == [False, False, False, False, False], (
            f"[{backend_name}] is_not_in: {is_not_in_res}"
        )

    def test_null_truth_table_definite_members(
        self, backend_name, backend_factory, select_and_extract, collect_expr
    ):
        """Test truth table when members are purely definite ["a", "b"]."""
        data = {"val": ["a", "c", None]}
        df = backend_factory.create(data, backend_name)

        expr_t_in = ma_col("val").t_is_in(["a", "b"])
        t_in_res = select_and_extract(
            df, expr_t_in.compile(df, booleanizer=None), "res", backend_name
        )
        assert t_in_res == [T_TRUE, T_FALSE, T_UNKNOWN], (
            f"[{backend_name}] t_is_in: {t_in_res}"
        )

        expr_t_not_in = ma_col("val").t_is_not_in(["a", "b"])
        t_not_in_res = select_and_extract(
            df, expr_t_not_in.compile(df, booleanizer=None), "res", backend_name
        )
        assert t_not_in_res == [T_FALSE, T_TRUE, T_UNKNOWN], (
            f"[{backend_name}] t_is_not_in: {t_not_in_res}"
        )

        is_in_res = collect_expr(df, ma_col("val").is_in(["a", "b"]))
        assert is_in_res == [True, False, False], (
            f"[{backend_name}] is_in: {is_in_res}"
        )

        is_not_in_res = collect_expr(df, ma_col("val").is_not_in(["a", "b"]))
        assert is_not_in_res == [False, True, False], (
            f"[{backend_name}] is_not_in: {is_not_in_res}"
        )

    def test_member_sentinel_unknown(
        self, backend_name, backend_factory, select_and_extract, collect_expr
    ):
        """Member-unknown sentinels via t_col(needle/member, unknown={...})."""
        data = {"needle": ["a", "s", "b"], "m1": ["b", "b", "b"]}
        df = backend_factory.create(data, backend_name)

        # needle is sentinel "s" -> UNKNOWN
        expr_t_in = ma_t_col("needle", unknown={"s"}).t_is_in([ma_col("m1"), "c"])
        t_in_res = select_and_extract(
            df, expr_t_in.compile(df, booleanizer=None), "res", backend_name
        )
        assert t_in_res == [T_FALSE, T_UNKNOWN, T_TRUE], (
            f"[{backend_name}] t_is_in sentinel: {t_in_res}"
        )

        is_in_res = collect_expr(
            df, ma_t_col("needle", unknown={"s"}).is_in([ma_col("m1"), "c"])
        )
        assert is_in_res == [False, False, True], (
            f"[{backend_name}] is_in sentinel: {is_in_res}"
        )


# ============================================================================
# 4. INVARIANTS: is_in ≡ booleanize(t_is_in) AND is_not_in ≡ booleanize(t_is_not_in)
# ============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestMembershipInvariants:
    """Verify is_in ≡ booleanize(t_is_in) AND is_not_in ≡ booleanize(t_is_not_in) under t_is_true."""

    def test_invariant_literal_members(
        self, backend_name, backend_factory, select_and_extract, collect_expr
    ):
        data = {"val": [1, 2, 3, None, 5]}
        df = backend_factory.create(data, backend_name)

        bool_in = collect_expr(df, ma_col("val").is_in([1, 3]))
        ternary_in = select_and_extract(
            df,
            ma_col("val").t_is_in([1, 3]).compile(df, booleanizer=None),
            "res",
            backend_name,
        )
        assert bool_in == [v == T_TRUE for v in ternary_in], f"[{backend_name}] is_in invariant failure"

        bool_not_in = collect_expr(df, ma_col("val").is_not_in([1, 3]))
        ternary_not_in = select_and_extract(
            df,
            ma_col("val").t_is_not_in([1, 3]).compile(df, booleanizer=None),
            "res",
            backend_name,
        )
        assert bool_not_in == [v == T_TRUE for v in ternary_not_in], f"[{backend_name}] is_not_in invariant failure"

    def test_invariant_variadic_members(
        self, backend_name, backend_factory, select_and_extract, collect_expr
    ):
        data = {"val": ["a", "b", "c", None]}
        df = backend_factory.create(data, backend_name)

        bool_in = collect_expr(df, ma_col("val").is_in("a", "c"))
        ternary_in = select_and_extract(
            df,
            ma_col("val").t_is_in("a", "c").compile(df, booleanizer=None),
            "res",
            backend_name,
        )
        assert bool_in == [v == T_TRUE for v in ternary_in]

        bool_not_in = collect_expr(df, ma_col("val").is_not_in("a", "c"))
        ternary_not_in = select_and_extract(
            df,
            ma_col("val").t_is_not_in("a", "c").compile(df, booleanizer=None),
            "res",
            backend_name,
        )
        assert bool_not_in == [v == T_TRUE for v in ternary_not_in]

    def test_invariant_expression_members(
        self, backend_name, backend_factory, select_and_extract, collect_expr
    ):
        data = {"needle": [1, 2, 3, None], "a": [1, 5, 3, 4], "b": [9, 2, 8, 4]}
        df = backend_factory.create(data, backend_name)

        bool_in = collect_expr(
            df, ma_col("needle").is_in([ma_col("a"), ma_col("b")])
        )
        ternary_in = select_and_extract(
            df,
            ma_col("needle")
            .t_is_in([ma_col("a"), ma_col("b")])
            .compile(df, booleanizer=None),
            "res",
            backend_name,
        )
        assert bool_in == [v == T_TRUE for v in ternary_in]

        bool_not_in = collect_expr(
            df, ma_col("needle").is_not_in([ma_col("a"), ma_col("b")])
        )
        ternary_not_in = select_and_extract(
            df,
            ma_col("needle")
            .t_is_not_in([ma_col("a"), ma_col("b")])
            .compile(df, booleanizer=None),
            "res",
            backend_name,
        )
        assert bool_not_in == [v == T_TRUE for v in ternary_not_in]


# ============================================================================
# 5. FAST-PATH EQUIVALENCE property test (Codex#12)
# ============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestFastPathEquivalence:
    """Property test proving COLLECT_VALUES fast-path and ma.lit(...) member path yield identical results."""

    def test_fast_path_equivalence_portable_values(
        self, backend_name, backend_factory, select_and_extract, collect_expr
    ):
        data = {"val": [1, 2, 3, 4, 5]}
        df = backend_factory.create(data, backend_name)

        # 1. raw literals → COLLECT_VALUES path
        fast_t_in = select_and_extract(
            df,
            ma_col("val").t_is_in([1, 3]).compile(df, booleanizer=None),
            "res",
            backend_name,
        )
        fast_bool_in = collect_expr(df, ma_col("val").is_in([1, 3]))

        # 2. ma.lit(...) members → flat expression member path
        slow_t_in = select_and_extract(
            df,
            ma_col("val")
            .t_is_in([ma_lit(1), ma_lit(3)])
            .compile(df, booleanizer=None),
            "res",
            backend_name,
        )
        slow_bool_in = collect_expr(
            df, ma_col("val").is_in([ma_lit(1), ma_lit(3)])
        )

        assert fast_t_in == slow_t_in, f"[{backend_name}] t_is_in fast-path mismatch"
        assert fast_bool_in == slow_bool_in, f"[{backend_name}] is_in fast-path mismatch"

    def test_fast_path_equivalence_null_needle(
        self, backend_name, backend_factory, select_and_extract, collect_expr
    ):
        data = {"val": [1, None, 3, None]}
        df = backend_factory.create(data, backend_name)

        fast_t_in = select_and_extract(
            df,
            ma_col("val").t_is_in([1, 3]).compile(df, booleanizer=None),
            "res",
            backend_name,
        )
        slow_t_in = select_and_extract(
            df,
            ma_col("val")
            .t_is_in([ma_lit(1), ma_lit(3)])
            .compile(df, booleanizer=None),
            "res",
            backend_name,
        )
        assert fast_t_in == slow_t_in

    def test_fast_path_equivalence_nan_values(
        self, backend_name, backend_factory, select_and_extract, collect_expr
    ):
        data = {"val": [1.0, float("nan"), 3.0, 4.0]}
        df = backend_factory.create(data, backend_name)

        fast_bool = collect_expr(df, ma_col("val").is_in([1.0, 3.0]))
        slow_bool = collect_expr(
            df, ma_col("val").is_in([ma_lit(1.0), ma_lit(3.0)])
        )
        assert fast_bool == slow_bool

    def test_fast_path_equivalence_heterogeneous_values(
        self, backend_name, backend_factory, select_and_extract, collect_expr
    ):
        data = {"val": ["a", "b", "c", "d"]}
        df = backend_factory.create(data, backend_name)

        fast_t_in = select_and_extract(
            df,
            ma_col("val").t_is_in(["a", "c"]).compile(df, booleanizer=None),
            "res",
            backend_name,
        )
        slow_t_in = select_and_extract(
            df,
            ma_col("val")
            .t_is_in([ma_lit("a"), ma_lit("c")])
            .compile(df, booleanizer=None),
            "res",
            backend_name,
        )
        assert fast_t_in == slow_t_in


# ============================================================================
# 6. Regressions
# ============================================================================


class TestMembershipRegressions:
    """Regression assertions for traditional API patterns."""

    def test_is_in_list_regression(self) -> None:
        expr = ma_col("x").is_in([1, 2, 3])
        assert expr is not None

    def test_t_col_is_in_regression(self) -> None:
        expr = ma_t_col("x").is_in([1, 2, 3])
        assert expr is not None

    def test_t_col_t_is_in_regression(self) -> None:
        expr = ma_t_col("x", unknown={"s"}).t_is_in(["a", "b"])
        assert expr is not None
