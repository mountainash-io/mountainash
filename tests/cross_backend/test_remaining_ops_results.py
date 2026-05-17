"""Cross-backend result verification for remaining operations.

Tests relative datetime ops (older_than, newer_than),
rfloor_divide, and null aggregates (null_count, has_nulls).

is_dst is excluded — it currently fails at the AST level
(ScalarFunctionNode options=None validation error).
"""

from __future__ import annotations

from datetime import datetime

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

TEMPORAL_BACKENDS = [
    "polars",
    "narwhals-polars",
    "narwhals-pandas",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]


def _collect_agg(df, expr, alias="__value__"):
    """Collect an aggregate expression result as a scalar."""
    r = ma.relation(df)
    aggregated = Relation(
        AggregateRelNode(
            input=r._node,
            keys=[],
            measures=[expr.alias(alias)],
        )
    )
    return aggregated.item(alias)


# =============================================================================
# older_than
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", TEMPORAL_BACKENDS)
class TestDtOlderThan:
    """Verify older_than returns True for timestamps older than the threshold."""

    def test_older_than_basic(self, backend_name, backend_factory, collect_expr):
        data = {"ts": [datetime(2020, 1, 1), datetime(2026, 1, 1)]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("ts").dt.older_than("365d"))
        # 2020-01-01 is more than 365 days old; 2026-01-01 is in the future
        assert actual == [True, False]

    def test_older_than_all_old(self, backend_name, backend_factory, collect_expr):
        data = {"ts": [datetime(2000, 6, 15), datetime(2010, 3, 1)]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("ts").dt.older_than("30d"))
        assert actual == [True, True]

    def test_older_than_none_old(self, backend_name, backend_factory, collect_expr):
        data = {"ts": [datetime(2026, 5, 1), datetime(2026, 5, 10)]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("ts").dt.older_than("3650d"))
        assert actual == [False, False]


# =============================================================================
# newer_than
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", TEMPORAL_BACKENDS)
class TestDtNewerThan:
    """Verify newer_than returns True for timestamps newer than the threshold."""

    def test_newer_than_basic(self, backend_name, backend_factory, collect_expr):
        data = {"ts": [datetime(2020, 1, 1), datetime(2026, 1, 1)]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("ts").dt.newer_than("365d"))
        # 2020-01-01 is not within last 365 days; 2026-01-01 is
        assert actual == [False, True]

    def test_newer_than_all_recent(self, backend_name, backend_factory, collect_expr):
        data = {"ts": [datetime(2026, 5, 1), datetime(2026, 5, 10)]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("ts").dt.newer_than("3650d"))
        assert actual == [True, True]

    def test_newer_than_none_recent(self, backend_name, backend_factory, collect_expr):
        data = {"ts": [datetime(2000, 6, 15), datetime(2010, 3, 1)]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("ts").dt.newer_than("30d"))
        assert actual == [False, False]


# =============================================================================
# rfloor_divide
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestRfloorDivide:
    """Verify rfloor_divide (reversed floor division: b // a)."""

    def test_rfloor_divide_basic(self, backend_name, backend_factory, collect_expr):
        data = {"a": [7, 10, -7], "b": [2, 3, 2]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").rfloor_divide(ma.col("b")))
        # b // a: 2//7=0, 3//10=0, 2//-7=-1
        assert actual == [0, 0, -1]

    def test_rfloor_divide_exact(self, backend_name, backend_factory, collect_expr):
        data = {"a": [2, 5, 3], "b": [10, 25, 9]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").rfloor_divide(ma.col("b")))
        # b // a: 10//2=5, 25//5=5, 9//3=3
        assert actual == [5, 5, 3]

    def test_rfloor_divide_ones(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1, 1, 1], "b": [7, 0, -3]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").rfloor_divide(ma.col("b")))
        # b // 1 = b
        assert actual == [7, 0, -3]


# =============================================================================
# null_count (aggregate)
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestNullCount:
    """Verify null_count aggregate counts null values."""

    def test_null_count_some_nulls(self, backend_name, backend_factory):
        data = {"a": [1, None, 3, None, 5]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").null_count())
        assert actual == 2

    def test_null_count_no_nulls(self, backend_name, backend_factory):
        data = {"a": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").null_count())
        assert actual == 0

    def test_null_count_all_nulls(self, backend_name, backend_factory):
        if backend_name == "ibis-duckdb":
            pytest.xfail("DuckDB cannot create tables with all-NULL columns (no type inference)")
        data = {"a": [None, None, None]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").null_count())
        assert actual == 3


# =============================================================================
# has_nulls (aggregate)
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestHasNulls:
    """Verify has_nulls aggregate returns boolean."""

    def test_has_nulls_true(self, backend_name, backend_factory):
        data = {"a": [1, None, 3, None, 5]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").has_nulls())
        assert actual is True

    def test_has_nulls_false(self, backend_name, backend_factory):
        data = {"a": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").has_nulls())
        assert actual is False

    def test_has_nulls_all_nulls(self, backend_name, backend_factory):
        if backend_name == "ibis-duckdb":
            pytest.xfail("DuckDB cannot create tables with all-NULL columns (no type inference)")
        data = {"a": [None, None, None]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").has_nulls())
        assert actual is True
