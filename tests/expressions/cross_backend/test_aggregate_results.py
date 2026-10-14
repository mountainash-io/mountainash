"""Cross-backend result verification for aggregate operations.

Verifies that aggregate expressions produce identical results across all 7
backends. Exact scoped manifestation bindings select expected failures;
genuine API-misuse gaps (first/last require ``.over()``;
``col().median()`` is unavailable) are pinned with ``pytest.raises`` fix-tests.
"""

from __future__ import annotations

from decimal import Decimal as D, ROUND_HALF_EVEN
from functools import reduce

import polars as pl
import pytest

import mountainash as ma
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_VALUE,
    FKEY_SUBSTRAIT_SCALAR_AGGREGATE,
)
from mountainash.relations.core.relation_api.relation import Relation
from mountainash.relations.core.relation_nodes.substrait.reln_aggregate import (
    AggregateRelNode,
)
from fixtures.backend_registry import ALL_BACKENDS
from duckdb import OutOfRangeException
from ibis.common.exceptions import IbisTypeError
from narwhals.exceptions import InvalidOperationError
from fixtures.call_expectations import expect_call_failure


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

# min/max/count all-null: only ibis-duckdb rejects the table (IB-REL-06).

# mode() / any_value(): order-dependent, rejected on a narwhals LazyFrame (NW-AGG-03).

# any_value()/n_unique() all-null: narwhals-lazy (NW-AGG-03) + ibis-duckdb
# (IB-REL-06); ibis-polars/ibis-sqlite compute None over an all-null column.


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

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_sum_all_nulls(self, backend_name, backend_factory):
        data = {"a": [None, None, None]}
        if backend_name == "ibis-duckdb":
            with expect_call_failure(
                reason="DuckDB cannot construct a table with an inferred NULL-typed column",
                errors=(IbisTypeError,),
            ):
                backend_factory.create(data, backend_name)
        else:
            df = backend_factory.create(data, backend_name)
            with expect_call_failure(
                when=backend_name in ("ibis-polars", "ibis-sqlite"),
                reason="all-null sum raises on ibis-polars/ibis-sqlite",
                errors=(AttributeError,),
            ):
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

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_mean_all_nulls(self, backend_name, backend_factory):
        data = {"a": [None, None, None]}
        if backend_name == "ibis-duckdb":
            with expect_call_failure(
                reason="DuckDB cannot construct a table with an inferred NULL-typed column",
                errors=(IbisTypeError,),
            ):
                backend_factory.create(data, backend_name)
        else:
            df = backend_factory.create(data, backend_name)
            with expect_call_failure(
                when=backend_name in ("ibis-polars", "ibis-sqlite"),
                reason="all-null mean raises on ibis-polars/ibis-sqlite",
                errors=(AttributeError,),
            ):
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

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_min_all_nulls(self, backend_name, backend_factory):
        data = {"a": [None, None, None]}
        if backend_name == "ibis-duckdb":
            with expect_call_failure(
                reason="DuckDB cannot construct a table with an inferred NULL-typed column",
                errors=(IbisTypeError,),
            ):
                backend_factory.create(data, backend_name)
        else:
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

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_max_all_nulls(self, backend_name, backend_factory):
        data = {"a": [None, None, None]}
        if backend_name == "ibis-duckdb":
            with expect_call_failure(
                reason="DuckDB cannot construct a table with an inferred NULL-typed column",
                errors=(IbisTypeError,),
            ):
                backend_factory.create(data, backend_name)
        else:
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

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_count_all_nulls(self, backend_name, backend_factory):
        data = {"a": [None, None, None]}
        if backend_name == "ibis-duckdb":
            with expect_call_failure(
                reason="DuckDB cannot construct a table with an inferred NULL-typed column",
                errors=(IbisTypeError,),
            ):
                backend_factory.create(data, backend_name)
        else:
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

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_std_dev_all_nulls(self, backend_name, backend_factory):
        data = {"a": [None, None, None]}
        if backend_name == "ibis-duckdb":
            with expect_call_failure(
                reason="DuckDB cannot construct a table with an inferred NULL-typed column",
                errors=(IbisTypeError,),
            ):
                backend_factory.create(data, backend_name)
        else:
            df = backend_factory.create(data, backend_name)
            with expect_call_failure(
                when=backend_name in ("ibis-polars", "ibis-sqlite"),
                reason="all-null std_dev raises on ibis-polars/ibis-sqlite",
                errors=(AttributeError,),
            ):
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

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_variance_all_nulls(self, backend_name, backend_factory):
        data = {"a": [None, None, None]}
        if backend_name == "ibis-duckdb":
            with expect_call_failure(
                reason="DuckDB cannot construct a table with an inferred NULL-typed column",
                errors=(IbisTypeError,),
            ):
                backend_factory.create(data, backend_name)
        else:
            df = backend_factory.create(data, backend_name)
            with expect_call_failure(
                when=backend_name in ("ibis-polars", "ibis-sqlite"),
                reason="all-null variance raises on ibis-polars/ibis-sqlite",
                errors=(AttributeError,),
            ):
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
    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_median_all_nulls(self, backend_name, backend_factory):
        # ibis-duckdb rejects all-NULL table construction (IB-REL-06); every
        # other backend raises AttributeError on col().median().
        data = {"a": [None, None, None]}
        if backend_name == "ibis-duckdb":
            with expect_call_failure(
                reason="DuckDB cannot construct a table with an inferred NULL-typed column",
                errors=(IbisTypeError,),
            ):
                backend_factory.create(data, backend_name)
        else:
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

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_n_unique_all_nulls(self, backend_name, backend_factory):
        data = {"a": [None, None, None]}
        if backend_name == "ibis-duckdb":
            with expect_call_failure(
                reason="DuckDB cannot construct a table with an inferred NULL-typed column",
                errors=(IbisTypeError,),
            ):
                backend_factory.create(data, backend_name)
        else:
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

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_first_all_nulls(self, backend_name, backend_factory):
        # ibis-duckdb rejects all-NULL table construction (IB-REL-06); the
        # others raise ValueError because first requires .over().
        data = {"a": [None, None, None]}
        if backend_name == "ibis-duckdb":
            with expect_call_failure(
                reason="DuckDB cannot construct a table with an inferred NULL-typed column",
                errors=(IbisTypeError,),
            ):
                backend_factory.create(data, backend_name)
        else:
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

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_last_all_nulls(self, backend_name, backend_factory):
        data = {"a": [None, None, None]}
        if backend_name == "ibis-duckdb":
            with expect_call_failure(
                reason="DuckDB cannot construct a table with an inferred NULL-typed column",
                errors=(IbisTypeError,),
            ):
                backend_factory.create(data, backend_name)
        else:
            df = backend_factory.create(data, backend_name)
            with pytest.raises(ValueError):
                _collect_agg(df, ma.col("a").last())


