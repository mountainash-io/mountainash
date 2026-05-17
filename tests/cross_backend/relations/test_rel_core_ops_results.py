"""Cross-backend result verification for core relational operations.

Phase 1 of the relation result verification suite. Tests filter, remove,
select, with_columns, drop, rename, sort, head, tail, slice, unique, pipe
across all 7 backends.
"""
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


def sorted_dicts(dicts: list[dict], by: str | list[str]) -> list[dict]:
    """Sort list of dicts by key(s) for order-independent comparison."""
    if isinstance(by, str):
        by = [by]
    return sorted(dicts, key=lambda d: tuple(d[k] for k in by))


# ---------------------------------------------------------------------------
# Filter
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestFilter:
    def test_single_predicate(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [1, 2, 3, 4], "b": [10, 20, 30, 40]}, backend_name
        )
        result = ma.relation(df).filter(ma.col("a").gt(2)).to_dicts()
        assert result == [{"a": 3, "b": 30}, {"a": 4, "b": 40}]

    def test_compound_predicate_and(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [1, 2, 3, 4], "b": [10, 20, 30, 40]}, backend_name
        )
        result = ma.relation(df).filter(
            ma.col("a").gt(1), ma.col("b").lt(40)
        ).to_dicts()
        assert result == [{"a": 2, "b": 20}, {"a": 3, "b": 30}]

    def test_filter_to_empty(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [1, 2, 3], "b": [10, 20, 30]}, backend_name
        )
        result = ma.relation(df).filter(ma.col("a").gt(100)).to_dicts()
        assert result == []


# ---------------------------------------------------------------------------
# Remove (inverse of filter)
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestRemove:
    def test_remove_matching_rows(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [1, 2, 3, 4], "b": [10, 20, 30, 40]}, backend_name
        )
        result = ma.relation(df).remove(ma.col("a").gt(2)).to_dicts()
        assert result == [{"a": 1, "b": 10}, {"a": 2, "b": 20}]
