"""Cross-backend result verification for aggregation and set operations.

Phase 3 of the relation result verification suite. Tests group_by+agg
and concat across all 7 backends.
"""

from __future__ import annotations

import pytest

import mountainash as ma
from mountainash.relations.core.projection_names import ProjectionNameError
from mountainash.relations.core.relation_api.relation import Relation
from mountainash.relations.core.relation_nodes import AggregateRelNode

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
        result = ma.relation(df).group_by("group").agg(ma.col("val").sum().alias("total")).to_dicts()
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
        result = ma.relation(df).group_by("group").agg(ma.col("val").mean().alias("avg")).to_dicts()
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
        result = ma.relation(df).group_by("group").agg(ma.col("val").count().alias("cnt")).to_dicts()
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
        result = (
            ma.relation(df)
            .group_by("group")
            .agg(
                ma.col("val").sum().alias("total"),
                ma.col("val").min().alias("minimum"),
                ma.col("val").max().alias("maximum"),
            )
            .to_dicts()
        )
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
        result = ma.relation(df).group_by("region", "category").agg(ma.col("val").sum().alias("total")).to_dicts()
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
        result = ma.concat(
            [
                ma.relation(df1),
                ma.relation(df2),
            ]
        ).to_dicts()
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
        result = ma.concat(
            [
                ma.relation(df1),
                ma.relation(df2),
            ]
        ).to_dicts()
        assert result == [{"a": 1}, {"a": 2}, {"a": 1}, {"a": 2}]


NAMING_CASES = [
    ("sum", lambda: ma.col("x").sum(), "x", [6, 8], 14),
    ("any_value", lambda: ma.col("x").any_value(), "x", [3, 8], None),
    ("nested", lambda: ma.col("x").alias("renamed").sum(), "renamed", [6, 8], 14),
    ("suffix", lambda: ma.col("x").sum().name.suffix("_sum"), "x_sum", [6, 8], 14),
    ("outer", lambda: ma.col("x").sum().alias("total"), "total", [6, 8], 14),
    ("literal_first", lambda: (ma.lit(1) + ma.col("x")).sum(), "literal", [8, 9], 17),
]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("grouped", [True, False])
@pytest.mark.parametrize("direct", [True, False])
@pytest.mark.parametrize("case,make,name,group_values,global_value", NAMING_CASES)
def test_aggregate_output_names(
    backend_name, backend_factory, grouped, direct, case, make, name, group_values, global_value,
):
    """Names must survive native compilation and downstream selection."""
    from narwhals.exceptions import InvalidOperationError

    source = backend_factory.create({"g": [0, 0, 1], "x": [3, 3, 8]}, backend_name)
    base = ma.relation(source)
    keys = ["g"] if grouped else []
    expression = make()
    q = (
        Relation(AggregateRelNode(input=base._node, keys=keys, measures=[expression]))
        if direct else base.group_by(*keys).agg(expression)
    )
    names = keys + [name]
    assert q.columns == names
    with expect_call_failure(
        when=backend_name == "narwhals-lazy" and case == "any_value",
        reason="NW-AGG-03: any_value() raises on narwhals-lazy",
        errors=(InvalidOperationError,),
    ):
        rows = q.select(*names).to_dicts()
        if grouped:
            assert sorted_dicts(rows, "g") == [
                {"g": g, name: value} for g, value in enumerate(group_values)
            ]
        elif case == "any_value":
            assert rows in [[{"x": 3}], [{"x": 8}]]
        else:
            assert rows == [{name: global_value}]
        assert q.to_polars().columns == names


@pytest.mark.parametrize("direct", [True, False])
@pytest.mark.parametrize(
    "keys,measures,name",
    [
        (["x"], [ma.col("x").sum()], "x"),
        ([], [ma.col("x").sum(), ma.col("x").max()], "x"),
        ([], [ma.col("x").sum(), ma.col("g").max().alias("x")], "x"),
        (["g", "g"], [ma.col("x").sum()], "g"),
        ([], [ma.col("x").sum().alias(""), ma.col("g").sum().alias("")], ""),
    ],
)
def test_aggregate_duplicate_names(keys, measures, name, direct):
    """Statically known collisions fail even before missing fields are compiled."""
    base = ma.relation([{"unrelated": 1}])
    with pytest.raises(ProjectionNameError) as caught:
        if direct:
            Relation(AggregateRelNode(input=base._node, keys=keys, measures=measures)).collect()
        else:
            base.group_by(*keys).agg(*measures)
    assert repr(name) in str(caught.value)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_aggregate_expression_reuse(backend_name, backend_factory):
    base = ma.relation(backend_factory.create({"x": [2, 4]}, backend_name))
    measure = ma.col("x").sum()
    original = base.group_by().agg(measure)
    renamed = base.group_by().agg(measure.alias("total"))
    assert renamed.to_dicts() == [{"total": 6}]
    assert original.to_dicts() == [{"x": 6}]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_native_aggregate_executes_without_complete_ast_schema(backend_name, backend_factory):
    import ibis

    from mountainash.relations.core.projection_names import IncompleteProjectionSchemaError

    source = backend_factory.create({"g": [0, 0, 1], "x": [3, 3, 8]}, backend_name)
    native = ma.col("x").sum().compile(source)
    if isinstance(native, ibis.Deferred):
        native = native.resolve(source)
    q = ma.relation(source).group_by("g").agg(ma.native(native).alias("total"))
    with pytest.raises(IncompleteProjectionSchemaError):
        _ = q.columns
    assert sorted_dicts(q.to_dicts(), "g") == [{"g": 0, "total": 6}, {"g": 1, "total": 8}]


@pytest.mark.parametrize("shape", ["wildcard", "regex", "zero", "native-multi", "native-zero"])
def test_aggregate_polars_expansion_passthrough(shape):
    """Polars native selector escape: no portable selector language is promised."""
    import polars as pl

    from mountainash.relations.core.projection_names import IncompleteProjectionSchemaError

    expressions = {
        "wildcard": ma.col("*").sum(),
        "regex": ma.col("^x.*$").sum(),
        "zero": ma.col("^absent$").sum(),
        "native-multi": ma.native(pl.col(["x", "y"]).sum()),
        "native-zero": ma.native(pl.col("^absent$").sum()),
    }
    q = ma.relation(pl.DataFrame({"x": [1, 2], "y": [4, 5]})).group_by().agg(
        expressions[shape], ma.lit(1).alias("one"),
    )
    if shape == "zero":
        assert q.columns == ["one"]
    else:
        with pytest.raises(IncompleteProjectionSchemaError):
            _ = q.columns
    expected = {
        "wildcard": [{"x": 3, "y": 9, "one": 1}],
        "regex": [{"x": 3, "one": 1}],
        "zero": [{"one": 1}],
        "native-multi": [{"x": 3, "y": 9, "one": 1}],
        "native-zero": [{"one": 1}],
    }
    assert q.to_dicts() == expected[shape]


def test_aggregate_native_duplicate_aliases_keep_backend_validation():
    """Polars multi-output alias validation remains owned by native execution."""
    import polars as pl

    q = ma.relation(pl.DataFrame({"x": [1], "y": [2]})).group_by().agg(
        ma.native(pl.col(["x", "y"]).sum()).alias("total"),
    )
    with pytest.raises(pl.exceptions.DuplicateError):
        q.collect()
