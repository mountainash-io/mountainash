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