# ─── Mode ───────────────────────────────────────────────────────────────────


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestAggregateMode:
    def test_mode_single_mode(self, backend_name, backend_factory):
        data = {"a": [1, 2, 2, 3, 3, 3, 4]}
        df = backend_factory.create(data, backend_name)
        with expect_call_failure(
            when=backend_name == 'narwhals-lazy',
            reason='mode() and any_value() raise on narwhals-lazy',
            errors=(InvalidOperationError,),
        ):
            actual = _collect_agg(df, ma.col("a").mode())
            # Handle structural differences — Polars may return list, others scalar
            if isinstance(actual, list):
                assert 3 in actual
            else:
                assert actual == 3

    def test_mode_all_same(self, backend_name, backend_factory):
        data = {"a": [7, 7, 7, 7]}
        df = backend_factory.create(data, backend_name)
        with expect_call_failure(
            when=backend_name == 'narwhals-lazy',
            reason='mode() and any_value() raise on narwhals-lazy',
            errors=(InvalidOperationError,),
        ):
            actual = _collect_agg(df, ma.col("a").mode())
            if isinstance(actual, list):
                assert 7 in actual
            else:
                assert actual == 7

    def test_mode_strings(self, backend_name, backend_factory):
        data = {"a": ["x", "y", "y", "z", "y"]}
        df = backend_factory.create(data, backend_name)
        with expect_call_failure(
            when=backend_name == 'narwhals-lazy',
            reason='mode() and any_value() raise on narwhals-lazy',
            errors=(InvalidOperationError,),
        ):
            actual = _collect_agg(df, ma.col("a").mode())
            if isinstance(actual, list):
                assert "y" in actual
            else:
                assert actual == "y"


# ─── Product ────────────────────────────────────────────────────────────────


@pytest.mark.cross_backend
class TestAggregateProduct:
    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    @pytest.mark.parametrize(
        "values,expected",
        [
            ([2, 3, 4], 24),
            ([10, 0, 30], 0),
            ([-2, 3], -6),
            ([9007199254740993, 1], 9007199254740993),
            ([2, None, 3], 6),
        ],
        ids=["positive", "zero", "negative", "exact-int64", "null-operand"],
    )
    def test_product_backend_contract(self, backend_name, backend_factory, values, expected):
        df = backend_factory.create({"a": values}, backend_name)
        if backend_name.startswith("polars"):
            assert _collect_agg(df, ma.col("a").product()) == expected
        else:
            with pytest.raises(BackendCapabilityError):
                _collect_agg(df, ma.col("a").product())


# ─── AnyValue ───────────────────────────────────────────────────────────────


