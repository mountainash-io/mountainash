"""Cross-backend tests for empty-relation scalar aggregate behaviour."""
from __future__ import annotations

import pytest

import mountainash as ma
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
class TestEmptyAggregates:
    def _empty_rel(self, backend_name, backend_factory):
        df = backend_factory.create({"x": [1, 2, 3]}, backend_name)
        return relation(df).filter(ma.col("x").gt(ma.lit(999)))

    def test_empty_sum_returns_null_or_zero(self, backend_name, backend_factory):
        result = self._empty_rel(backend_name, backend_factory).sum("x")
        assert result is None or result == 0, f"[{backend_name}]"

    def test_empty_avg_returns_null(self, backend_name, backend_factory):
        result = self._empty_rel(backend_name, backend_factory).avg("x")
        assert result is None, f"[{backend_name}]"

    def test_empty_min_returns_null(self, backend_name, backend_factory):
        result = self._empty_rel(backend_name, backend_factory).min("x")
        assert result is None, f"[{backend_name}]"

    def test_empty_max_returns_null(self, backend_name, backend_factory):
        result = self._empty_rel(backend_name, backend_factory).max("x")
        assert result is None, f"[{backend_name}]"
