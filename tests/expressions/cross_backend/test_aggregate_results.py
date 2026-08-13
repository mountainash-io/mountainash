"""Cross-backend result verification for aggregate operations.

Verifies that aggregate expressions produce identical results across all 7
backends. Divergences route through declared DivergenceFacts via
``xfail_divergence``; genuine API-misuse gaps (first/last require ``.over()``;
``col().median()`` is unavailable) are pinned with ``pytest.raises`` fix-tests.
"""

from __future__ import annotations

import pytest

import mountainash as ma
from mountainash.relations.core.relation_api.relation import Relation
from mountainash.relations.core.relation_nodes.substrait.reln_aggregate import (
    AggregateRelNode,
)
from fixtures.backend_registry import ALL_BACKENDS
from fixtures.capability_gating import xfail_divergence


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


# all-null aggregate: ibis-duckdb rejects the untyped all-null table (IB-REL-06),
# ibis-polars/ibis-sqlite raise AttributeError on the inferred NullColumn (IB-AGG-06).
_ALLNULL = [
    pytest.param(
        b,
        marks=[xfail_divergence("IB-REL-06", backend=b), xfail_divergence("IB-AGG-06", backend=b)],
    )
    for b in ALL_BACKENDS
]
# min/max/count all-null: only ibis-duckdb rejects the table (IB-REL-06).
_ALLNULL_DUCK = [
    pytest.param(b, marks=xfail_divergence("IB-REL-06", backend=b)) for b in ALL_BACKENDS
]
# mode() / any_value(): order-dependent, rejected on a narwhals LazyFrame (NW-AGG-03).
_LAZY = [
    pytest.param(b, marks=xfail_divergence("NW-AGG-03", backend=b)) for b in ALL_BACKENDS
]
# product() non-zero data: ibis-polars returns None (IB-AGG-05); ibis-duckdb/sqlite compute it.
_PRODUCT = [
    pytest.param(b, marks=xfail_divergence("IB-AGG-05", backend=b)) for b in ALL_BACKENDS
]
# product() with a zero factor: ibis-polars None (IB-AGG-05); ibis-duckdb/sqlite break (IB-AGG-07).
_PRODUCT_ZERO = [
    pytest.param(
        b,
        marks=[xfail_divergence("IB-AGG-05", backend=b), xfail_divergence("IB-AGG-07", backend=b)],
    )
    for b in ALL_BACKENDS
]
# any_value()/n_unique() all-null: narwhals-lazy (NW-AGG-03) + ibis-duckdb
# (IB-REL-06); ibis-polars/ibis-sqlite compute None over an all-null column.
_ANYVAL_ALLNULL = [
    pytest.param(
        b,
        marks=[
            xfail_divergence("NW-AGG-03", backend=b),
            xfail_divergence("IB-REL-06", backend=b),
        ],
    )
    for b in ALL_BACKENDS
]


