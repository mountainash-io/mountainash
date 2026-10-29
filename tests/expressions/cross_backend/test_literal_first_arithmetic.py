"""Cross-backend: literal-first binary arithmetic (item 226b / Ibis #11742).

col + lit already worked; lit + col crashed on ibis. Assert executed results
across ALL canonical backends, including the pointbreak string-concat shape.
"""
import pytest

import mountainash.expressions as ma
from fixtures.backend_registry import ALL_BACKENDS


@pytest.mark.cross_backend
@pytest.mark.arithmetic
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestLiteralFirstArithmetic:
    def test_lit_plus_col_numeric(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create({"n": [10, 20, 30]}, backend_name)
        assert collect_expr(df, ma.lit(5) + ma.col("n")) == [15, 25, 35]

    def test_lit_minus_col_order_preserved(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create({"n": [10, 20, 30]}, backend_name)
        assert collect_expr(df, ma.lit(100) - ma.col("n")) == [90, 80, 70]

    def test_lit_times_col(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create({"n": [10, 20, 30]}, backend_name)
        assert collect_expr(df, ma.lit(2) * ma.col("n")) == [20, 40, 60]

    def test_lit_div_col_float(self, backend_name, backend_factory, collect_expr):
        # Float inputs so the result is unambiguous across backends — sidesteps
        # the orthogonal SQLite integer-division divergence (IB-TYPE-02).
        df = backend_factory.create({"f": [10.0, 20.0, 40.0]}, backend_name)
        assert collect_expr(df, ma.lit(100.0) / ma.col("f")) == [10.0, 5.0, 2.5]

    def test_lit_mod_col(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create({"n": [3, 5, 7]}, backend_name)
        assert collect_expr(df, ma.lit(100) % ma.col("n")) == [1, 0, 2]

    def test_lit_pow_col(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create({"n": [2, 3, 4]}, backend_name)
        assert collect_expr(df, ma.lit(2) ** ma.col("n")) == [4, 8, 16]

    def test_lit_floordiv_col(self, backend_name, backend_factory, collect_expr):
        # floor_divide lives in the Mountainash extension arithmetic system, a
        # separate file from the Substrait ops — but the same literal-left crash.
        df = backend_factory.create({"n": [3, 5, 7]}, backend_name)
        assert collect_expr(df, ma.lit(100) // ma.col("n")) == [33, 20, 14]

    def test_lit_str_concat_col(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create({"c": ["x", "y"]}, backend_name)
        assert collect_expr(df, ma.lit("sev/") + ma.col("c")) == ["sev/x", "sev/y"]

    def test_chained_lit_col_lit_col(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create({"ct": ["add", "del"], "ev": ["a", "b"]}, backend_name)
        expr = ma.lit("sev/") + ma.col("ct") + ma.lit("/") + ma.col("ev")
        assert collect_expr(df, expr) == ["sev/add/a", "sev/del/b"]

    def test_nested_deferred_gate_skips_outer_lift(self, backend_name, backend_factory, collect_expr):
        # (lit + col) resolves to a Deferred; the OUTER op sees Deferred-left and
        # must skip lifting — still compiles/executes correctly.
        df = backend_factory.create({"n": [1, 2, 3]}, backend_name)
        assert collect_expr(df, (ma.lit(1) + ma.col("n")) * ma.col("n")) == [2, 6, 12]

    def test_order_sensitivity_guard(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create({"n": [10, 20, 30]}, backend_name)
        lit_first = collect_expr(df, ma.lit(100) - ma.col("n"))
        col_first = collect_expr(df, ma.col("n") - ma.lit(100))
        assert lit_first == [90, 80, 70]
        assert col_first == [-90, -80, -70]
        assert lit_first != col_first

    # --- scope-negatives: paths the gate MUST leave untouched (spec §5.6) ---

    def test_lit_gt_col_still_works(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create({"n": [10, 20, 30]}, backend_name)
        assert collect_expr(df, ma.lit(15) > ma.col("n")) == [True, False, False]

    def test_lit_bool_and_col_still_works(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create({"b": [True, False, True]}, backend_name)
        assert collect_expr(df, ma.lit(True) & ma.col("b")) == [True, False, True]

    def test_col_first_arithmetic_unchanged(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create({"n": [10, 20, 30]}, backend_name)
        assert collect_expr(df, ma.col("n") + ma.lit(5)) == [15, 25, 35]

    def test_both_literal_add_unchanged(self, backend_name, backend_factory, collect_expr):
        # A pure literal+literal expression collapses to a single scalar row on
        # polars/pandas/narwhals but broadcasts to the column length on ibis — a
        # row-count divergence orthogonal to this fix. Assert the VALUE (every
        # element is 7) backend-agnostically; the point is only that the
        # both-concrete path is left unchanged by the literal-left gate.
        df = backend_factory.create({"n": [1, 2]}, backend_name)
        result = collect_expr(df, ma.lit(3) + ma.lit(4))
        assert result and set(result) == {7}

    def test_string_literal_receiver_deferred_arg_now_works(self, backend_name, backend_factory, collect_expr):
        # Formerly the item 226c KNOWN GAP (this asserted it still crashed).
        # Fixed by _lift_deferred_receiver — a literal string receiver with a
        # Deferred argument now compiles on ibis. Full 15-method acceptance lives
        # in backends/ibis/test_string_lift_all_methods.py; here we confirm the
        # headline case on the ibis backends that support columnar string args.
        if backend_name not in ("ibis-duckdb", "ibis-sqlite"):
            pytest.skip("columnar string-arg support is a separate per-backend matrix")
        df = backend_factory.create({"s": ["abcx", "zzz"], "sub": ["bc", "q"]}, backend_name)
        assert collect_expr(df, ma.lit("abcx").str.contains(ma.col("sub"))) == [True, False]
