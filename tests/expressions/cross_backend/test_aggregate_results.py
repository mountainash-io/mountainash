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


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestAggregateStdDev:
    def test_std_dev_default(self, backend_name, backend_factory):
        data = {"a": [2, 4, 4, 4, 5, 5, 7, 9]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").std_dev())
        # Sample std dev (ddof=1) of [2,4,4,4,5,5,7,9] ≈ 2.138
        assert actual == pytest.approx(2.138089935299395, rel=1e-6)

    def test_std_dev_sample_explicit(self, backend_name, backend_factory):
        data = {"a": [2, 4, 4, 4, 5, 5, 7, 9]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").std_dev(distribution="SAMPLE"))
        assert actual == pytest.approx(2.138089935299395, rel=1e-6)

    def test_std_dev_with_nulls(self, backend_name, backend_factory):
        data = {"a": [2, None, 4, 4, None, 5, 5, 7, 9]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").std_dev())
        # After NULL removal: [2,4,4,5,5,7,9] → sample std ≈ 2.268
        assert actual is not None
        assert actual == pytest.approx(2.2677868380553634, rel=1e-6)

    def test_std_dev_all_nulls(self, backend_name, backend_factory):
        if backend_name == "ibis-duckdb":
            pytest.xfail("ibis-duckdb: cannot create tables with all-NULL columns")
        if backend_name in ("ibis-polars", "ibis-sqlite"):
            pytest.xfail("ibis: NullColumn has no 'std' attribute")
        data = {"a": [None, None, None]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").std_dev())
        assert actual is None


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestAggregateVariance:
    def test_variance_default(self, backend_name, backend_factory):
        if backend_name in ("pandas", "narwhals-polars", "narwhals-pandas"):
            pytest.xfail("narwhals: variance() uses Expr.pow() which Narwhals lacks")
        data = {"a": [2, 4, 4, 4, 5, 5, 7, 9]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").variance())
        # Sample variance (ddof=1) = 32/7 ≈ 4.571
        assert actual == pytest.approx(4.571428571428571, rel=1e-6)

    def test_variance_sample_explicit(self, backend_name, backend_factory):
        if backend_name in ("pandas", "narwhals-polars", "narwhals-pandas"):
            pytest.xfail("narwhals: variance() uses Expr.pow() which Narwhals lacks")
        data = {"a": [2, 4, 4, 4, 5, 5, 7, 9]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").variance(distribution="SAMPLE"))
        assert actual == pytest.approx(4.571428571428571, rel=1e-6)

    def test_variance_all_nulls(self, backend_name, backend_factory):
        if backend_name == "ibis-duckdb":
            pytest.xfail("ibis-duckdb: cannot create tables with all-NULL columns")
        if backend_name in ("ibis-polars", "ibis-sqlite"):
            pytest.xfail("ibis: NullColumn has no 'var' attribute")
        if backend_name in ("pandas", "narwhals-polars", "narwhals-pandas"):
            pytest.xfail("narwhals: variance() uses Expr.pow() which Narwhals lacks")
        data = {"a": [None, None, None]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").variance())
        assert actual is None


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestAggregateMedian:
    def test_median_odd_count(self, backend_name, backend_factory):
        pytest.xfail("median() not available as col().median() — Substrait signature mismatch")
        data = {"a": [1, 3, 5, 7, 9]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").median())
        assert actual == pytest.approx(5.0, rel=1e-9)

    def test_median_even_count(self, backend_name, backend_factory):
        pytest.xfail("median() not available as col().median() — Substrait signature mismatch")
        data = {"a": [1, 3, 5, 7]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").median())
        assert actual == pytest.approx(4.0, rel=1e-9)

    def test_median_with_nulls(self, backend_name, backend_factory):
        pytest.xfail("median() not available as col().median() — Substrait signature mismatch")
        data = {"a": [1, None, 5, None, 9]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").median())
        assert actual == pytest.approx(5.0, rel=1e-9)

    def test_median_all_nulls(self, backend_name, backend_factory):
        pytest.xfail("median() not available as col().median() — Substrait signature mismatch")
        data = {"a": [None, None, None]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").median())
        assert actual is None


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestAggregateNUnique:
    def test_n_unique_distinct(self, backend_name, backend_factory):
        data = {"a": [1, 2, 3, 4, 5]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").n_unique())
        assert actual == 5

    def test_n_unique_with_duplicates(self, backend_name, backend_factory):
        data = {"a": [1, 2, 2, 3, 3, 3]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").n_unique())
        assert actual == 3

    def test_n_unique_with_nulls(self, backend_name, backend_factory):
        data = {"a": [1, None, 2, None, 2]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").n_unique())
        # Backends differ on whether NULL counts as a unique value
        # Polars: NULL is a unique value → 3; SQL: NULL not counted → 2
        assert actual in [2, 3]

    def test_n_unique_all_nulls(self, backend_name, backend_factory):
        if backend_name == "ibis-duckdb":
            pytest.xfail("ibis-duckdb: cannot create tables with all-NULL columns")
        if backend_name in ("ibis-polars", "ibis-sqlite"):
            pytest.xfail("ibis: NullColumn has no 'nunique' attribute")
        data = {"a": [None, None, None]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").n_unique())
        # Either 0 (SQL) or 1 (Polars counts NULL as unique)
        assert actual in [0, 1]


# ─── First ──────────────────────────────────────────────────────────────────


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestAggregateFirst:
    def test_first_integers(self, backend_name, backend_factory):
        pytest.xfail("first() is window-only — requires .over(); not usable as aggregate")
        data = {"a": [10, 20, 30, 40, 50]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").first())
        assert actual == 10

    def test_first_strings(self, backend_name, backend_factory):
        pytest.xfail("first() is window-only — requires .over(); not usable as aggregate")
        data = {"a": ["apple", "banana", "cherry"]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").first())
        assert actual == "apple"

    def test_first_with_leading_null(self, backend_name, backend_factory):
        pytest.xfail("first() is window-only — requires .over(); not usable as aggregate")
        data = {"a": [None, 20, 30]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").first())
        # Some backends return NULL (first value is NULL), others skip nulls
        assert actual in [None, 20]

    def test_first_all_nulls(self, backend_name, backend_factory):
        pytest.xfail("first() is window-only — requires .over(); not usable as aggregate")
        data = {"a": [None, None, None]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").first())
        assert actual is None


# ─── Last ───────────────────────────────────────────────────────────────────


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestAggregateLast:
    def test_last_integers(self, backend_name, backend_factory):
        pytest.xfail("last() is window-only — requires .over(); not usable as aggregate")
        data = {"a": [10, 20, 30, 40, 50]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").last())
        assert actual == 50

    def test_last_strings(self, backend_name, backend_factory):
        pytest.xfail("last() is window-only — requires .over(); not usable as aggregate")
        data = {"a": ["apple", "banana", "cherry"]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").last())
        assert actual == "cherry"

    def test_last_with_trailing_null(self, backend_name, backend_factory):
        pytest.xfail("last() is window-only — requires .over(); not usable as aggregate")
        data = {"a": [10, 20, None]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").last())
        # Some backends return NULL (last value is NULL), others skip nulls
        assert actual in [None, 20]

    def test_last_all_nulls(self, backend_name, backend_factory):
        pytest.xfail("last() is window-only — requires .over(); not usable as aggregate")
        data = {"a": [None, None, None]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").last())
        assert actual is None


# ─── Mode ───────────────────────────────────────────────────────────────────


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestAggregateMode:
    def test_mode_single_mode(self, backend_name, backend_factory):
        if backend_name in ("pandas", "narwhals-polars", "narwhals-pandas"):
            pytest.xfail("mode() not supported by Narwhals backend")
        data = {"a": [1, 2, 2, 3, 3, 3, 4]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").mode())
        # Handle structural differences — Polars may return list, others scalar
        if isinstance(actual, list):
            assert 3 in actual
        else:
            assert actual == 3

    def test_mode_all_same(self, backend_name, backend_factory):
        if backend_name in ("pandas", "narwhals-polars", "narwhals-pandas"):
            pytest.xfail("mode() not supported by Narwhals backend")
        data = {"a": [7, 7, 7, 7]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").mode())
        if isinstance(actual, list):
            assert 7 in actual
        else:
            assert actual == 7

    def test_mode_strings(self, backend_name, backend_factory):
        if backend_name in ("pandas", "narwhals-polars", "narwhals-pandas"):
            pytest.xfail("mode() not supported by Narwhals backend")
        data = {"a": ["x", "y", "y", "z", "y"]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").mode())
        if isinstance(actual, list):
            assert "y" in actual
        else:
            assert actual == "y"


# ─── Product ────────────────────────────────────────────────────────────────


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestAggregateProduct:
    def test_product_integers(self, backend_name, backend_factory):
        if backend_name in ("ibis-polars", "ibis-duckdb", "ibis-sqlite"):
            pytest.xfail("ibis backends: product() returns None (not implemented as aggregate)")
        data = {"a": [2, 3, 4]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").product())
        # pandas/narwhals compute via log/exp — allow float approximation
        assert actual == pytest.approx(24)

    def test_product_with_one(self, backend_name, backend_factory):
        if backend_name in ("ibis-polars", "ibis-duckdb", "ibis-sqlite"):
            pytest.xfail("ibis backends: product() returns None (not implemented as aggregate)")
        data = {"a": [5, 1, 1, 1]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").product())
        assert actual == pytest.approx(5)

    def test_product_with_zero(self, backend_name, backend_factory):
        if backend_name in ("ibis-polars", "ibis-duckdb", "ibis-sqlite"):
            pytest.xfail("ibis backends: product() returns None (not implemented as aggregate)")
        data = {"a": [10, 20, 0, 30]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").product())
        assert actual == 0

    def test_product_single_element(self, backend_name, backend_factory):
        if backend_name in ("ibis-polars", "ibis-duckdb", "ibis-sqlite"):
            pytest.xfail("ibis backends: product() returns None (not implemented as aggregate)")
        data = {"a": [42]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").product())
        assert actual == pytest.approx(42)


# ─── AnyValue ───────────────────────────────────────────────────────────────


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestAggregateAnyValue:
    def test_any_value_returns_valid_element(self, backend_name, backend_factory):
        data = {"a": [10, 20, 30, 40, 50]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").any_value())
        assert actual in [10, 20, 30, 40, 50]

    def test_any_value_strings(self, backend_name, backend_factory):
        data = {"a": ["alpha", "beta", "gamma"]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").any_value())
        assert actual in ["alpha", "beta", "gamma"]

    def test_any_value_with_nulls(self, backend_name, backend_factory):
        data = {"a": [None, 20, None, 40]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").any_value())
        # May return None or any non-null value
        assert actual in [None, 20, 40]

    def test_any_value_all_nulls(self, backend_name, backend_factory):
        if backend_name == "ibis-duckdb":
            pytest.xfail("ibis-duckdb: cannot create tables with all-NULL columns")
        if backend_name in ("ibis-polars", "ibis-sqlite"):
            pytest.xfail("ibis: NullColumn attribute error")
        data = {"a": [None, None, None]}
        df = backend_factory.create(data, backend_name)
        actual = _collect_agg(df, ma.col("a").any_value())
        assert actual is None
