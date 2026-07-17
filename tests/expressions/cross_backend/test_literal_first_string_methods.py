"""Cross-backend guard for item 226c (literal-receiver string methods).

`lit.str.contains(col)` (concrete string receiver + Deferred column argument)
crashed on ibis with the same root cause as literal-first arithmetic (item 226b
/ Ibis #11742), on the method-dispatch path. The fix (`_lift_deferred_receiver`)
is an **ibis** crash fix — its positive acceptance (all 15 routed methods
executing literal-first) lives in
tests/expressions/backends/ibis/test_string_lift_all_methods.py, because a
*columnar* string argument is not universally supported: pandas, narwhals-*, and
ibis-polars raise a clean capability error for it regardless of receiver (a
separate, pre-existing divergence — NOT 226c).

This module asserts the universally-portable shapes (literal arguments) still
behave identically across every backend — i.e. the receiver-lift did not disturb
any already-working path.
"""
import pytest

import mountainash.expressions as ma
from fixtures.backend_registry import ALL_BACKENDS


@pytest.mark.cross_backend
@pytest.mark.string
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestLiteralFirstStringMethodsNoRegression:
    def test_col_contains_lit_unchanged(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create({"s": ["abcx", "zzq"]}, backend_name)
        assert collect_expr(df, ma.col("s").str.contains(ma.lit("bc"))) == [True, False]

    def test_col_starts_with_lit_unchanged(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create({"s": ["abcx", "zzq"]}, backend_name)
        assert collect_expr(df, ma.col("s").str.starts_with(ma.lit("ab"))) == [True, False]

    def test_col_replace_lit_unchanged(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create({"s": ["abcx", "zzq"]}, backend_name)
        assert collect_expr(df, ma.col("s").str.replace(ma.lit("bc"), ma.lit("X"))) == ["aXx", "zzq"]
