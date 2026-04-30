"""Cross-backend tests: col().count() and ma.count_records() via the public API."""
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


# AST-level tests — backend-agnostic, no parametrization needed

def test_col_count_exposed_as_method():
    """ma.col('value').count() should be callable from the public API."""
    expr = ma.col("value").count()
    assert expr is not None


def test_count_records_exposed_as_free_function():
    """ma.count_records() should be callable from the top-level namespace."""
    expr = ma.count_records()
    assert expr is not None


# Cross-backend compilation tests

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestCountViaGroupBy:
    def test_count_via_group_by_agg(self, backend_name, backend_factory):
        """col().count() compiles correctly through the aggregate pipeline."""
        df = backend_factory.create(
            {"group": ["a", "a", "b", "b", "b"], "value": [1, None, 3, 4, None]},
            backend_name,
        )
        result = (
            relation(df)
            .group_by("group")
            .agg(ma.col("value").count().alias("non_null_count"))
            .sort("group")
            .to_dict()
        )
        assert result["non_null_count"] == [1, 2], f"[{backend_name}]"

    def test_count_records_via_group_by_agg(self, backend_name, backend_factory):
        """ma.count_records() compiles correctly through the aggregate pipeline."""
        df = backend_factory.create(
            {"group": ["a", "a", "b", "b", "b"], "value": [1, None, 3, 4, None]},
            backend_name,
        )
        result = (
            relation(df)
            .group_by("group")
            .agg(ma.count_records().alias("row_count"))
            .sort("group")
            .to_dict()
        )
        assert result["row_count"] == [2, 3], f"[{backend_name}]"