@pytest.mark.cross_backend
class TestAggregateAnyValue:
    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_any_value_returns_valid_element(self, backend_name, backend_factory):
        data = {"a": [10, 20, 30, 40, 50]}
        df = backend_factory.create(data, backend_name)
        with expect_call_failure(
            when=backend_name == 'narwhals-lazy',
            reason='mode() and any_value() raise on narwhals-lazy',
            errors=(InvalidOperationError,),
        ):
            actual = _collect_agg(df, ma.col("a").any_value())
            assert actual in [10, 20, 30, 40, 50]

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_any_value_strings(self, backend_name, backend_factory):
        data = {"a": ["alpha", "beta", "gamma"]}
        df = backend_factory.create(data, backend_name)
        with expect_call_failure(
            when=backend_name == 'narwhals-lazy',
            reason='mode() and any_value() raise on narwhals-lazy',
            errors=(InvalidOperationError,),
        ):
            actual = _collect_agg(df, ma.col("a").any_value())
            assert actual in ["alpha", "beta", "gamma"]

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_any_value_with_nulls(self, backend_name, backend_factory):
        data = {"a": [None, 20, None, 40]}
        df = backend_factory.create(data, backend_name)
        with expect_call_failure(
            when=backend_name == 'narwhals-lazy',
            reason='mode() and any_value() raise on narwhals-lazy',
            errors=(InvalidOperationError,),
        ):
            actual = _collect_agg(df, ma.col("a").any_value())
            # May return None or any non-null value
            assert actual in [None, 20, 40]

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_any_value_all_nulls(self, backend_name, backend_factory):
        data = {"a": [None, None, None]}
        if backend_name == "ibis-duckdb":
            with expect_call_failure(
                reason="DuckDB cannot construct a table with an inferred NULL-typed column",
                errors=(IbisTypeError,),
            ):
                backend_factory.create(data, backend_name)
        else:
            df = backend_factory.create(data, backend_name)
            with expect_call_failure(
                when=backend_name == "narwhals-lazy",
                reason="any_value() raises on narwhals-lazy",
                errors=(InvalidOperationError,),
            ):
                actual = _collect_agg(df, ma.col("a").any_value())
                assert actual is None


# ─── Declared Decimal aggregate arithmetic ─────────────────────────────────


_DECIMAL_AGGREGATE_ORACLES = {
    "sum": lambda values: sum(values, D("0")),
    "min": min,
    "max": max,
    "mean": lambda values: sum(values, D("0")) / len(values),
    "product": lambda values: reduce(lambda left, right: left * right, values, D("1")),
}

_DECIMAL_AGGREGATE_INPUTS = [
    pytest.param([D("1.001"), D("1.002"), None], [D("1.001"), D("1.002")], id="fractional-null"),
    pytest.param([D("-2.345")], [D("-2.345")], id="signed-singleton"),
    pytest.param([D("-1.250"), D("0.000"), D("2.500")], [D("-1.250"), D("0.000"), D("2.500")], id="signed-zero"),
    pytest.param([None, None], [], id="typed-all-null"),
    pytest.param([], [], id="typed-empty"),
]


def _decimal_aggregate_expected(operation, values, backend_name):
    if values:
        return _DECIMAL_AGGREGATE_ORACLES[operation](values)
    if operation == "sum":
        return None if backend_name.startswith("ibis-") else D("0")
    if operation == "product" and backend_name.startswith("polars"):
        return D("1")
    return None


def _authored_decimal_expected(operation, values, backend_name):
    exact = _decimal_aggregate_expected(operation, values, backend_name)
    if exact is None:
        return None
    return exact.quantize(D("0.000001"), rounding=ROUND_HALF_EVEN)


def _assert_function_key(error, function_key):
    assert error.value.function_key is function_key


def _global_decimal_aggregate(relation, operation):
    return relation.group_by().agg(
        getattr(ma.col("amount"), operation)().alias("result")
    )


