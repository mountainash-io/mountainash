"""Cross-backend tests for Relation.<agg>(col) scalar terminal methods."""
from __future__ import annotations

import pytest

import mountainash as ma
from mountainash.relations import relation

from fixtures.backend_registry import ALL_BACKENDS
from fixtures.capability_gating import xfail_divergence

_ALL = ALL_BACKENDS
_PROD_BACKENDS = [pytest.param(b, marks=xfail_divergence("IB-AGG-05", backend=b)) for b in ALL_BACKENDS]
_NWAGG_BACKENDS = [pytest.param(b, marks=xfail_divergence("NW-AGG-03", backend=b)) for b in ALL_BACKENDS]

# ALL_BACKENDS = [
#     "polars",
#     "pandas",
#     "narwhals-polars",
#     "narwhals-pandas",
#     "ibis-polars",
#     "ibis-duckdb",
#     "ibis-sqlite",
# ]


@pytest.mark.cross_backend
class TestScalarAggregates:
    @pytest.mark.parametrize("backend_name", _ALL)
    def test_sum(self, backend_name, backend_factory):
        df = backend_factory.create({"x": [1, 2, 3, 4, 6]}, backend_name)
        assert relation(df).sum("x") == 16, f"[{backend_name}]"

    @pytest.mark.parametrize("backend_name", _ALL)
    def test_avg(self, backend_name, backend_factory):
        df = backend_factory.create({"x": [1, 2, 3, 4, 6]}, backend_name)
        assert relation(df).avg("x") == pytest.approx(3.2), f"[{backend_name}]"

    @pytest.mark.parametrize("backend_name", _ALL)
    def test_mean_alias(self, backend_name, backend_factory):
        df = backend_factory.create({"x": [1, 2, 3, 4, 6]}, backend_name)
        assert relation(df).mean("x") == relation(df).avg("x"), f"[{backend_name}]"

    @pytest.mark.parametrize("backend_name", _ALL)
    def test_min(self, backend_name, backend_factory):
        df = backend_factory.create({"x": [1, 2, 3, 4, 6]}, backend_name)
        assert relation(df).min("x") == 1, f"[{backend_name}]"

    @pytest.mark.parametrize("backend_name", _ALL)
    def test_max(self, backend_name, backend_factory):
        df = backend_factory.create({"x": [1, 2, 3, 4, 6]}, backend_name)
        assert relation(df).max("x") == 6, f"[{backend_name}]"

    @pytest.mark.parametrize("backend_name", _PROD_BACKENDS)
    def test_product(self, backend_name, backend_factory):
        df = backend_factory.create({"x": [1, 2, 3, 4, 6]}, backend_name)
        # narwhals/pandas backends compute product via exp(sum(log(x))) — floating-point
        assert relation(df).product("x") == pytest.approx(144), f"[{backend_name}]"

    @pytest.mark.parametrize("backend_name", _ALL)
    def test_std_dev(self, backend_name, backend_factory):
        df = backend_factory.create({"x": [1.0, 2.0, 3.0]}, backend_name)
        assert relation(df).std_dev("x") == pytest.approx(1.0), f"[{backend_name}]"

    @pytest.mark.parametrize("backend_name", _ALL)
    def test_variance(self, backend_name, backend_factory):
        df = backend_factory.create({"x": [1.0, 2.0, 3.0]}, backend_name)
        assert relation(df).variance("x") == pytest.approx(1.0), f"[{backend_name}]"

    @pytest.mark.parametrize("backend_name", _NWAGG_BACKENDS)
    def test_any_value(self, backend_name, backend_factory):
        df = backend_factory.create({"x": [1, 2, 3, 4, 6]}, backend_name)
        val = relation(df).any_value("x")
        assert val in {1, 2, 3, 4, 6}, f"[{backend_name}]"

    @pytest.mark.parametrize("backend_name", _ALL)
    def test_sum_after_filter(self, backend_name, backend_factory):
        df = backend_factory.create({"x": [1, 2, 3, 4, 6]}, backend_name)
        rel = relation(df).filter(ma.col("x").gt(ma.lit(2)))
        assert rel.sum("x") == 13, f"[{backend_name}]"
