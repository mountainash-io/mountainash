"""Tests for case-insensitive string matching."""

from __future__ import annotations

import pytest

import mountainash as ma

BACKENDS = ["polars", "narwhals-polars", "ibis-duckdb"]


@pytest.mark.parametrize("backend_name", BACKENDS)
class TestCaseInsensitiveContains:
    def test_case_insensitive_contains(self, backend_name, backend_factory, collect_expr):
        """str.contains(case_sensitive=False) matches regardless of case."""
        data = {"text": ["Hello World", "HELLO WORLD", "hello world", "Goodbye", "foo.bar"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.contains("hello", case_sensitive=False)
        result = collect_expr(df, expr)
        assert result == [True, True, True, False, False], f"[{backend_name}] got {result}"

    def test_case_sensitive_contains_default(self, backend_name, backend_factory, collect_expr):
        """str.contains() is case-sensitive by default."""
        data = {"text": ["Hello World", "HELLO WORLD", "hello world", "Goodbye", "foo.bar"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.contains("hello")
        result = collect_expr(df, expr)
        assert result == [False, False, True, False, False], f"[{backend_name}] got {result}"

    def test_case_insensitive_preserves_literal_semantics(self, backend_name, backend_factory, collect_expr):
        """Regex metacharacters treated as literals in case-insensitive mode."""
        data = {"text": ["Hello World", "HELLO WORLD", "hello world", "Goodbye", "foo.bar"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.contains("foo.bar", case_sensitive=False)
        result = collect_expr(df, expr)
        assert result == [False, False, False, False, True], f"[{backend_name}] got {result}"

    def test_case_insensitive_starts_with(self, backend_name, backend_factory, collect_expr):
        """str.starts_with(case_sensitive=False) matches prefix regardless of case."""
        data = {"text": ["Hello World", "HELLO WORLD", "hello world", "Goodbye", "foo.bar"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.starts_with("hello", case_sensitive=False)
        result = collect_expr(df, expr)
        assert result == [True, True, True, False, False], f"[{backend_name}] got {result}"

    def test_case_insensitive_ends_with(self, backend_name, backend_factory, collect_expr):
        """str.ends_with(case_sensitive=False) matches suffix regardless of case."""
        data = {"text": ["Hello World", "HELLO WORLD", "hello world", "Goodbye", "foo.bar"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.ends_with("world", case_sensitive=False)
        result = collect_expr(df, expr)
        assert result == [True, True, True, False, False], f"[{backend_name}] got {result}"
