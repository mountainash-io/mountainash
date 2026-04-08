"""Cross-backend tests: t_is_in / t_is_not_in accept list-typed column argument.

Tracks mountainash-expressions#75. See spec at
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


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestTIsInListColumn:

    def test_t_is_in_list_column_happy_path(self, backend_name, backend_factory, collect_expr):
        """Scalar column vs list column: per-row membership."""
        if backend_name in ("narwhals-pandas", "narwhals-polars"):
            pytest.xfail(
                "narwhals (as of 2.19.0) does not accept expression arguments "
                "for list.contains on any native backend — signature rejects "
                "non-literal `item`. Tracked via KNOWN_EXPR_LIMITATIONS."
            )
        if backend_name == "pandas":
            pytest.xfail(
                "pandas backend routes through narwhals, which has the same "
                "list.contains(expr) gap as narwhals-polars/narwhals-pandas."
            )
        if backend_name == "ibis-sqlite":
            pytest.xfail("SQLite has no native array/list column type.")
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
