"""Tests for reusable expression combinators."""
from __future__ import annotations

import polars as pl
import mountainash as ma

from mountainash.datacontracts.expressions import (
    any_not_null, all_not_null, any_null, all_null,
    col_equals, col_not_equals, col_in,
    col_le_col, col_ge_col,
)
from mountainash.expressions import BaseExpressionAPI


def _eval(expr, df):
    """Compile and evaluate an expression against a DataFrame."""
    return df.select(expr.compile(df)).to_series().to_list()


class TestNullPatterns:

    def test_any_not_null_all_null(self):
        df = pl.DataFrame({"a": [None], "b": [None]})
        assert _eval(any_not_null("a", "b"), df) == [False]

    def test_any_not_null_one_present(self):
        df = pl.DataFrame({"a": [None], "b": [1]})
        assert _eval(any_not_null("a", "b"), df) == [True]

    def test_all_not_null_all_present(self):
        df = pl.DataFrame({"a": [1], "b": [2]})
        assert _eval(all_not_null("a", "b"), df) == [True]

    def test_all_not_null_one_missing(self):
        df = pl.DataFrame({"a": [1], "b": [None]})
        assert _eval(all_not_null("a", "b"), df) == [False]

    def test_any_null(self):
        df = pl.DataFrame({"a": [1], "b": [None]})
        assert _eval(any_null("a", "b"), df) == [True]

    def test_all_null(self):
        df = pl.DataFrame({"a": [None], "b": [None]})
        assert _eval(all_null("a", "b"), df) == [True]

    def test_all_null_one_present(self):
        df = pl.DataFrame({"a": [None], "b": [1]})
        assert _eval(all_null("a", "b"), df) == [False]

    def test_returns_expression_api(self):
        assert isinstance(any_not_null("a", "b"), BaseExpressionAPI)


class TestValuePatterns:

    def test_col_equals_match(self):
        df = pl.DataFrame({"x": ["Y"]})
        assert _eval(col_equals("x", "Y"), df) == [True]

    def test_col_equals_no_match(self):
        df = pl.DataFrame({"x": ["N"]})
        assert _eval(col_equals("x", "Y"), df) == [False]

    def test_col_not_equals(self):
        df = pl.DataFrame({"x": ["Y"]})
        assert _eval(col_not_equals("x", "N"), df) == [True]

    def test_col_in_match(self):
        df = pl.DataFrame({"x": ["Y"]})
        assert _eval(col_in("x", ["Y", "N"]), df) == [True]

    def test_col_in_no_match(self):
        df = pl.DataFrame({"x": ["X"]})
        assert _eval(col_in("x", ["Y", "N"]), df) == [False]


class TestCrossColumnPatterns:

    def test_col_le_col_true(self):
        df = pl.DataFrame({"a": [1], "b": [2]})
        assert _eval(col_le_col("a", "b"), df) == [True]

    def test_col_le_col_equal(self):
        df = pl.DataFrame({"a": [2], "b": [2]})
        assert _eval(col_le_col("a", "b"), df) == [True]

    def test_col_le_col_false(self):
        df = pl.DataFrame({"a": [3], "b": [2]})
        assert _eval(col_le_col("a", "b"), df) == [False]

    def test_col_ge_col_true(self):
        df = pl.DataFrame({"a": [3], "b": [2]})
        assert _eval(col_ge_col("a", "b"), df) == [True]

    def test_col_ge_col_false(self):
        df = pl.DataFrame({"a": [1], "b": [2]})
        assert _eval(col_ge_col("a", "b"), df) == [False]

    def test_string_comparison(self):
        df = pl.DataFrame({"a": ["2024-01-01"], "b": ["2025-01-01"]})
        assert _eval(col_le_col("a", "b"), df) == [True]
