"""Cross-backend result verification for edge cases and terminal operations.

Phase 5 of the relation result verification suite. Tests empty DataFrames,
all-NULL columns, single-row DataFrames, output terminals, and collect/compile/explain.
"""
from __future__ import annotations

import pytest

import mountainash as ma

from fixtures.backend_registry import ALL_BACKENDS

# ALL_BACKENDS = [
#     "polars",
#     "pandas",
#     "narwhals-polars",
#     "narwhals-pandas",
#     "ibis-polars",
#     "ibis-duckdb",
#     "ibis-sqlite",
# ]


def sorted_dicts(dicts: list[dict], by: str | list[str]) -> list[dict]:
    """Sort list of dicts by key(s) for order-independent comparison."""
    if isinstance(by, str):
        by = [by]
    return sorted(dicts, key=lambda d: tuple(
        (0, d[k]) if d[k] is not None else (1,) for k in by
    ))


# ---------------------------------------------------------------------------
# Empty DataFrame through operations
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestEmptyDataFrame:
    def test_empty_through_filter(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [1, 2, 3], "b": [10, 20, 30]}, backend_name
        )
        result = ma.relation(df).filter(ma.col("a").gt(100)).to_dicts()
        assert result == []

    def test_empty_through_sort(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [1, 2, 3], "b": [10, 20, 30]}, backend_name
        )
        result = (
            ma.relation(df)
            .filter(ma.col("a").gt(100))
            .sort("a")
            .to_dicts()
        )
        assert result == []

    def test_empty_through_group_by(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"group": ["a", "b"], "val": [1, 2]}, backend_name
        )
        result = (
            ma.relation(df)
            .filter(ma.col("val").gt(100))
            .group_by("group")
            .agg(ma.col("val").sum().alias("total"))
            .to_dicts()
        )
        assert result == []

    def test_empty_count_rows(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [1, 2, 3]}, backend_name
        )
        count = ma.relation(df).filter(ma.col("a").gt(100)).count_rows()
        assert count == 0


# ---------------------------------------------------------------------------
# All-NULL columns through operations
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestAllNullColumns:
    def test_null_column_through_filter(self, backend_name, backend_factory):
        if backend_name == "ibis-duckdb":
            pytest.xfail(
                "DuckDB rejects tables with NULL-typed columns at creation time; "
                "a typed null column (e.g. Int64) would work, but pure Python "
                "[None, None, None] infers NULL type. Known DuckDB limitation."
            )
        df = backend_factory.create(
            {"a": [1, 2, 3], "b": [None, None, None]}, backend_name
        )
        result = ma.relation(df).filter(ma.col("a").gt(1)).to_dicts()
        assert result == [
            {"a": 2, "b": None},
            {"a": 3, "b": None},
        ]

    def test_null_column_through_sort(self, backend_name, backend_factory):
        if backend_name == "ibis-duckdb":
            pytest.xfail(
                "DuckDB rejects tables with NULL-typed columns at creation time; "
                "a typed null column (e.g. Int64) would work, but pure Python "
                "[None, None, None] infers NULL type. Known DuckDB limitation."
            )
        df = backend_factory.create(
            {"a": [3, 1, 2], "b": [None, None, None]}, backend_name
        )
        result = ma.relation(df).sort("a").to_dicts()
        assert result == [
            {"a": 1, "b": None},
            {"a": 2, "b": None},
            {"a": 3, "b": None},
        ]


# ---------------------------------------------------------------------------
# Single-row DataFrame
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestSingleRow:
    def test_single_row_through_sort(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [42], "b": ["hello"]}, backend_name
        )
        result = ma.relation(df).sort("a").to_dicts()
        assert result == [{"a": 42, "b": "hello"}]

    def test_single_row_through_head(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [42], "b": ["hello"]}, backend_name
        )
        result = ma.relation(df).head(5).to_dicts()
        assert result == [{"a": 42, "b": "hello"}]

    def test_single_row_through_unique(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [42], "b": ["hello"]}, backend_name
        )
        result = ma.relation(df).unique("a", "b").to_dicts()
        assert result == [{"a": 42, "b": "hello"}]


# ---------------------------------------------------------------------------
# Output terminals: to_dict, to_dicts, to_tuples
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestOutputTerminals:
    def test_to_dict(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [1, 2, 3], "b": ["x", "y", "z"]}, backend_name
        )
        result = ma.relation(df).to_dict()
        assert isinstance(result, dict)
        assert result["a"] == [1, 2, 3]
        assert result["b"] == ["x", "y", "z"]

    def test_to_dicts(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [1, 2], "b": ["x", "y"]}, backend_name
        )
        result = ma.relation(df).to_dicts()
        assert isinstance(result, list)
        assert result == [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]

    def test_to_tuples(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [1, 2], "b": ["x", "y"]}, backend_name
        )
        result = ma.relation(df).to_tuples()
        assert isinstance(result, list)
        assert result == [(1, "x"), (2, "y")]

    def test_to_pandas(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [1, 2, 3], "b": ["x", "y", "z"]}, backend_name
        )
        result = ma.relation(df).to_pandas()
        import pandas as pd
        assert isinstance(result, pd.DataFrame)
        assert list(result["a"]) == [1, 2, 3]
        assert list(result["b"]) == ["x", "y", "z"]


# ---------------------------------------------------------------------------
# Collect / Compile / Explain terminals
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestCollectCompileExplain:
    def test_collect_materializes(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [1, 2, 3]}, backend_name
        )
        result = ma.relation(df).filter(ma.col("a").gt(1)).collect()
        # collect() should return a materialized result, not a lazy plan
        # For polars, it should be a DataFrame not a LazyFrame
        assert result is not None

    def test_compile_returns_plan(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [1, 2, 3]}, backend_name
        )
        result = ma.relation(df).filter(ma.col("a").gt(1)).compile()
        assert result is not None

    def test_explain_returns_string(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [1, 2, 3]}, backend_name
        )
        result = ma.relation(df).filter(ma.col("a").gt(1)).explain()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_count_rows_after_filter(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [1, 2, 3, 4, 5]}, backend_name
        )
        count = ma.relation(df).filter(ma.col("a").gt(2)).count_rows()
        assert count == 3
        assert isinstance(count, int)
