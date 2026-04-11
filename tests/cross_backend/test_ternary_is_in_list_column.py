"""Cross-backend tests: t_is_in / t_is_not_in accept list-typed column argument.

Tracks mountainash#75. See spec at
docs/superpowers/specs/2026-04-08-ternary-is-in-list-column-design.md
"""
from __future__ import annotations

import pytest

import mountainash.expressions as ma


ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals-polars",
    "narwhals-pandas",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]


def _xfail_unsupported_backend(backend_name: str) -> None:
    """xfail backends that can't do list-column membership yet."""
    if backend_name in ("narwhals-pandas", "narwhals-polars", "pandas"):
        pytest.xfail(
            "narwhals (as of 2.19.0) types list.contains(item) as "
            "NonNestedLiteral; expression args rejected across all its "
            "native backends. pandas relation backend routes through narwhals."
        )
    if backend_name == "ibis-sqlite":
        pytest.xfail("SQLite has no native array/list column type.")


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestTIsInListColumn:

    def test_t_is_in_list_column_happy_path(self, backend_name, backend_factory, collect_expr):
        """Scalar column vs list column: per-row membership."""
        _xfail_unsupported_backend(backend_name)
        data = {
            "ctx": ["AU", "US", "CN"],
            "allowed": [["AU", "NZ"], ["US", "CA"], ["JP", "KR"]],
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.t_col("ctx").t_is_in(ma.col("allowed"))
        actual = collect_expr(df, expr)
        assert actual == [1, 1, -1], (
            f"[{backend_name}] Expected [1, 1, -1], got {actual}"
        )

    def test_t_is_in_null_list_row_is_unknown(self, backend_name, backend_factory, collect_expr):
        """Row where the list column is null → ternary UNKNOWN (0)."""
        _xfail_unsupported_backend(backend_name)
        data = {
            "ctx": ["AU", "US"],
            "allowed": [["AU", "NZ"], None],
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.t_col("ctx").t_is_in(ma.col("allowed"))
        actual = collect_expr(df, expr)
        assert actual[0] == 1, f"[{backend_name}] row 0 expected 1, got {actual[0]!r}"
        assert actual[1] == 0, f"[{backend_name}] row 1 expected 0 (UNKNOWN), got {actual[1]!r}"

    def test_t_is_in_sentinel_ctx_is_unknown(self, backend_name, backend_factory, collect_expr):
        """When ctx matches an unknown_values sentinel, result is UNKNOWN."""
        _xfail_unsupported_backend(backend_name)
        data = {
            "ctx": ["AU", "<NA>", "US"],
            "allowed": [["AU"], ["AU"], ["AU"]],
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.t_col("ctx", unknown={"<NA>"}).t_is_in(ma.col("allowed"))
        actual = collect_expr(df, expr)
        assert actual == [1, 0, -1], (
            f"[{backend_name}] Expected [1, 0, -1], got {actual}"
        )

    def test_t_is_not_in_list_column(self, backend_name, backend_factory, collect_expr):
        """Mirror of happy path for t_is_not_in."""
        _xfail_unsupported_backend(backend_name)
        data = {
            "ctx": ["AU", "US", "CN"],
            "allowed": [["AU", "NZ"], ["US", "CA"], ["JP", "KR"]],
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.t_col("ctx").t_is_not_in(ma.col("allowed"))
        actual = collect_expr(df, expr)
        assert actual == [-1, -1, 1], (
            f"[{backend_name}] Expected [-1, -1, 1], got {actual}"
        )

    def test_t_is_in_literal_list_still_works(self, backend_name, backend_factory, collect_expr):
        """Regression guard: literal-list path unchanged by this refactor."""
        data = {"ctx": ["AU", "US", "CN"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.t_col("ctx").t_is_in(["AU", "US"])
        actual = collect_expr(df, expr)
        assert actual == [1, 1, -1], (
            f"[{backend_name}] Expected [1, 1, -1], got {actual}"
        )
