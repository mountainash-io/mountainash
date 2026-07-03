"""union_distinct wiring — cross-backend (spec §3.6)."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.relations.core.relation_api.relation import concat


def _frames(backend):
    a = pl.DataFrame({"x": [1, 2]})
    b = pl.DataFrame({"x": [2, 3]})
    if backend == "polars":
        return a, b
    if backend == "narwhals":
        import narwhals as nw
        return nw.from_native(a, eager_only=True), nw.from_native(b, eager_only=True)
    if backend == "ibis":
        import ibis
        return ibis.memtable(a.to_pandas()), ibis.memtable(b.to_pandas())
    raise AssertionError(backend)


@pytest.mark.parametrize("backend", ["polars", "narwhals", "ibis"])
def test_concat_distinct_deduplicates(backend):
    a, b = _frames(backend)
    rel = concat([ma.relation(a), ma.relation(b)], distinct=True)
    out = rel.to_polars()
    assert sorted(out["x"].to_list()) == [1, 2, 3]


@pytest.mark.parametrize("backend", ["polars", "narwhals", "ibis"])
def test_concat_default_keeps_duplicates(backend):
    a, b = _frames(backend)
    rel = concat([ma.relation(a), ma.relation(b)])
    out = rel.to_polars()
    assert sorted(out["x"].to_list()) == [1, 2, 2, 3]
