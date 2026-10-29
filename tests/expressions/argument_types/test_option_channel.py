"""Verify option channel: accepts raw Python values, rejects expressions at API builder level."""
from __future__ import annotations

import pytest

import mountainash as ma


def test_option_rejects_expression_on_round_decimals():
    """round() decimals is an option — passing an expression should fail at the API builder level."""
    with pytest.raises((TypeError, ValueError, AttributeError)):
        ma.col("x").round(ma.col("n"))  # type: ignore[arg-type]


def test_option_rejects_expression_on_alias():
    """name.alias takes a str option — passing an expression should fail."""
    with pytest.raises((TypeError, ValueError, AttributeError)):
        ma.col("x").name.alias(ma.col("y"))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "build",
    [
        lambda: ma.col("x").str.regexp_match_substring(r"\d+", group=ma.col("g")),
        lambda: ma.col("x").str.regexp_match_substring(r"\d+", position=ma.col("p")),
        lambda: ma.col("x").str.regexp_match_substring(r"\d+", occurrence=ma.col("o")),
        lambda: ma.col("x").str.regexp_match_substring_all(r"\d+", position=ma.col("p")),
        lambda: ma.col("x").str.regexp_strpos(r"\d+", occurrence=ma.col("o")),
        lambda: ma.col("x").str.regexp_count_substring(r"\d+", position=ma.col("p")),
        lambda: ma.col("x").str.regexp_replace(r"\d+", "X", position=ma.col("p")),
        lambda: ma.col("x").str.regexp_replace(r"\d+", "X", occurrence=ma.col("o")),
    ],
)
def test_regexp_positional_options_reject_expression(build):
    """position/occurrence/group are literal-only options (arguments-vs-options.md):
    passing an expression must fail at the API-builder boundary, not silently no-op."""
    with pytest.raises(TypeError):
        build()


@pytest.mark.parametrize(
    "build",
    [
        lambda: ma.col("x").str.regexp_match_substring(r"\d+", group="2"),
        lambda: ma.col("x").str.regexp_strpos(r"\d+", position="1"),
        lambda: ma.col("x").str.regexp_replace(r"\d+", "X", occurrence=True),
    ],
)
def test_regexp_positional_options_reject_nonint_literal(build):
    """A str or bool is not a valid literal int for these options (bool excluded)."""
    with pytest.raises(TypeError):
        build()


@pytest.mark.parametrize(
    "build",
    [
        # case_sensitive across the non-regexp and regexp flag builders
        lambda: ma.col("x").str.contains("h", case_sensitive=ma.col("c")),
        lambda: ma.col("x").str.like("%h%", case_sensitive=ma.col("c")),
        lambda: ma.col("x").str.regexp_match_substring(r"\d+", case_sensitive=ma.col("c")),
        lambda: ma.col("x").str.regexp_replace(r"\d+", "X", case_sensitive=ma.col("c")),
        lambda: ma.col("x").str.regexp_string_split(r"\d+", case_sensitive=ma.col("c")),
        # multiline / dotall flags
        lambda: ma.col("x").str.regexp_match_substring(r"\d+", multiline=ma.col("m")),
        lambda: ma.col("x").str.regexp_match_substring(r"\d+", dotall=ma.col("d")),
        lambda: ma.col("x").str.regexp_replace(r"\d+", "X", multiline=ma.col("m")),
        lambda: ma.col("x").str.regexp_string_split(r"\d+", dotall=ma.col("d")),
        # an arbitrary non-bool literal (int) must not be coerced through truthiness
        lambda: ma.col("x").str.regexp_match_substring(r"\d+", case_sensitive=1),
    ],
)
def test_flag_options_reject_non_boolean(build):
    """case_sensitive/multiline/dotall are literal boolean options: an expression
    or arbitrary non-bool must be rejected at the API-builder boundary, not
    silently coerced to an enum through truthiness (arguments-vs-options.md)."""
    with pytest.raises(TypeError):
        build()
