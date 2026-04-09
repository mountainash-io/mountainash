"""Cross-backend regression pin for `Relation.with_row_index`.

Tracks mountainash-expressions#78 and the upstream gap
https://github.com/ibis-project/ibis/issues/10513 — the Ibis Polars
backend has no translator for `WindowFunction`, so `ibis.row_number()`
(which our `with_row_index` lowers to) cannot compile on `ibis-polars`.

This test pins the divergence: when upstream ibis#10513 lands, the
`ibis-polars` xfail here flips to xpass and this marker should be
removed in the same PR that bumps the ibis pin.

See principle `e.cross-backend/known-divergences.md` §8.
"""
from __future__ import annotations

import pytest

from mountainash.relations import relation


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
class TestWithRowIndex:

    def test_with_row_index_adds_zero_based_sequence(self, backend_name, backend_factory):
        """`with_row_index` adds a 0..N-1 column on every backend."""
        if backend_name == "ibis-polars":
            pytest.xfail(
                "ibis-polars has no WindowFunction translator — tracked "
                "upstream at ibis-project/ibis#10513. See "
                "e.cross-backend/known-divergences.md §8."
            )
        data = {"name": ["a", "b", "c", "d"]}
        df = backend_factory.create(data, backend_name)

        rel = relation(df).with_row_index(name="idx")
        result = rel.collect()

        # Result type varies by backend; extract the idx column to a plain list.
        # polars / narwhals return DataFrame-like objects with [] access;
        # ibis returns a Table whose .execute() gives a pandas DataFrame.
        if hasattr(result, "execute"):
            idx_values = result.execute()["idx"].tolist()
        else:
            idx_values = list(result["idx"])

        assert idx_values == [0, 1, 2, 3], (
            f"[{backend_name}] Expected [0, 1, 2, 3], got {idx_values}"
        )
