"""Every routed ibis string method must accept a literal receiver + Deferred
argument (item 226c) — the method-call analog of item 226b.

Before the fix, `ma.lit("abcx").str.contains(ma.col("sub"))` (concrete string
receiver + Deferred column argument) crashed at compile time with
SignatureValidationError (or TypeError for int-count args). The receiver-lift
resolves the whole family. These assertions execute on ibis-duckdb; the
portable subset is additionally covered cross-backend in
tests/expressions/cross_backend/test_literal_first_string_methods.py.
"""
import ibis
import pytest

import mountainash.expressions as ma


@pytest.fixture
def t():
    con = ibis.duckdb.connect()
    return con.create_table(
        "t",
        {
            "s": ["abcx", "zzq"],
            "sub": ["bc", "q"],
            "rep": ["X", "Y"],
            "n": [2, 3],
            "sep": ["b", "z"],
        },
    )


def _run(t, expr):
    be = expr.compile(t)
    return t.select(be.name("r"))["r"].execute().tolist()


@pytest.mark.parametrize(
    "build, expected",
    [
        (lambda: ma.lit("abcx").str.contains(ma.col("sub")), [True, False]),
        (lambda: ma.lit("abcx").str.starts_with(ma.col("sub")), [False, False]),
        (lambda: ma.lit("abcx").str.ends_with(ma.col("sub")), [False, False]),
        (lambda: ma.lit("abcx").str.strpos(ma.col("sub")), [2, 0]),
        (lambda: ma.lit("abcx").str.like(ma.col("sub")), [False, False]),
        (lambda: ma.lit("a-b").str.string_split(ma.col("sep")), [["a-", ""], ["a-b"]]),
        (lambda: ma.lit("abcx").str.replace(ma.col("sub"), ma.col("rep")), ["aXx", "abcx"]),
        (lambda: ma.lit("abcx").str.regexp_replace(ma.col("sub"), ma.col("rep")), ["aXx", "abcx"]),
        (lambda: ma.lit("abcx").str.regexp_match_substring(ma.col("sub")), ["bc", ""]),
        (lambda: ma.lit("ab").str.repeat(ma.col("n")), ["abab", "ababab"]),
        (lambda: ma.lit("ab").str.lpad(ma.col("n")), ["ab", " ab"]),
        (lambda: ma.lit("ab").str.rpad(ma.col("n")), ["ab", "ab "]),
        (lambda: ma.lit("abcx").str.substring(ma.col("n")), ["cx", "x"]),
        (lambda: ma.lit("abcx").str.left(ma.col("n")), ["ab", "abc"]),
        (lambda: ma.lit("abcx").str.right(ma.col("n")), ["cx", "bcx"]),
    ],
)
def test_literal_receiver_deferred_arg_executes(t, build, expected):
    assert _run(t, build()) == expected
