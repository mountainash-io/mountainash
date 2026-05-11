"""Cross-backend tests for forward_fill and backward_fill window operations."""
from __future__ import annotations

import pytest

import mountainash as ma

FILL_BACKENDS = [
    "polars",
    "narwhals-polars",
]

IBIS_BACKENDS = [
    pytest.param(
        backend,
        marks=pytest.mark.xfail(
            strict=True,
            reason="Ibis has no expression-level forward_fill/backward_fill — raises BackendCapabilityError",
        ),
    )
    for backend in ("ibis-duckdb", "ibis-polars", "ibis-sqlite")
]


@pytest.mark.parametrize("backend_name", FILL_BACKENDS + IBIS_BACKENDS)
class TestForwardFill:
    def test_forward_fill_basic(self, backend_name, backend_factory, collect_expr):
        """forward_fill propagates last valid value forward over nulls."""
        data = {"val": [1, None, None, 4, None]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").forward_fill()
        result = collect_expr(df, expr)
        assert result == [1, 1, 1, 4, 4]

    def test_forward_fill_with_limit(self, backend_name, backend_factory, collect_expr):
        """forward_fill(limit=1) fills at most one consecutive null."""
        data = {"val": [1, None, None, 4, None]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").forward_fill(limit=1)
        result = collect_expr(df, expr)
        assert result == [1, 1, None, 4, 4]

    def test_forward_fill_no_nulls(self, backend_name, backend_factory, collect_expr):
        """forward_fill on a column with no nulls is a no-op."""
        data = {"val": [1, 2, 3, 4, 5]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").forward_fill()
        result = collect_expr(df, expr)
        assert result == [1, 2, 3, 4, 5]

    def test_forward_fill_leading_null(self, backend_name, backend_factory, collect_expr):
        """Leading nulls before any valid value remain null."""
        data = {"val": [None, None, 3, None, 5]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").forward_fill()
        result = collect_expr(df, expr)
        assert result == [None, None, 3, 3, 5]


@pytest.mark.parametrize("backend_name", FILL_BACKENDS + IBIS_BACKENDS)
class TestBackwardFill:
    def test_backward_fill_basic(self, backend_name, backend_factory, collect_expr):
        """backward_fill propagates next valid value backward over nulls."""
        data = {"val": [None, 2, None, None, 5]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").backward_fill()
        result = collect_expr(df, expr)
        assert result == [2, 2, 5, 5, 5]

    def test_backward_fill_trailing_null(self, backend_name, backend_factory, collect_expr):
        """Trailing nulls after the last valid value remain null."""
        data = {"val": [1, None, 3, None, None]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").backward_fill()
        result = collect_expr(df, expr)
        assert result == [1, 3, 3, None, None]

    def test_backward_fill_with_limit(self, backend_name, backend_factory, collect_expr):
        """backward_fill(limit=1) fills at most one consecutive null."""
        data = {"val": [None, None, 3, None, 5]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").backward_fill(limit=1)
        result = collect_expr(df, expr)
        assert result == [None, 3, 3, 5, 5]

    def test_backward_fill_no_nulls(self, backend_name, backend_factory, collect_expr):
        """backward_fill on a column with no nulls is a no-op."""
        data = {"val": [1, 2, 3, 4, 5]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").backward_fill()
        result = collect_expr(df, expr)
        assert result == [1, 2, 3, 4, 5]
