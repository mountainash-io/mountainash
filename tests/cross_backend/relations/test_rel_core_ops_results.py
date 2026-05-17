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


# ---------------------------------------------------------------------------
# Select
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestSelect:
    def test_select_columns_by_name(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [1, 2], "b": [10, 20], "c": ["x", "y"]}, backend_name
        )
        result = ma.relation(df).select("a", "c").to_dicts()
        assert result == [{"a": 1, "c": "x"}, {"a": 2, "c": "y"}]

    def test_select_expression_projection(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [1, 2, 3], "b": [10, 20, 30]}, backend_name
        )
        result = ma.relation(df).select(
            ma.col("a"),
            ma.col("b").mul(2).alias("b_doubled"),
        ).to_dicts()
        assert result == [
            {"a": 1, "b_doubled": 20},
            {"a": 2, "b_doubled": 40},
            {"a": 3, "b_doubled": 60},
        ]

    def test_select_reorder_columns(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [1, 2], "b": [10, 20], "c": ["x", "y"]}, backend_name
        )
        result = ma.relation(df).select("c", "a").to_dicts()
        assert result == [{"c": "x", "a": 1}, {"c": "y", "a": 2}]


# ---------------------------------------------------------------------------
# With Columns
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWithColumns:
    def test_add_computed_column(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [1, 2, 3], "b": [10, 20, 30]}, backend_name
        )
        result = ma.relation(df).with_columns(
            ma.col("a").add(ma.col("b")).alias("sum")
        ).to_dicts()
        assert result == [
            {"a": 1, "b": 10, "sum": 11},
            {"a": 2, "b": 20, "sum": 22},
            {"a": 3, "b": 30, "sum": 33},
        ]

    def test_overwrite_existing_column(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [1, 2, 3], "b": [10, 20, 30]}, backend_name
        )
        result = ma.relation(df).with_columns(
            ma.col("b").mul(2).alias("b")
        ).to_dicts()
        assert result == [
            {"a": 1, "b": 20},
            {"a": 2, "b": 40},
            {"a": 3, "b": 60},
        ]


# ---------------------------------------------------------------------------
# Drop
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestDrop:
    def test_drop_single_column(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [1, 2], "b": [10, 20], "c": ["x", "y"]}, backend_name
        )
        result = ma.relation(df).drop("b").to_dicts()
        assert result == [{"a": 1, "c": "x"}, {"a": 2, "c": "y"}]

    def test_drop_multiple_columns(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [1, 2], "b": [10, 20], "c": ["x", "y"]}, backend_name
        )
        result = ma.relation(df).drop("a", "c").to_dicts()
        assert result == [{"b": 10}, {"b": 20}]


# ---------------------------------------------------------------------------
# Rename
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestRename:
    def test_single_rename(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [1, 2], "b": [10, 20]}, backend_name
        )
        result = ma.relation(df).rename({"a": "alpha"}).to_dicts()
        assert result == [{"alpha": 1, "b": 10}, {"alpha": 2, "b": 20}]

    def test_multiple_renames(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [1, 2], "b": [10, 20]}, backend_name
        )
        result = ma.relation(df).rename({"a": "x", "b": "y"}).to_dicts()
        assert result == [{"x": 1, "y": 10}, {"x": 2, "y": 20}]


# ---------------------------------------------------------------------------
# Sort
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestSort:
    def test_sort_ascending(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [3, 1, 2], "b": [30, 10, 20]}, backend_name
        )
        result = ma.relation(df).sort("a").to_dicts()
        assert result == [
            {"a": 1, "b": 10},
            {"a": 2, "b": 20},
            {"a": 3, "b": 30},
        ]

    def test_sort_descending(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [3, 1, 2], "b": [30, 10, 20]}, backend_name
        )
        result = ma.relation(df).sort("a", descending=True).to_dicts()
        assert result == [
            {"a": 3, "b": 30},
            {"a": 2, "b": 20},
            {"a": 1, "b": 10},
        ]

    def test_sort_multi_column(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"group": ["b", "a", "a", "b"], "val": [2, 1, 2, 1]},
            backend_name,
        )
        result = ma.relation(df).sort("group", "val").to_dicts()
        assert result == [
            {"group": "a", "val": 1},
            {"group": "a", "val": 2},
            {"group": "b", "val": 1},
            {"group": "b", "val": 2},
        ]

    def test_sort_with_nulls(self, backend_name, backend_factory):
        """Test null ordering in sort.

        Polars default is nulls_last=True (nulls at end).
        Narwhals ignores nulls_last — narwhals.sort() has no such parameter.
        Ibis uses SQL default (typically nulls last for ASC, varies by engine).

        This test verifies that each backend returns nulls somewhere consistent
        without asserting a specific null position, since the API does not
        expose nulls_last to the user and backends diverge.
        """
        df = backend_factory.create(
            {"a": [3, None, 1, None, 2], "b": [30, 90, 10, 80, 20]},
            backend_name,
        )
        result = ma.relation(df).sort("a").to_dicts()
        non_null_rows = [r for r in result if r["a"] is not None]
        null_rows = [r for r in result if r["a"] is None]
        assert len(non_null_rows) == 3
        assert len(null_rows) == 2
        assert [r["a"] for r in non_null_rows] == [1, 2, 3]
