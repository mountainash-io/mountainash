"""Cross-backend tests for Relation method aliases."""

from __future__ import annotations

import pytest

from duckdb.duckdb import BinderException
from ibis.common.exceptions import OperationNotDefinedError
from sqlite3 import OperationalError

import mountainash as ma
from fixtures.call_expectations import expect_call_failure



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
class TestRelationAliases:
    def _make_relation(self, backend_name, backend_factory):
        df = backend_factory.create({"a": [1, 2, 3], "b": [4, 5, 6]}, backend_name)
        return ma.relation(df)

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_limit_is_head(self, backend_name, backend_factory):
        r = self._make_relation(backend_name, backend_factory)
        assert r.limit(2).to_dicts() == r.head(2).to_dicts(), f"[{backend_name}]"

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_melt_is_unpivot(self, backend_name, backend_factory):
        r = self._make_relation(backend_name, backend_factory)
        with expect_call_failure(
            when=backend_name == "ibis-sqlite",
            errors=(OperationNotDefinedError,),
            reason="Relation.drop_nans()/unpivot()/melt() raise on ibis-sqlite; other backends compute them",
        ):
            melt_result = sorted(r.melt(on="b", index="a").to_dicts(), key=lambda d: d["a"])
            unpivot_result = sorted(r.unpivot(on="b", index="a").to_dicts(), key=lambda d: d["a"])
            assert melt_result == unpivot_result, f"[{backend_name}]"

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_bottom_k(self, backend_name, backend_factory):
        r = self._make_relation(backend_name, backend_factory)
        bottom = sorted(r.bottom_k(2, by="a").to_dicts(), key=lambda d: d["a"])
        top_asc = sorted(r.top_k(2, by="a", descending=False).to_dicts(), key=lambda d: d["a"])
        assert bottom == top_asc, f"[{backend_name}]"

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_cross_join(self, backend_name, backend_factory):
        r1 = self._make_relation(backend_name, backend_factory)
        r2 = ma.relation(backend_factory.create({"c": [10, 20]}, backend_name))
        with expect_call_failure(
            when=backend_name in ("ibis-duckdb", "ibis-sqlite"),
            errors=(BinderException,) if backend_name == "ibis-duckdb" else (OperationalError,),
            reason="Relation.cross_join() raises on ibis-duckdb/ibis-sqlite; polars/narwhals and ibis-polars compute it",
        ):
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
