"""Build-time validation tests for regex_contains / regex_match.

Per arguments-vs-options.md (ENFORCED), the regex pattern is a
universally-literal parameter and MUST be passed as a literal `str`.
The API builder rejects non-string inputs at build time with a clear
TypeError pointing at the Relation.compile() escape hatch for
dynamic-pattern use cases.
"""
from __future__ import annotations

import pytest

import mountainash as ma


def test_regex_contains_rejects_expression_pattern():
    """Passing a column reference as the pattern raises TypeError."""
    with pytest.raises(TypeError) as excinfo:
        ma.col("name").str.regex_contains(ma.col("regex_col"))

    msg = str(excinfo.value)
    assert "literal str" in msg
    assert "compile()" in msg


def test_regex_contains_rejects_lit_wrapped_pattern():
    """Even ma.lit("foo") wrapping a literal must be rejected.

    The strict semantics: pattern is `str` only, full stop. Wrapping
    a literal in an expression node loses the build-time type check
    and is therefore disallowed.
    """
    with pytest.raises(TypeError) as excinfo:
        ma.col("name").str.regex_contains(ma.lit("foo"))

    msg = str(excinfo.value)
    assert "literal str" in msg


def test_regex_match_rejects_expression_pattern():
    """regex_match delegates to regex_contains; the same TypeError flows through."""
    with pytest.raises(TypeError) as excinfo:
        ma.col("name").str.regex_match(ma.col("regex_col"))

    msg = str(excinfo.value)
    assert "literal str" in msg
