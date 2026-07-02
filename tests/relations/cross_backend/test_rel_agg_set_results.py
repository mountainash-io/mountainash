"""Cross-backend result verification for aggregation and set operations.

Phase 3 of the relation result verification suite. Tests group_by+agg
and concat across all 7 backends.
"""
from __future__ import annotations

import pytest

import mountainash as ma
from mountainash.relations.schema_inference import infer_schema

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
    return sorted(dicts, key=lambda d: tuple(d[k] for k in by))


# ---------------------------------------------------------------------------
# Group By + Single Aggregate
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestGroupBySingleAgg:
    def test_group_by_sum(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"group": ["a", "a", "b", "b"], "val": [1, 2, 3, 4]},
            backend_name,
        )
        result = ma.relation(df).group_by("group").agg(
            ma.col("val").sum().alias("total")
        ).to_dicts()
        result_sorted = sorted_dicts(result, "group")
        assert result_sorted == [
            {"group": "a", "total": 3},
            {"group": "b", "total": 7},
        ]

    def test_group_by_mean(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"group": ["a", "a", "b", "b"], "val": [2, 4, 6, 8]},
            backend_name,
        )
        result = ma.relation(df).group_by("group").agg(
            ma.col("val").mean().alias("avg")
        ).to_dicts()
        result_sorted = sorted_dicts(result, "group")
        assert result_sorted == [
            {"group": "a", "avg": 3.0},
            {"group": "b", "avg": 7.0},
        ]

    def test_group_by_count(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"group": ["a", "a", "a", "b", "b"], "val": [1, 2, 3, 4, 5]},
            backend_name,
        )
        result = ma.relation(df).group_by("group").agg(
            ma.col("val").count().alias("cnt")
        ).to_dicts()
        result_sorted = sorted_dicts(result, "group")
        assert result_sorted == [
            {"group": "a", "cnt": 3},
            {"group": "b", "cnt": 2},
        ]


# ---------------------------------------------------------------------------
# Group By + Multiple Aggregates
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestGroupByMultipleAggs:
    def test_multiple_measures(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"group": ["a", "a", "b", "b"], "val": [1, 3, 5, 7]},
            backend_name,
        )
        result = ma.relation(df).group_by("group").agg(
            ma.col("val").sum().alias("total"),
            ma.col("val").min().alias("minimum"),
            ma.col("val").max().alias("maximum"),
        ).to_dicts()
        result_sorted = sorted_dicts(result, "group")
        assert result_sorted == [
            {"group": "a", "total": 4, "minimum": 1, "maximum": 3},
            {"group": "b", "total": 12, "minimum": 5, "maximum": 7},
        ]


# ---------------------------------------------------------------------------
# Group By + Multiple Keys
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestGroupByMultipleKeys:
    def test_composite_grouping(self, backend_name, backend_factory):
        df = backend_factory.create(
            {
                "region": ["east", "east", "west", "west"],
                "category": ["a", "b", "a", "b"],
                "val": [10, 20, 30, 40],
            },
            backend_name,
        )
        result = ma.relation(df).group_by("region", "category").agg(
            ma.col("val").sum().alias("total")
        ).to_dicts()
        result_sorted = sorted_dicts(result, ["region", "category"])
        assert result_sorted == [
            {"region": "east", "category": "a", "total": 10},
            {"region": "east", "category": "b", "total": 20},
            {"region": "west", "category": "a", "total": 30},
            {"region": "west", "category": "b", "total": 40},
        ]


# ---------------------------------------------------------------------------
# Group By on Empty Groups
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestGroupByEmpty:
    def test_group_by_after_filter_to_empty(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"group": ["a", "a", "b", "b"], "val": [1, 2, 3, 4]},
            backend_name,
        )
        result = (
            ma.relation(df)
            .filter(ma.col("val").gt(100))
            .group_by("group")
            .agg(ma.col("val").sum().alias("total"))
            .to_dicts()
        )
        assert result == []


# ---------------------------------------------------------------------------
# Concat (UNION ALL)
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestConcat:
    def test_concat_two_relations(self, backend_name, backend_factory):
        df1, df2 = backend_factory.create_pair(
            {"a": [1, 2], "b": ["x", "y"]},
            {"a": [3, 4], "b": ["z", "w"]},
            backend_name,
        )
        result = ma.concat([
            ma.relation(df1),
            ma.relation(df2),
        ]).to_dicts()
        assert result == [
            {"a": 1, "b": "x"},
            {"a": 2, "b": "y"},
            {"a": 3, "b": "z"},
            {"a": 4, "b": "w"},
        ]

    def test_concat_preserves_duplicates(self, backend_name, backend_factory):
        df1, df2 = backend_factory.create_pair(
            {"a": [1, 2]},
            {"a": [1, 2]},
            backend_name,
        )
        result = ma.concat([
            ma.relation(df1),
            ma.relation(df2),
        ]).to_dicts()
        assert result == [{"a": 1}, {"a": 2}, {"a": 1}, {"a": 2}]


# ---------------------------------------------------------------------------
# Un-aliased Measure Naming Parity (item 46 a)
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestUnaliasedMeasureNameParity:
    """Runtime parity oracle: infer_schema()'s column-name set for an
    un-aliased aggregate measure must match the actual to_polars() column
    set. Polars, pandas, and both narwhals variants name the measure after
    its leftmost source column ("v"); Ibis instead names it "Sum(v)" on
    every engine (duckdb/polars/sqlite) — a documented divergence, not
    chased in inference (see known-divergences.md #18). The Ibis cases run
    the full assertion under a strict xfail marker so an upstream naming
    convergence surfaces as a hard XPASS failure."""

    def test_unaliased_measure_name_parity_with_runtime(
        self, backend_name, backend_factory, request
    ):
        if backend_name in ("ibis-duckdb", "ibis-polars", "ibis-sqlite"):
            request.applymarker(pytest.mark.xfail(
                strict=True,
                reason=(
                    "Ibis names un-aliased measures from expr repr (e.g. "
                    "'Sum(v)'), not the source column — see "
                    "known-divergences.md #18"
                ),
            ))
        df = backend_factory.create(
            {"k": ["a", "a", "b"], "v": [1, 2, 3]}, backend_name
        )
        rel = ma.relation(df).group_by("k").agg(ma.col("v").sum())
        inferred = infer_schema(rel._node, None)
        assert set(inferred.keys()) == set(rel.to_polars().columns)
