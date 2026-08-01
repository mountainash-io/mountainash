"""Cross-backend regression pin for `Relation.with_row_index`.

Tracks mountainash#78 and the upstream gap
https://github.com/ibis-project/ibis/issues/10513 — the Ibis Polars
backend has no translator for `WindowFunction`, so `ibis.row_number()`
(which our `with_row_index` lowers to) cannot compile on `ibis-polars`.

This test pins the declared capability gap: ibis-polars is expected to
raise ``BackendCapabilityError`` until upstream ibis#10513 lands. Remove
the capability fact and this error assertion in the same PR that bumps
the ibis pin.

See principle `d.cross-backend/known-divergences.md` §8.
"""
from __future__ import annotations

import pytest

from mountainash.relations import relation
from mountainash.core.types import BackendCapabilityError
from fixtures.backend_registry import ALL_BACKENDS


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWithRowIndex:

    def test_with_row_index_adds_zero_based_sequence(self, backend_name, backend_factory):
        """`with_row_index` adds a 0..N-1 column on every backend."""
        if backend_name == "narwhals-lazy":
            pytest.xfail(
                "narwhals LazyFrame.with_row_index() requires an explicit "
                "keyword-only `order_by=` argument because row order over a "
                "lazy frame is undefined by design "
                "(TypeError: LazyFrame.with_row_index() missing 1 required "
                "keyword-only argument: 'order_by'). The eager/polars paths "
                "assign indices in physical storage order with no order_by; "
                "there is no column that recovers insertion order on a lazy "
                "frame, so a 0..N-1 sequence matching the input row order is "
                "not reproducible without changing data ordering — a genuine, "
                "unavoidable backend limitation."
            )
        data = {"name": ["a", "b", "c", "d"]}
        df = backend_factory.create(data, backend_name)

        rel = relation(df).with_row_index(name="idx")
        if backend_name == "ibis-polars":
            with pytest.raises(BackendCapabilityError, match="with_row_index"):
                rel.collect()
            return
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
