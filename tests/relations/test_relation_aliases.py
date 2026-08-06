"""Cross-backend tests for Relation method aliases."""
from __future__ import annotations

import pytest

import mountainash as ma


ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals-polars",
    "narwhals-pandas",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]


from fixtures.capability_gating import xfail_divergence

_MELT = [
    pytest.param(b, marks=xfail_divergence("IB-REL-07", backend=b)) for b in ALL_BACKENDS
]
_CROSSJOIN = [
    pytest.param(b, marks=xfail_divergence("IB-REL-09", backend=b)) for b in ALL_BACKENDS
]

@pytest.mark.cross_backend
class TestRelationAliases:
    def _make_relation(self, backend_name, backend_factory):
        df = backend_factory.create({"a": [1, 2, 3], "b": [4, 5, 6]}, backend_name)
        return ma.relation(df)

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_limit_is_head(self, backend_name, backend_factory):
        r = self._make_relation(backend_name, backend_factory)
        assert r.limit(2).to_dicts() == r.head(2).to_dicts(), f"[{backend_name}]"

    @pytest.mark.parametrize("backend_name", _MELT)
    def test_melt_is_unpivot(self, backend_name, backend_factory):
        r = self._make_relation(backend_name, backend_factory)
        melt_result = sorted(r.melt(on="b", index="a").to_dicts(), key=lambda d: d["a"])
        unpivot_result = sorted(r.unpivot(on="b", index="a").to_dicts(), key=lambda d: d["a"])
        assert melt_result == unpivot_result, f"[{backend_name}]"

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_bottom_k(self, backend_name, backend_factory):
        r = self._make_relation(backend_name, backend_factory)
        bottom = sorted(r.bottom_k(2, by="a").to_dicts(), key=lambda d: d["a"])
        top_asc = sorted(r.top_k(2, by="a", descending=False).to_dicts(), key=lambda d: d["a"])
        assert bottom == top_asc, f"[{backend_name}]"

    @pytest.mark.parametrize("backend_name", _CROSSJOIN)
    def test_cross_join(self, backend_name, backend_factory):
        r1 = self._make_relation(backend_name, backend_factory)
        r2 = ma.relation(backend_factory.create({"c": [10, 20]}, backend_name))
        cross = sorted(r1.cross_join(r2).to_dicts(), key=lambda d: (d["a"], d["c"]))
        join_cross = sorted(r1.join(r2, how="cross").to_dicts(), key=lambda d: (d["a"], d["c"]))
        assert cross == join_cross, f"[{backend_name}]"

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_first_is_head_1(self, backend_name, backend_factory):
        r = self._make_relation(backend_name, backend_factory)
        assert r.first().to_dicts() == r.head(1).to_dicts(), f"[{backend_name}]"

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_last_is_tail_1(self, backend_name, backend_factory):
        r = self._make_relation(backend_name, backend_factory)
        assert r.last().to_dicts() == r.tail(1).to_dicts(), f"[{backend_name}]"

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_remove(self, backend_name, backend_factory):
        r = self._make_relation(backend_name, backend_factory)
        remove_result = sorted(r.remove(ma.col("a").gt(2)).to_dicts(), key=lambda d: d["a"])
        filter_result = sorted(r.filter(ma.col("a").le(2)).to_dicts(), key=lambda d: d["a"])
        assert remove_result == filter_result, f"[{backend_name}]"
