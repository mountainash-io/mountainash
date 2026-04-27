"""Tests for case-insensitive string matching."""

from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma


@pytest.fixture
def string_df():
    return pl.DataFrame({
        "text": ["Hello World", "HELLO WORLD", "hello world", "Goodbye", "foo.bar"],
    })


class TestCaseInsensitiveContains:
    def test_case_insensitive_contains(self, string_df):
        """str.contains(case_sensitive=False) matches regardless of case."""
        expr = ma.col("text").str.contains("hello", case_sensitive=False)
        result = string_df.with_columns(expr.compile(string_df).alias("match"))
        matches = result["match"].to_list()
        assert matches == [True, True, True, False, False]

    def test_case_sensitive_contains_default(self, string_df):
        """str.contains() is case-sensitive by default."""
        expr = ma.col("text").str.contains("hello")
        result = string_df.with_columns(expr.compile(string_df).alias("match"))
        matches = result["match"].to_list()
        assert matches == [False, False, True, False, False]

    def test_case_insensitive_preserves_literal_semantics(self, string_df):
        """Regex metacharacters treated as literals in case-insensitive mode."""
        expr = ma.col("text").str.contains("foo.bar", case_sensitive=False)
        result = string_df.with_columns(expr.compile(string_df).alias("match"))
        matches = result["match"].to_list()
        assert matches == [False, False, False, False, True]

    def test_case_insensitive_starts_with(self, string_df):
        """str.starts_with(case_sensitive=False) matches prefix regardless of case."""
        expr = ma.col("text").str.starts_with("hello", case_sensitive=False)
        result = string_df.with_columns(expr.compile(string_df).alias("match"))
        matches = result["match"].to_list()
        assert matches == [True, True, True, False, False]

    def test_case_insensitive_ends_with(self, string_df):
        """str.ends_with(case_sensitive=False) matches suffix regardless of case."""
        expr = ma.col("text").str.ends_with("world", case_sensitive=False)
        result = string_df.with_columns(expr.compile(string_df).alias("match"))
        matches = result["match"].to_list()
        assert matches == [True, True, True, False, False]
