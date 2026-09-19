"""Cross-backend tests for Relation.<agg>(col) scalar terminal methods."""

from __future__ import annotations

import pytest

import mountainash as ma
from mountainash.relations import relation

from narwhals.exceptions import InvalidOperationError

from fixtures.backend_registry import ALL_BACKENDS
from fixtures.call_expectations import expect_call_failure



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
    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_sum(self, backend_name, backend_factory):
        df = backend_factory.create({"x": [1, 2, 3, 4, 6]}, backend_name)
        assert relation(df).sum("x") == 16, f"[{backend_name}]"

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_avg(self, backend_name, backend_factory):
        df = backend_factory.create({"x": [1, 2, 3, 4, 6]}, backend_name)
        assert relation(df).avg("x") == pytest.approx(3.2), f"[{backend_name}]"

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_mean_alias(self, backend_name, backend_factory):
        df = backend_factory.create({"x": [1, 2, 3, 4, 6]}, backend_name)
        assert relation(df).mean("x") == relation(df).avg("x"), f"[{backend_name}]"

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_min(self, backend_name, backend_factory):
        df = backend_factory.create({"x": [1, 2, 3, 4, 6]}, backend_name)
        assert relation(df).min("x") == 1, f"[{backend_name}]"

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_max(self, backend_name, backend_factory):
        df = backend_factory.create({"x": [1, 2, 3, 4, 6]}, backend_name)
        assert relation(df).max("x") == 6, f"[{backend_name}]"

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_product(self, backend_name, backend_factory):
        df = backend_factory.create({"x": [1, 2, 3, 4, 6]}, backend_name)
        # narwhals/pandas backends compute product via exp(sum(log(x))) — floating-point
        with expect_call_failure(
            when=backend_name == "ibis-polars",
            errors=(AssertionError,),
            reason="product() returns None on ibis-polars",
        ):
            assert relation(df).product("x") == pytest.approx(144), f"[{backend_name}]"

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_std_dev(self, backend_name, backend_factory):
        df = backend_factory.create({"x": [1.0, 2.0, 3.0]}, backend_name)
        assert relation(df).std_dev("x") == pytest.approx(1.0), f"[{backend_name}]"

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_variance(self, backend_name, backend_factory):
        df = backend_factory.create({"x": [1.0, 2.0, 3.0]}, backend_name)
        assert relation(df).variance("x") == pytest.approx(1.0), f"[{backend_name}]"

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_any_value(self, backend_name, backend_factory):
        df = backend_factory.create({"x": [1, 2, 3, 4, 6]}, backend_name)
        with expect_call_failure(
            when=backend_name == "narwhals-lazy",
            errors=(InvalidOperationError,),
            reason="mode() and any_value() raise on narwhals-lazy",
        ):
            val = relation(df).any_value("x")
            assert val in {1, 2, 3, 4, 6}, f"[{backend_name}]"

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_sum_after_filter(self, backend_name, backend_factory):
        df = backend_factory.create({"x": [1, 2, 3, 4, 6]}, backend_name)
        rel = relation(df).filter(ma.col("x").gt(ma.lit(2)))
        assert rel.sum("x") == 13, f"[{backend_name}]"
