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


# ---------------------------------------------------------------------------
# Head
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestHead:
    def test_head_default(self, backend_name, backend_factory):
        data = {"a": list(range(10)), "b": list(range(10, 20))}
        df = backend_factory.create(data, backend_name)
        result = ma.relation(df).head().to_dicts()
        assert len(result) == 5
        assert result[0] == {"a": 0, "b": 10}
        assert result[4] == {"a": 4, "b": 14}

    def test_head_custom_n(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [1, 2, 3, 4, 5], "b": [10, 20, 30, 40, 50]}, backend_name
        )
        result = ma.relation(df).head(3).to_dicts()
        assert result == [
            {"a": 1, "b": 10},
            {"a": 2, "b": 20},
            {"a": 3, "b": 30},
        ]


# ---------------------------------------------------------------------------
# Tail
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestTail:
    def test_tail_default(self, backend_name, backend_factory):
        data = {"a": list(range(10)), "b": list(range(10, 20))}
        df = backend_factory.create(data, backend_name)
        result = ma.relation(df).tail().to_dicts()
        assert len(result) == 5
        assert result[0] == {"a": 5, "b": 15}
        assert result[4] == {"a": 9, "b": 19}

    def test_tail_custom_n(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [1, 2, 3, 4, 5], "b": [10, 20, 30, 40, 50]}, backend_name
        )
        result = ma.relation(df).tail(2).to_dicts()
        assert result == [
            {"a": 4, "b": 40},
            {"a": 5, "b": 50},
        ]


# ---------------------------------------------------------------------------
# Slice
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestSlice:
    def test_slice_offset_and_length(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [1, 2, 3, 4, 5], "b": [10, 20, 30, 40, 50]}, backend_name
        )
        result = ma.relation(df).slice(1, 3).to_dicts()
        assert result == [
            {"a": 2, "b": 20},
            {"a": 3, "b": 30},
            {"a": 4, "b": 40},
        ]


# ---------------------------------------------------------------------------
# Unique
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestUnique:
    def test_unique_single_column(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [1, 2, 2, 3, 3, 3]}, backend_name
        )
        result = ma.relation(df).unique("a").to_dicts()
        result_sorted = sorted_dicts(result, "a")
        assert result_sorted == [{"a": 1}, {"a": 2}, {"a": 3}]

    def test_unique_multi_column(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [1, 1, 2, 2], "b": ["x", "x", "x", "y"]}, backend_name
        )
        result = ma.relation(df).unique("a", "b").to_dicts()
        result_sorted = sorted_dicts(result, ["a", "b"])
        assert result_sorted == [
            {"a": 1, "b": "x"},
            {"a": 2, "b": "x"},
            {"a": 2, "b": "y"},
        ]


# ---------------------------------------------------------------------------
# Pipe
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestPipe:
    def test_pipe_transform(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [1, 2, 3, 4, 5], "b": [10, 20, 30, 40, 50]}, backend_name
        )

        def top_two(rel):
            return rel.sort("a", descending=True).head(2)

        result = ma.relation(df).pipe(top_two).to_dicts()
        assert result == [{"a": 5, "b": 50}, {"a": 4, "b": 40}]
