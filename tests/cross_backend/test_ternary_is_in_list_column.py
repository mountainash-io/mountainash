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
        if backend_name == "narwhals-pandas":
            pytest.xfail(
                "narwhals-pandas list ops lag narwhals-polars; "
                "KNOWN_EXPR_LIMITATIONS registers an enriched error"
            )
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
