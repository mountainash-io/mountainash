"""Cross-backend result verification for aggregate operations.

Verifies that aggregate expressions produce identical results across all 7
backends. Discovered divergences are marked with pytest.xfail and documented
in upstream-issues.yaml.
"""

from __future__ import annotations

import pytest

import mountainash as ma
from mountainash.relations.core.relation_api.relation import Relation
from mountainash.relations.core.relation_nodes.substrait.reln_aggregate import (
    AggregateRelNode,
)


ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals-polars",
    "narwhals-pandas",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]


def _collect_agg(df, expr, alias="__value__"):
    """Collect an aggregate expression result as a scalar.

    Uses AggregateRelNode with empty keys (same approach as Relation._scalar_aggregate)
    which works correctly across all backends including Ibis.
    """
    r = ma.relation(df)
    aggregated = Relation(
        AggregateRelNode(
            input=r._node,
            keys=[],
            measures=[expr.alias(alias)],
        )
    )
    return aggregated.item(alias)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestAggregateSum:
    def test_sum_integers(self, backend_name, backend_factory):
        data = {"a": [1, 2, 3, 4, 5]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").sum())
        assert actual == 15

    def test_sum_with_nulls(self, backend_name, backend_factory):
        data = {"a": [1, None, 3, None, 5]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").sum())
        assert actual == 9

    def test_sum_all_nulls(self, backend_name, backend_factory):
        if backend_name == "ibis-duckdb":
            pytest.xfail("ibis-duckdb: cannot create tables with all-NULL columns")
        if backend_name in ("ibis-polars", "ibis-sqlite"):
            pytest.xfail("ibis: NullColumn has no 'sum' attribute")
        data = {"a": [None, None, None]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").sum())
        assert actual is None or actual == 0

    def test_sum_single_value(self, backend_name, backend_factory):
        data = {"a": [42]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").sum())
        assert actual == 42

    def test_sum_floats(self, backend_name, backend_factory):
        data = {"a": [1.5, 2.5, 3.0]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").sum())
        assert actual == pytest.approx(7.0, rel=1e-9)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestAggregateMean:
    def test_mean_integers(self, backend_name, backend_factory):
        data = {"a": [2, 4, 6, 8, 10]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").mean())
        assert actual == pytest.approx(6.0, rel=1e-9)

    def test_mean_with_nulls(self, backend_name, backend_factory):
        data = {"a": [2, None, 6, None, 10]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").mean())
        assert actual == pytest.approx(6.0, rel=1e-9)

    def test_mean_all_nulls(self, backend_name, backend_factory):
        if backend_name == "ibis-duckdb":
            pytest.xfail("ibis-duckdb: cannot create tables with all-NULL columns")
        if backend_name in ("ibis-polars", "ibis-sqlite"):
            pytest.xfail("ibis: NullColumn has no 'mean' attribute")
        data = {"a": [None, None, None]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").mean())
        assert actual is None

    def test_mean_single_value(self, backend_name, backend_factory):
        data = {"a": [7]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").mean())
        assert actual == pytest.approx(7.0, rel=1e-9)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestAggregateMin:
    def test_min_integers(self, backend_name, backend_factory):
        data = {"a": [5, 3, 8, 1, 9]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").min())
        assert actual == 1

    def test_min_with_nulls(self, backend_name, backend_factory):
        data = {"a": [5, None, 8, 1, None]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").min())
        assert actual == 1

    def test_min_all_nulls(self, backend_name, backend_factory):
        if backend_name == "ibis-duckdb":
            pytest.xfail("ibis-duckdb: cannot create tables with all-NULL columns")
        data = {"a": [None, None, None]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").min())
        assert actual is None

    def test_min_single_value(self, backend_name, backend_factory):
        data = {"a": [42]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").min())
        assert actual == 42


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestAggregateMax:
    def test_max_integers(self, backend_name, backend_factory):
        data = {"a": [5, 3, 8, 1, 9]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").max())
        assert actual == 9

    def test_max_with_nulls(self, backend_name, backend_factory):
        data = {"a": [5, None, 8, 1, None]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").max())
        assert actual == 8

    def test_max_all_nulls(self, backend_name, backend_factory):
        if backend_name == "ibis-duckdb":
            pytest.xfail("ibis-duckdb: cannot create tables with all-NULL columns")
        data = {"a": [None, None, None]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").max())
        assert actual is None

    def test_max_single_value(self, backend_name, backend_factory):
        data = {"a": [42]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").max())
        assert actual == 42


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestAggregateCount:
    def test_count_integers(self, backend_name, backend_factory):
        data = {"a": [1, 2, 3, 4, 5]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").count())
        assert actual == 5

    def test_count_with_nulls(self, backend_name, backend_factory):
        data = {"a": [1, None, 3, None, 5]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").count())
        assert actual == 3

    def test_count_all_nulls(self, backend_name, backend_factory):
        if backend_name == "ibis-duckdb":
            pytest.xfail("ibis-duckdb: cannot create tables with all-NULL columns")
        data = {"a": [None, None, None]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").count())
        assert actual == 0

    def test_count_single_value(self, backend_name, backend_factory):
        data = {"a": [42]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").count())
        assert actual == 1