@pytest.mark.cross_backend
class TestAggregateSum:
    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_sum_integers(self, backend_name, backend_factory):
        data = {"a": [1, 2, 3, 4, 5]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").sum())
        assert actual == 15

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_sum_with_nulls(self, backend_name, backend_factory):
        data = {"a": [1, None, 3, None, 5]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").sum())
        assert actual == 9

    @pytest.mark.parametrize("backend_name", _ALLNULL)
    def test_sum_all_nulls(self, backend_name, backend_factory):
        data = {"a": [None, None, None]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").sum())
        assert actual is None or actual == 0

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_sum_single_value(self, backend_name, backend_factory):
        data = {"a": [42]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").sum())
        assert actual == 42


@pytest.mark.cross_backend
class TestAggregateMean:
    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_mean_integers(self, backend_name, backend_factory):
        data = {"a": [2, 4, 6, 8, 10]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").mean())
        assert actual == pytest.approx(6.0, rel=1e-9)

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_mean_with_nulls(self, backend_name, backend_factory):
        data = {"a": [2, None, 6, None, 10]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").mean())
        assert actual == pytest.approx(6.0, rel=1e-9)

    @pytest.mark.parametrize("backend_name", _ALLNULL)
    def test_mean_all_nulls(self, backend_name, backend_factory):
        data = {"a": [None, None, None]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").mean())
        assert actual is None

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_mean_single_value(self, backend_name, backend_factory):
        data = {"a": [7]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").mean())
        assert actual == pytest.approx(7.0, rel=1e-9)


@pytest.mark.cross_backend
class TestAggregateMin:
    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_min_integers(self, backend_name, backend_factory):
        data = {"a": [5, 3, 8, 1, 9]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").min())
        assert actual == 1

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_min_with_nulls(self, backend_name, backend_factory):
        data = {"a": [5, None, 8, 1, None]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").min())
        assert actual == 1

    @pytest.mark.parametrize("backend_name", _ALLNULL_DUCK)
    def test_min_all_nulls(self, backend_name, backend_factory):
        data = {"a": [None, None, None]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").min())
        assert actual is None

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_min_single_value(self, backend_name, backend_factory):
        data = {"a": [42]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").min())
        assert actual == 42


@pytest.mark.cross_backend
class TestAggregateMax:
    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_max_integers(self, backend_name, backend_factory):
        data = {"a": [5, 3, 8, 1, 9]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").max())
        assert actual == 9

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_max_with_nulls(self, backend_name, backend_factory):
        data = {"a": [5, None, 8, 1, None]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").max())
        assert actual == 8

    @pytest.mark.parametrize("backend_name", _ALLNULL_DUCK)
    def test_max_all_nulls(self, backend_name, backend_factory):
        data = {"a": [None, None, None]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").max())
        assert actual is None

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_max_single_value(self, backend_name, backend_factory):
        data = {"a": [42]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").max())
        assert actual == 42


@pytest.mark.cross_backend
class TestAggregateCount:
    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_count_integers(self, backend_name, backend_factory):
        data = {"a": [1, 2, 3, 4, 5]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").count())
        assert actual == 5

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_count_with_nulls(self, backend_name, backend_factory):
        data = {"a": [1, None, 3, None, 5]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").count())
        assert actual == 3

    @pytest.mark.parametrize("backend_name", _ALLNULL_DUCK)
    def test_count_all_nulls(self, backend_name, backend_factory):
        data = {"a": [None, None, None]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").count())
        assert actual == 0

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_count_single_value(self, backend_name, backend_factory):
        data = {"a": [42]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").count())
        assert actual == 1


@pytest.mark.cross_backend
class TestAggregateStdDev:
    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_std_dev_default(self, backend_name, backend_factory):
        data = {"a": [2, 4, 4, 4, 5, 5, 7, 9]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").std_dev())
        # Sample std dev (ddof=1) of [2,4,4,4,5,5,7,9] ≈ 2.138
        assert actual == pytest.approx(2.138089935299395, rel=1e-6)

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_std_dev_sample_explicit(self, backend_name, backend_factory):
        data = {"a": [2, 4, 4, 4, 5, 5, 7, 9]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").std_dev(distribution="SAMPLE"))
        assert actual == pytest.approx(2.138089935299395, rel=1e-6)

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_std_dev_with_nulls(self, backend_name, backend_factory):
        data = {"a": [2, None, 4, 4, None, 5, 5, 7, 9]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").std_dev())
        # After NULL removal: [2,4,4,5,5,7,9] → sample std ≈ 2.268
        assert actual is not None
        assert actual == pytest.approx(2.2677868380553634, rel=1e-6)

    @pytest.mark.parametrize("backend_name", _ALLNULL)
    def test_std_dev_all_nulls(self, backend_name, backend_factory):
        data = {"a": [None, None, None]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").std_dev())
        assert actual is None


@pytest.mark.cross_backend
class TestAggregateVariance:
    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_variance_default(self, backend_name, backend_factory):
        data = {"a": [2, 4, 4, 4, 5, 5, 7, 9]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").variance())
        # Sample variance (ddof=1) = 32/7 ≈ 4.571
        assert actual == pytest.approx(4.571428571428571, rel=1e-6)

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_variance_sample_explicit(self, backend_name, backend_factory):
        data = {"a": [2, 4, 4, 4, 5, 5, 7, 9]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").variance(distribution="SAMPLE"))
        assert actual == pytest.approx(4.571428571428571, rel=1e-6)

    @pytest.mark.parametrize("backend_name", _ALLNULL)
    def test_variance_all_nulls(self, backend_name, backend_factory):
        data = {"a": [None, None, None]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").variance())
        assert actual is None


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestAggregateMedian:
    # median() is not available as col().median() on any backend (Substrait
    # signature mismatch; the terminal aggregate raises AttributeError). Pinned
    # as a fix-test until median-as-terminal is implemented (backlog).
    def test_median_odd_count(self, backend_name, backend_factory):
        data = {"a": [1, 3, 5, 7, 9]}
        df = backend_factory.create(data, backend_name)
        with pytest.raises(AttributeError):
            _collect_agg(df, ma.col("a").median())

    def test_median_even_count(self, backend_name, backend_factory):
        data = {"a": [1, 3, 5, 7]}
        df = backend_factory.create(data, backend_name)
        with pytest.raises(AttributeError):
            _collect_agg(df, ma.col("a").median())

    def test_median_with_nulls(self, backend_name, backend_factory):
        data = {"a": [1, None, 5, None, 9]}
        df = backend_factory.create(data, backend_name)
        with pytest.raises(AttributeError):
            _collect_agg(df, ma.col("a").median())


@pytest.mark.cross_backend
class TestAggregateMedianAllNulls:
    @pytest.mark.parametrize("backend_name", _ALLNULL_DUCK)
    def test_median_all_nulls(self, backend_name, backend_factory):
        # ibis-duckdb rejects the all-null table (IB-REL-06) before median is
        # reached; every other backend raises AttributeError on col().median().
        data = {"a": [None, None, None]}
        df = backend_factory.create(data, backend_name)
        with pytest.raises(AttributeError):
            _collect_agg(df, ma.col("a").median())


@pytest.mark.cross_backend
class TestAggregateNUnique:
    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_n_unique_distinct(self, backend_name, backend_factory):
        data = {"a": [1, 2, 3, 4, 5]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").n_unique())
        assert actual == 5

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_n_unique_with_duplicates(self, backend_name, backend_factory):
        data = {"a": [1, 2, 2, 3, 3, 3]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").n_unique())
        assert actual == 3

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_n_unique_with_nulls(self, backend_name, backend_factory):
        data = {"a": [1, None, 2, None, 2]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").n_unique())
        # Backends differ on whether NULL counts as a unique value
        # Polars: NULL is a unique value → 3; SQL: NULL not counted → 2
        assert actual in [2, 3]

    @pytest.mark.parametrize("backend_name", _ALLNULL_DUCK)
    def test_n_unique_all_nulls(self, backend_name, backend_factory):
        data = {"a": [None, None, None]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").n_unique())
        # Either 0 (SQL) or 1 (Polars counts NULL as unique)
        assert actual in [0, 1]


# ─── First ──────────────────────────────────────────────────────────────────


@pytest.mark.cross_backend
class TestAggregateFirst:
    # first() is window-only — it requires .over() and is not usable as a
    # terminal aggregate (ValueError on every backend). Pinned as a fix-test.
    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_first_integers(self, backend_name, backend_factory):
        data = {"a": [10, 20, 30, 40, 50]}
        df = backend_factory.create(data, backend_name)
        with pytest.raises(ValueError):
            _collect_agg(df, ma.col("a").first())

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_first_strings(self, backend_name, backend_factory):
        data = {"a": ["apple", "banana", "cherry"]}
        df = backend_factory.create(data, backend_name)
        with pytest.raises(ValueError):
            _collect_agg(df, ma.col("a").first())

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_first_with_leading_null(self, backend_name, backend_factory):
        data = {"a": [None, 20, 30]}
        df = backend_factory.create(data, backend_name)
        with pytest.raises(ValueError):
            _collect_agg(df, ma.col("a").first())

    @pytest.mark.parametrize("backend_name", _ALLNULL_DUCK)
    def test_first_all_nulls(self, backend_name, backend_factory):
        # ibis-duckdb rejects the all-null table (IB-REL-06); the others raise
        # ValueError (first requires .over()).
        data = {"a": [None, None, None]}
        df = backend_factory.create(data, backend_name)
        with pytest.raises(ValueError):
            _collect_agg(df, ma.col("a").first())


# ─── Last ───────────────────────────────────────────────────────────────────


@pytest.mark.cross_backend
class TestAggregateLast:
    # last() is window-only — same fix-test contract as first().
    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_last_integers(self, backend_name, backend_factory):
        data = {"a": [10, 20, 30, 40, 50]}
        df = backend_factory.create(data, backend_name)
        with pytest.raises(ValueError):
            _collect_agg(df, ma.col("a").last())

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_last_strings(self, backend_name, backend_factory):
        data = {"a": ["apple", "banana", "cherry"]}
        df = backend_factory.create(data, backend_name)
        with pytest.raises(ValueError):
            _collect_agg(df, ma.col("a").last())

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_last_with_trailing_null(self, backend_name, backend_factory):
        data = {"a": [10, 20, None]}
        df = backend_factory.create(data, backend_name)
        with pytest.raises(ValueError):
            _collect_agg(df, ma.col("a").last())

    @pytest.mark.parametrize("backend_name", _ALLNULL_DUCK)
    def test_last_all_nulls(self, backend_name, backend_factory):
        data = {"a": [None, None, None]}
        df = backend_factory.create(data, backend_name)
        with pytest.raises(ValueError):
            _collect_agg(df, ma.col("a").last())


# ─── Mode ───────────────────────────────────────────────────────────────────


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _LAZY)
class TestAggregateMode:
    def test_mode_single_mode(self, backend_name, backend_factory):
        data = {"a": [1, 2, 2, 3, 3, 3, 4]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").mode())
        # Handle structural differences — Polars may return list, others scalar
        if isinstance(actual, list):
            assert 3 in actual
        else:
            assert actual == 3

    def test_mode_all_same(self, backend_name, backend_factory):
        data = {"a": [7, 7, 7, 7]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").mode())
        if isinstance(actual, list):
            assert 7 in actual
        else:
            assert actual == 7

    def test_mode_strings(self, backend_name, backend_factory):
        data = {"a": ["x", "y", "y", "z", "y"]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").mode())
        if isinstance(actual, list):
            assert "y" in actual
        else:
            assert actual == "y"


# ─── Product ────────────────────────────────────────────────────────────────


@pytest.mark.cross_backend
class TestAggregateProduct:
    @pytest.mark.parametrize("backend_name", _PRODUCT)
    def test_product_integers(self, backend_name, backend_factory):
        data = {"a": [2, 3, 4]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").product())
        # pandas/narwhals compute via log/exp — allow float approximation
        assert actual == pytest.approx(24)

    @pytest.mark.parametrize("backend_name", _PRODUCT)
    def test_product_with_one(self, backend_name, backend_factory):
        data = {"a": [5, 1, 1, 1]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").product())
        assert actual == pytest.approx(5)

    @pytest.mark.parametrize("backend_name", _PRODUCT_ZERO)
    def test_product_with_zero(self, backend_name, backend_factory):
        data = {"a": [10, 20, 0, 30]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").product())
        assert actual == 0

    @pytest.mark.parametrize("backend_name", _PRODUCT)
    def test_product_single_element(self, backend_name, backend_factory):
        data = {"a": [42]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").product())
        assert actual == pytest.approx(42)


# ─── AnyValue ───────────────────────────────────────────────────────────────


@pytest.mark.cross_backend
class TestAggregateAnyValue:
    @pytest.mark.parametrize("backend_name", _LAZY)
    def test_any_value_returns_valid_element(self, backend_name, backend_factory):
        data = {"a": [10, 20, 30, 40, 50]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").any_value())
        assert actual in [10, 20, 30, 40, 50]

    @pytest.mark.parametrize("backend_name", _LAZY)
    def test_any_value_strings(self, backend_name, backend_factory):
        data = {"a": ["alpha", "beta", "gamma"]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").any_value())
        assert actual in ["alpha", "beta", "gamma"]

    @pytest.mark.parametrize("backend_name", _LAZY)
    def test_any_value_with_nulls(self, backend_name, backend_factory):
        data = {"a": [None, 20, None, 40]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").any_value())
        # May return None or any non-null value
        assert actual in [None, 20, 40]

    @pytest.mark.parametrize("backend_name", _ANYVAL_ALLNULL)
    def test_any_value_all_nulls(self, backend_name, backend_factory):
        data = {"a": [None, None, None]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").any_value())
        assert actual is None
