"""Cross-backend tests for Relation.count_rows() terminal."""
from __future__ import annotations

import polars as pl
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
class TestCountRows:
    def test_count_rows_basic(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"id": [1, 2, 3, 4, 5], "amount": [10, 20, 30, 40, 50], "status": ["a", "b", "a", "b", "a"]},
            backend_name,
        )
        assert relation(df).count_rows() == 5, f"[{backend_name}]"

    def test_count_rows_after_head(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"id": [1, 2, 3, 4, 5], "amount": [10, 20, 30, 40, 50], "status": ["a", "b", "a", "b", "a"]},
            backend_name,
        )
        assert relation(df).head(2).count_rows() == 2, f"[{backend_name}]"

    def test_count_rows_after_filter_match(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"id": [1, 2, 3, 4, 5], "amount": [10, 20, 30, 40, 50], "status": ["a", "b", "a", "b", "a"]},
            backend_name,
        )
        rel = relation(df).filter(ma.col("status").eq(ma.lit("a")))
        assert rel.count_rows() == 3, f"[{backend_name}]"

    def test_count_rows_after_filter_empty(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"id": [1, 2, 3, 4, 5], "amount": [10, 20, 30, 40, 50], "status": ["a", "b", "a", "b", "a"]},
            backend_name,
        )
        rel = relation(df).filter(ma.col("status").eq(ma.lit("zzz")))
        assert rel.count_rows() == 0, f"[{backend_name}]"

    def test_count_rows_returns_int(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"id": [1, 2, 3, 4, 5], "amount": [10, 20, 30, 40, 50], "status": ["a", "b", "a", "b", "a"]},
            backend_name,
        )
        result = relation(df).count_rows()
        assert isinstance(result, int), f"[{backend_name}]"
        assert not isinstance(result, bool), f"[{backend_name}]"


# Polars-specific: LazyFrame is a Polars concept
def test_count_rows_polars_lazyframe():
    lf = pl.DataFrame({"x": list(range(100))}).lazy()
    assert relation(lf).count_rows() == 100