@pytest.mark.cross_backend
class TestDeclaredDecimalAggregateArithmetic:
    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    @pytest.mark.parametrize("operation", tuple(_DECIMAL_AGGREGATE_ORACLES))
    @pytest.mark.parametrize("data,values", _DECIMAL_AGGREGATE_INPUTS)
    def test_authored_fp64_global_aggregate_then_decimal_cast(
        self, backend_name, operation, data, values, declared_decimal_frame, backend_factory
    ):
        if backend_name == "ibis-sqlite":
            frame = backend_factory.create({"amount": [1.001, 1.002]}, backend_name)
        else:
            frame = declared_decimal_frame({"amount": data}, {"amount": (12, 3)})
        working = ma.relation(frame).select(ma.col("amount").cast("fp64").alias("amount"))

        # Product refusal is checked before any Decimal cast, including SQLite.
        if operation == "product" and not backend_name.startswith("polars"):
            with pytest.raises(BackendCapabilityError) as error:
                _global_decimal_aggregate(working, operation).to_polars()
            _assert_function_key(error, FKEY_SUBSTRAIT_SCALAR_AGGREGATE.PRODUCT)
            return

        reduced = _global_decimal_aggregate(working, operation)
        casted = reduced.select(
            ma.col("result").cast(
                ma.DecimalDtype(16, 6), rounding="half_to_even"
            ).alias("result")
        )
        if backend_name == "ibis-sqlite":
            with pytest.raises(BackendCapabilityError) as error:
                casted.to_polars()
            _assert_function_key(error, FKEY_MOUNTAINASH_SCALAR_VALUE.DECIMAL_CAST)
            return
        if backend_name in {
            "pandas", "narwhals-polars", "narwhals-pandas", "narwhals-lazy"
        }:
            with pytest.raises(BackendCapabilityError) as error:
                casted.to_polars()
            _assert_function_key(error, FKEY_MOUNTAINASH_SCALAR_VALUE.DECIMAL_CAST)
            return

        from mountainash.relations.schema_inference import SchemaTypeStatus
        assert casted.schema["result"] in (SchemaTypeStatus.UNKNOWN, ma.DecimalDtype(16, 6))
        output = casted.to_polars()
        expected = _authored_decimal_expected(operation, values, backend_name)
        assert output.schema["result"] == pl.Decimal(16, 6)
        assert output["result"].to_list() == [expected]


    @pytest.mark.cross_backend
    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    @pytest.mark.parametrize("operation", tuple(_DECIMAL_AGGREGATE_ORACLES))
    @pytest.mark.parametrize("data,values", _DECIMAL_AGGREGATE_INPUTS)
    def test_direct_declared_decimal_global_aggregate(
        self, backend_name, operation, data, values, declared_decimal_frame, backend_factory
    ):
        if backend_name == "ibis-sqlite":
            # SQLite has no native Decimal input; exercise its public cast
            # refusal as the direct-route capability disposition.
            frame = backend_factory.create({"amount": [1.001, 1.002]}, backend_name)
            working = ma.relation(frame).select(
                ma.col("amount").cast("fp64").alias("amount")
            )
            if operation == "product":
                with pytest.raises(BackendCapabilityError) as error:
                    _global_decimal_aggregate(working, operation).to_polars()
                _assert_function_key(error, FKEY_SUBSTRAIT_SCALAR_AGGREGATE.PRODUCT)
            else:
                reduced = _global_decimal_aggregate(working, operation)
                with pytest.raises(BackendCapabilityError) as error:
                    reduced.select(
                        ma.col("result").cast(
                            ma.DecimalDtype(16, 6), rounding="half_to_even"
                        ).alias("result")
                    ).to_polars()
                _assert_function_key(error, FKEY_MOUNTAINASH_SCALAR_VALUE.DECIMAL_CAST)
            return

        frame = declared_decimal_frame({"amount": data}, {"amount": (12, 3)})
        if operation == "product" and not backend_name.startswith("polars"):
            with pytest.raises(BackendCapabilityError) as error:
                _global_decimal_aggregate(ma.relation(frame), operation).to_polars()
            _assert_function_key(error, FKEY_SUBSTRAIT_SCALAR_AGGREGATE.PRODUCT)
            return
        reduced = _global_decimal_aggregate(ma.relation(frame), operation)

        exact = (
            _DECIMAL_AGGREGATE_ORACLES[operation](values)
            if values
            else _decimal_aggregate_expected(operation, values, backend_name)
        )
        output = reduced.to_polars()
        if operation == "mean" and backend_name in {
            "polars", "polars-lazy", "narwhals-polars", "narwhals-lazy"
        }:
            assert output.schema["result"] == pl.Float64
            expected_values = [None] if exact is None else [float(exact)]
            assert output["result"].to_list() == expected_values
            return

        if (
            backend_name in {"pandas", "narwhals-pandas"}
            and not values
            and operation in {"min", "max", "mean"}
        ):
            assert output.schema["result"] == pl.Null
        else:
            assert output.schema["result"].is_decimal()
        if operation == "mean":
            if backend_name.startswith("ibis-") and values == [D("1.001"), D("1.002")]:
                with expect_call_failure(
                    reason="Ibis native Decimal mean extraction rounds 1.0015 to 1.002",
                    errors=(AssertionError,),
                ):
                    assert output["result"].to_list() == [exact]
                return
            expected = exact.quantize(D("0.001"), rounding=ROUND_HALF_EVEN) if exact is not None else None
        else:
            expected = exact
        if operation == "product" and values == [D("1.001"), D("1.002")]:
            with expect_call_failure(
                when=backend_name.startswith("polars"),
                reason="native Polars Decimal product returns 1.003 rather than the exact 1.003002",
                errors=(AssertionError,),
            ):
                assert output["result"].to_list() == [expected]
            return
        assert output["result"].to_list() == [expected]
