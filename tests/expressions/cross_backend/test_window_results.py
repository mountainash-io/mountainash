"""Cross-backend result verification for window operations.

Verifies that window expressions produce identical results across all 9
backends. Window functions require .over() context for partitioned operations.

Test data uses unique sort keys to ensure deterministic output ordering.

Known divergences use exact scoped observer bindings:
- ibis: rank(method='average'/'max') has no SQL equivalent (IB-WIN-05)
- ibis: cum_prod unsupported (IB-WIN-04)
- ibis/narwhals/pandas: rank(method='dense'/'ordinal') via method param (MA-WIN-01),
  ntile (MA-WIN-02), .over() on elementwise expressions (MA-WIN-03)
- narwhals/pandas: percent_rank/cume_dist/nth_value/diff(n>1) (NW-WIN-04)
- narwhals-lazy: order-dependent window ops on a LazyFrame (NW-WIN-03)
"""

from __future__ import annotations

import pytest

import mountainash as ma
from fixtures.backend_registry import ALL_BACKENDS
from ibis.common.annotations import SignatureValidationError
from ibis.common.exceptions import IbisTypeError, OperationNotDefinedError
from mountainash.core.types import BackendCapabilityError
from narwhals.exceptions import InvalidOperationError
from polars.exceptions import ShapeError
from fixtures.call_expectations import expect_call_failure


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowRank:
    """Test rank(method='min') — equivalent to SQL RANK()."""

    def test_rank_basic(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "B", "B"], "score": [10, 30, 20, 15, 25]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").rank(method="min").over("group")
        result = (
            ma.relation(df).select(ma.col("group"), ma.col("score"), expr.alias("rnk")).sort("group", "score").to_dict()
        )
        # A: scores [10,20,30] -> ranks [1,2,3]; B: scores [15,25] -> ranks [1,2]
        assert result["rnk"] == [1, 2, 3, 1, 2]

    def test_rank_with_ties(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "A"], "score": [10, 20, 20, 30], "id": [1, 2, 3, 4]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").rank(method="min").over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), ma.col("id"), expr.alias("rnk"))
            .sort("group", "score", "id")
            .to_dict()
        )
        # Tied scores get same rank; next rank skips: [1, 2, 2, 4]
        assert result["rnk"] == [1, 2, 2, 4]

    def test_rank_single_row_partition(self, backend_name, backend_factory):
        data = {"group": ["A"], "score": [99]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").rank(method="min").over("group")
        result = ma.relation(df).select(ma.col("group"), ma.col("score"), expr.alias("rnk")).to_dict()
        assert result["rnk"] == [1]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowDenseRank:
    """Test dense_rank() — equivalent to SQL DENSE_RANK()."""

    def test_dense_rank_basic(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "B", "B"], "score": [10, 30, 20, 15, 25]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").dense_rank().over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), expr.alias("drnk"))
            .sort("group", "score")
            .to_dict()
        )
        assert result["drnk"] == [1, 2, 3, 1, 2]

    def test_dense_rank_with_ties(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "A"], "score": [10, 20, 20, 30], "id": [1, 2, 3, 4]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").dense_rank().over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), ma.col("id"), expr.alias("drnk"))
            .sort("group", "score", "id")
            .to_dict()
        )
        # Dense rank: no gaps -> [1, 2, 2, 3]
        assert result["drnk"] == [1, 2, 2, 3]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowRowNumber:
    """Test row_number() — equivalent to SQL ROW_NUMBER()."""

    def test_row_number_basic(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "B", "B"], "score": [10, 30, 20, 15, 25]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").row_number().over("group")
        result = (
            ma.relation(df).select(ma.col("group"), ma.col("score"), expr.alias("rn")).sort("group", "score").to_dict()
        )
        assert result["rn"] == [1, 2, 3, 1, 2]

    def test_row_number_single_partition(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A"], "score": [30, 10, 20]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").row_number().over("group")
        result = (
            ma.relation(df).select(ma.col("group"), ma.col("score"), expr.alias("rn")).sort("group", "score").to_dict()
        )
        assert result["rn"] == [1, 2, 3]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowLead:
    """Test lead(n) — next value in partition."""

    def test_lead_basic(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "B", "B", "B"], "score": [10, 20, 30, 15, 25, 35]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").lead(1).over("group")
        with expect_call_failure(
            when=backend_name == 'narwhals-lazy',
            reason=('order-dependent window operations raise on narwhals-lazy'),
            errors=((InvalidOperationError,)),
        ):
            result = (
                ma.relation(df)
                .select(ma.col("group"), ma.col("score"), expr.alias("lead_val"))
                .sort("group", "score")
                .to_dict()
            )
            assert result["lead_val"] == [20, 30, None, 25, 35, None]

    def test_lead_n2(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "A"], "score": [10, 20, 30, 40]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").lead(2).over("group")
        with expect_call_failure(
            when=backend_name == 'narwhals-lazy',
            reason=('order-dependent window operations raise on narwhals-lazy'),
            errors=((InvalidOperationError,)),
        ):
            result = (
                ma.relation(df)
                .select(ma.col("group"), ma.col("score"), expr.alias("lead_val"))
                .sort("group", "score")
                .to_dict()
            )
            assert result["lead_val"] == [30, 40, None, None]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowLag:
    """Test lag(n) — previous value in partition."""

    def test_lag_basic(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "B", "B", "B"], "score": [10, 20, 30, 15, 25, 35]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").lag(1).over("group")
        with expect_call_failure(
            when=backend_name == 'narwhals-lazy',
            reason=('order-dependent window operations raise on narwhals-lazy'),
            errors=((InvalidOperationError,)),
        ):
            result = (
                ma.relation(df)
                .select(ma.col("group"), ma.col("score"), expr.alias("lag_val"))
                .sort("group", "score")
                .to_dict()
            )
            assert result["lag_val"] == [None, 10, 20, None, 15, 25]

    def test_lag_n2(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "A"], "score": [10, 20, 30, 40]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").lag(2).over("group")
        with expect_call_failure(
            when=backend_name == 'narwhals-lazy',
            reason=('order-dependent window operations raise on narwhals-lazy'),
            errors=((InvalidOperationError,)),
        ):
            result = (
                ma.relation(df)
                .select(ma.col("group"), ma.col("score"), expr.alias("lag_val"))
                .sort("group", "score")
                .to_dict()
            )
            assert result["lag_val"] == [None, None, 10, 20]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowShift:
    """Test shift(n) — shift values in partition (positive=lag, negative=lead)."""

    def test_shift_forward(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "A", "A"], "score": [10, 20, 30, 40, 50]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").shift(1).over("group")
        with expect_call_failure(
            when=backend_name == 'narwhals-lazy',
            reason=('order-dependent window operations raise on narwhals-lazy'),
            errors=((InvalidOperationError,)),
        ):
            result = (
                ma.relation(df)
                .select(ma.col("group"), ma.col("score"), expr.alias("shifted"))
                .sort("group", "score")
                .to_dict()
            )
            assert result["shifted"] == [None, 10, 20, 30, 40]

    def test_shift_backward(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "A", "A"], "score": [10, 20, 30, 40, 50]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").shift(-1).over("group")
        with expect_call_failure(
            when=backend_name == 'narwhals-lazy',
            reason=('order-dependent window operations raise on narwhals-lazy'),
            errors=((InvalidOperationError,)),
        ):
            result = (
                ma.relation(df)
                .select(ma.col("group"), ma.col("score"), expr.alias("shifted"))
                .sort("group", "score")
                .to_dict()
            )
            assert result["shifted"] == [20, 30, 40, 50, None]

    def test_shift_n2(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "A", "A"], "score": [10, 20, 30, 40, 50]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").shift(2).over("group")
        with expect_call_failure(
            when=backend_name == 'narwhals-lazy',
            reason=('order-dependent window operations raise on narwhals-lazy'),
            errors=((InvalidOperationError,)),
        ):
            result = (
                ma.relation(df)
                .select(ma.col("group"), ma.col("score"), expr.alias("shifted"))
                .sort("group", "score")
                .to_dict()
            )
            assert result["shifted"] == [None, None, 10, 20, 30]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowFirstValue:
    """Test first_value() — first value in partition."""

    def test_first_value_basic(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "B", "B"], "score": [10, 20, 30, 15, 25]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").first_value().over("group")
        with expect_call_failure(
            when=backend_name == 'narwhals-lazy',
            reason=('order-dependent window operations raise on narwhals-lazy'),
            errors=((InvalidOperationError,)),
        ):
            result = (
                ma.relation(df).select(ma.col("group"), ma.col("score"), expr.alias("fv")).sort("group", "score").to_dict()
            )
            assert result["fv"] == [10, 10, 10, 15, 15]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowLastValue:
    """Test last_value() — last value in partition."""

    def test_last_value_basic(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "B", "B"], "score": [10, 20, 30, 15, 25]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").last_value().over("group")
        with expect_call_failure(
            when=backend_name == 'narwhals-lazy',
            reason=('order-dependent window operations raise on narwhals-lazy'),
            errors=((InvalidOperationError,)),
        ):
            result = (
                ma.relation(df).select(ma.col("group"), ma.col("score"), expr.alias("lv")).sort("group", "score").to_dict()
            )
            assert result["lv"] == [30, 30, 30, 25, 25]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowNtile:
    """Test ntile(n) — divide partition into n roughly equal buckets."""

    def test_ntile_2(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "A"], "score": [10, 20, 30, 40]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").ntile(2).over("group")
        with expect_call_failure(
            when=backend_name in ('ibis-duckdb', 'ibis-sqlite') or backend_name in ('narwhals-polars', 'narwhals-pandas', 'narwhals-lazy', 'pandas'),
            reason=(('ntile() is unsupported off Polars' if backend_name in ('ibis-duckdb', 'ibis-sqlite') else 'ntile() is unsupported off Polars')),
            errors=(((SignatureValidationError,) if backend_name in ('ibis-duckdb', 'ibis-sqlite') else (NotImplementedError,))),
        ):
            result = (
                ma.relation(df)
                .select(ma.col("group"), ma.col("score"), expr.alias("bucket"))
                .sort("group", "score")
                .to_dict()
            )
            assert result["bucket"] == [1, 1, 2, 2]

    def test_ntile_3(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "A", "A", "A"], "score": [10, 20, 30, 40, 50, 60]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").ntile(3).over("group")
        with expect_call_failure(
            when=backend_name in ('pandas', 'narwhals-pandas', 'narwhals-polars', 'narwhals-lazy') or backend_name in ('ibis-duckdb', 'ibis-sqlite'),
            reason=('ntile() is unsupported off Polars' if backend_name in ('pandas', 'narwhals-pandas', 'narwhals-polars', 'narwhals-lazy') else ('ntile() is unsupported off Polars' if backend_name in ('ibis-duckdb', 'ibis-sqlite') else 'ntile() is unsupported off Polars')),
            errors=((NotImplementedError,) if backend_name in ('pandas', 'narwhals-pandas', 'narwhals-polars', 'narwhals-lazy') else ((SignatureValidationError,) if backend_name in ('ibis-duckdb', 'ibis-sqlite') else (OperationNotDefinedError,))),
        ):
            result = (
                ma.relation(df)
                .select(ma.col("group"), ma.col("score"), expr.alias("bucket"))
                .sort("group", "score")
                .to_dict()
            )
            assert result["bucket"] == [1, 1, 2, 2, 3, 3]


# ─── Cumulative Operations ─────────────────────────────────────────────────────


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowCumSum:
    """Test cum_sum — cumulative sum."""

    def test_cum_sum_plain(self, backend_name, backend_factory):
        data = {"a": [1, 2, 3, 4, 5]}
        df = backend_factory.create(data, backend_name)
        with expect_call_failure(
            when=backend_name == 'narwhals-lazy',
            reason=('order-dependent window operations raise on narwhals-lazy'),
            errors=((InvalidOperationError,)),
        ):
            result = ma.relation(df).select(ma.col("a"), ma.col("a").cum_sum().alias("cs")).to_dict()
            assert result["cs"] == [1, 3, 6, 10, 15]

    def test_cum_sum_over_partition(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "B", "B"], "val": [1, 2, 3, 10, 20]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").cum_sum().over("group")
        with expect_call_failure(
            when=backend_name == 'narwhals-lazy',
            reason=('order-dependent window operations raise on narwhals-lazy'),
            errors=((InvalidOperationError,)),
        ):
            result = ma.relation(df).select(ma.col("group"), ma.col("val"), expr.alias("cs")).sort("group", "val").to_dict()
            assert result["cs"] == [1, 3, 6, 10, 30]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowCumMax:
    """Test cum_max — cumulative maximum."""

    def test_cum_max_plain(self, backend_name, backend_factory):
        data = {"a": [3, 1, 4, 1, 5]}
        df = backend_factory.create(data, backend_name)
        with expect_call_failure(
            when=backend_name == 'narwhals-lazy',
            reason=('order-dependent window operations raise on narwhals-lazy'),
            errors=((InvalidOperationError,)),
        ):
            result = ma.relation(df).select(ma.col("a"), ma.col("a").cum_max().alias("cm")).to_dict()
            assert result["cm"] == [3, 3, 4, 4, 5]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowCumMin:
    """Test cum_min — cumulative minimum."""

    def test_cum_min_plain(self, backend_name, backend_factory):
        data = {"a": [5, 3, 4, 1, 2]}
        df = backend_factory.create(data, backend_name)
        with expect_call_failure(
            when=backend_name == 'narwhals-lazy',
            reason=('order-dependent window operations raise on narwhals-lazy'),
            errors=((InvalidOperationError,)),
        ):
            result = ma.relation(df).select(ma.col("a"), ma.col("a").cum_min().alias("cm")).to_dict()
            assert result["cm"] == [5, 3, 3, 1, 1]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowCumCount:
    """Test cum_count — cumulative count (non-null values)."""

    def test_cum_count_plain(self, backend_name, backend_factory):
        data = {"a": [10, 20, 30, 40, 50]}
        df = backend_factory.create(data, backend_name)
        with expect_call_failure(
            when=backend_name == 'narwhals-lazy',
            reason=('order-dependent window operations raise on narwhals-lazy'),
            errors=((InvalidOperationError,)),
        ):
            result = ma.relation(df).select(ma.col("a"), ma.col("a").cum_count().alias("cc")).to_dict()
            assert result["cc"] == [1, 2, 3, 4, 5]

    def test_cum_count_with_nulls(self, backend_name, backend_factory):
        data = {"a": [10, None, 30, None, 50]}
        df = backend_factory.create(data, backend_name)
        with expect_call_failure(
            when=backend_name == 'narwhals-lazy',
            reason=('order-dependent window operations raise on narwhals-lazy'),
            errors=((InvalidOperationError,)),
        ):
            result = ma.relation(df).select(ma.col("a"), ma.col("a").cum_count().alias("cc")).to_dict()
            assert result["cc"] == [1, 1, 2, 2, 3]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowCumProd:
    """Test cum_prod — cumulative product."""

    def test_cum_prod_plain(self, backend_name, backend_factory):
        data = {"a": [1, 2, 3, 4]}
        df = backend_factory.create(data, backend_name)
        with expect_call_failure(
            when=backend_name in ('ibis-duckdb', 'ibis-sqlite') or backend_name == 'narwhals-lazy',
            reason=('cum_prod() raises on all Ibis backends' if backend_name in ('ibis-duckdb', 'ibis-sqlite') else 'order-dependent window operations raise on narwhals-lazy'),
            errors=((AttributeError,) if backend_name in ('ibis-duckdb', 'ibis-sqlite') else (InvalidOperationError,)),
        ):
            result = ma.relation(df).select(ma.col("a"), ma.col("a").cum_prod().alias("cp")).to_dict()
            assert result["cp"] == [1, 2, 6, 24]


@pytest.mark.cross_backend
class TestWindowDiff:
    """Test diff — element-wise difference with lag."""

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_diff_basic(self, backend_name, backend_factory):
        data = {"a": [10, 20, 35, 50]}
        df = backend_factory.create(data, backend_name)
        with expect_call_failure(
            when=backend_name == 'narwhals-lazy',
            reason=('order-dependent window operations raise on narwhals-lazy'),
            errors=((InvalidOperationError,)),
        ):
            result = ma.relation(df).select(ma.col("a"), ma.col("a").diff().alias("d")).to_dict()
            assert result["d"] == [None, 10, 15, 15]

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_diff_n2(self, backend_name, backend_factory):
        data = {"a": [10, 20, 30, 40, 50]}
        df = backend_factory.create(data, backend_name)
        with expect_call_failure(
            when=backend_name in ('pandas', 'narwhals-polars', 'narwhals-pandas', 'narwhals-lazy'),
            reason=('percent_rank/cume_dist/nth_value and diff(n>1) raise on pandas/narwhals'),
            errors=((NotImplementedError,)),
        ):
            result = ma.relation(df).select(ma.col("a"), ma.col("a").diff(n=2).alias("d")).to_dict()
            assert result["d"] == [None, None, 20, 20, 20]


# ─── Rank Variants ────────────────────────────────────────────────────────────


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowRankDescending:
    """Test rank(descending=True) produces reversed ordering."""

    def test_rank_descending_differs_from_ascending(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "A"], "score": [10, 20, 30, 30], "id": [1, 2, 3, 4]}
        df = backend_factory.create(data, backend_name)
        expr_asc = ma.col("score").rank(method="min").over("group")
        expr_desc = ma.col("score").rank(method="min", descending=True).over("group")
        result_asc = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), ma.col("id"), expr_asc.alias("rnk"))
            .sort("group", "score", "id")
            .to_dict()
        )
        result_desc = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), ma.col("id"), expr_desc.alias("rnk"))
            .sort("group", "score", "id")
            .to_dict()
        )
        assert result_asc["rnk"] != result_desc["rnk"]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowRankMethodDense:
    """Test rank(method='dense') — consecutive ranks, no gaps on ties."""

    def test_rank_method_dense(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "A"], "score": [10, 20, 30, 30], "id": [1, 2, 3, 4]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").rank(method="dense").over("group")
        with expect_call_failure(
            when=backend_name in ('ibis-duckdb', 'ibis-sqlite', 'narwhals-polars', 'narwhals-pandas', 'narwhals-lazy', 'pandas'),
            reason="rank(method='dense'|'ordinal') raises off Polars",
            errors=(TypeError,),
        ):
            result = (
                ma.relation(df)
                .select(ma.col("group"), ma.col("score"), ma.col("id"), expr.alias("drnk"))
                .sort("group", "score", "id")
                .to_dict()
            )
            assert result["drnk"] == [1, 2, 3, 3]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowRankMethodOrdinal:
    """Test rank(method='ordinal') — unique sequential ranks."""

    def test_rank_method_ordinal(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "A"], "score": [10, 20, 30, 30], "id": [1, 2, 3, 4]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").rank(method="ordinal").over("group")
        with expect_call_failure(
            when=backend_name in ('ibis-duckdb', 'ibis-sqlite', 'narwhals-polars', 'narwhals-pandas', 'narwhals-lazy', 'pandas'),
            reason="rank(method='dense'|'ordinal') raises off Polars",
            errors=(TypeError,),
        ):
            result = (
                ma.relation(df)
                .select(ma.col("group"), ma.col("score"), ma.col("id"), expr.alias("rn"))
                .sort("group", "score", "id")
                .to_dict()
            )
            assert result["rn"] == [1, 2, 3, 4]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowRankMethodAverage:
    """Test rank(method='average') — averaged ranks for ties (no SQL equivalent)."""

    def test_rank_method_average(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "A"], "score": [10, 20, 30, 30], "id": [1, 2, 3, 4]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").rank(method="average").over("group")
        with expect_call_failure(
            when=backend_name in ('ibis-duckdb', 'ibis-sqlite'),
            reason="rank(method='average'|'max') raises on Ibis",
            errors=(BackendCapabilityError,),
        ):
            result = (
                ma.relation(df)
                .select(ma.col("group"), ma.col("score"), ma.col("id"), expr.alias("rnk"))
                .sort("group", "score", "id")
                .to_dict()
            )
            assert result["rnk"] == [1.0, 2.0, 3.5, 3.5]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowRankMethodMax:
    """Test rank(method='max') — max rank for ties (no SQL equivalent)."""

    def test_rank_method_max(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "A"], "score": [10, 20, 30, 30], "id": [1, 2, 3, 4]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").rank(method="max").over("group")
        with expect_call_failure(
            when=backend_name in ('ibis-duckdb', 'ibis-sqlite'),
            reason="rank(method='average'|'max') raises on Ibis",
            errors=(BackendCapabilityError,),
        ):
            result = (
                ma.relation(df)
                .select(ma.col("group"), ma.col("score"), ma.col("id"), expr.alias("rnk"))
                .sort("group", "score", "id")
                .to_dict()
            )
            assert result["rnk"] == [1, 2, 4, 4]


# retirement-verdict: SP2-B (crosswalk Part F ground-truth, rank method=average/max) —
# TestWindowRankMethodGuard retired: its two pytest.raises(BackendCapabilityError)
# assertions duplicated the IB-WIN-05 divergence. Sole surviving catcher of the
# rank(method=average|max) ibis gap is the xfail'd TestWindowRankMethodAverage/Max[ibis]
# cases, whose exact observer bindings remain load-bearing. The native error is
# unenriched, so this remains a manifestation rather than a dispatch gate.


# ─── Percent Rank & Cume Dist ─────────────────────────────────────────────────


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowPercentRank:
    """Test percent_rank() — values between 0 and 1."""

    def test_percent_rank_basic(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "B", "B", "B"], "score": [10, 20, 20, 30, 10, 20]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").percent_rank().over("group", order_by="score")
        with expect_call_failure(
            when=backend_name in ('pandas', 'narwhals-polars', 'narwhals-pandas', 'narwhals-lazy'),
            reason=('percent_rank/cume_dist/nth_value and diff(n>1) raise on pandas/narwhals'),
            errors=((NotImplementedError,)),
        ):
            result = (
                ma.relation(df)
                .select(ma.col("group"), ma.col("score"), expr.alias("prnk"))
                .sort("group", "score")
                .to_dict()
            )
            for val in result["prnk"]:
                assert 0.0 <= val <= 1.0


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowCumeDist:
    """Test cume_dist() — cumulative distribution, values between 0 and 1."""

    def test_cume_dist_basic(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "B", "B", "B"], "score": [10, 20, 20, 30, 10, 20]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").cume_dist().over("group", order_by="score")
        with expect_call_failure(
            when=backend_name in ('pandas', 'narwhals-polars', 'narwhals-pandas', 'narwhals-lazy'),
            reason=('percent_rank/cume_dist/nth_value and diff(n>1) raise on pandas/narwhals'),
            errors=((NotImplementedError,)),
        ):
            result = (
                ma.relation(df)
                .select(ma.col("group"), ma.col("score"), expr.alias("cdist"))
                .sort("group", "score")
                .to_dict()
            )
            for val in result["cdist"]:
                assert 0.0 <= val <= 1.0


# ─── Nth Value ────────────────────────────────────────────────────────────────


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowNthValue:
    """Test nth_value(n) — nth value in partition."""

    def test_nth_value_basic(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A"], "score": [10, 20, 30]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").nth_value(2).over("group")
        with expect_call_failure(
            when=backend_name in ('pandas', 'narwhals-polars', 'narwhals-pandas', 'narwhals-lazy') or backend_name in ('polars', 'polars-lazy'),
            reason=(('percent_rank/cume_dist/nth_value and diff(n>1) raise on pandas/narwhals' if backend_name in ('pandas', 'narwhals-polars', 'narwhals-pandas', 'narwhals-lazy') else 'nth_value().over() raises on eager and lazy Polars')),
            errors=(((NotImplementedError,) if backend_name in ('pandas', 'narwhals-polars', 'narwhals-pandas', 'narwhals-lazy') else (ShapeError,))),
        ):
            result = (
                ma.relation(df).select(ma.col("group"), ma.col("score"), expr.alias("nth")).sort("group", "score").to_dict()
            )
            assert all(v == 20 for v in result["nth"])


# ─── Over Modifier Variants ──────────────────────────────────────────────────


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowOverScalar:
    """Test .over() wrapping a non-window expression (scalar windowed)."""

    def test_over_scalar_expression(self, backend_name, backend_factory):
        data = {"dept": ["eng", "eng", "sales", "sales"], "salary": [100, 120, 80, 110]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("salary").add(ma.lit(0)).over("dept")
        with expect_call_failure(
            when=backend_name in ('ibis-duckdb', 'ibis-sqlite') or backend_name in ('narwhals-polars', 'narwhals-pandas', 'narwhals-lazy', 'pandas'),
            reason=('scalar_expr.over(...) raises off Polars' if backend_name in ('ibis-duckdb', 'ibis-sqlite') else 'scalar_expr.over(...) raises off Polars'),
            errors=((IbisTypeError,) if backend_name in ('ibis-duckdb', 'ibis-sqlite') else (InvalidOperationError,)),
        ):
            result = (
                ma.relation(df)
                .select(ma.col("dept"), ma.col("salary"), expr.alias("windowed"))
                .sort("dept", "salary")
                .to_dict()
            )
            assert len(result["windowed"]) == 4


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowMultiPartition:
    """Test .over() with multiple partition columns."""

    def test_rank_multi_partition(self, backend_name, backend_factory):
        data = {
            "dept": ["eng", "eng", "eng", "sales", "sales"],
            "level": ["jr", "sr", "jr", "jr", "sr"],
            "salary": [100, 120, 90, 80, 110],
        }
        df = backend_factory.create(data, backend_name)
        expr = ma.col("salary").rank(method="min").over("dept", "level")
        result = (
            ma.relation(df)
            .select(
                ma.col("dept"),
                ma.col("level"),
                ma.col("salary"),
                expr.alias("rnk"),
            )
            .sort("dept", "level", "salary")
            .to_dict()
        )
        # eng/jr: 90,100 -> 1,2; eng/sr: 120 -> 1; sales/jr: 80 -> 1; sales/sr: 110 -> 1
        assert result["rnk"] == [1, 2, 1, 1, 1]


_NARWHALS_FAMILY = ("pandas", "narwhals-polars", "narwhals-pandas", "narwhals-lazy")
_NW_364 = (
    "backlog 364: Narwhals ranks on the first key and ignores descending; "
    "declared refusal pending"
)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWindowMultiKeyOrder:
    """.over(order_by=[...]) orders ranking functions by every key (backlog 364)."""

    DATA = {"g": [1, 1, 1, 1], "a": [1, 1, 2, 2], "b": [2, 1, 2, 1]}

    @pytest.mark.parametrize(
        ("fn", "order_by", "expected"),
        [
            # rows sorted by (a, b): (1,1), (1,2), (2,1), (2,2)
            ("row_number", ["a", "b"], [1, 2, 3, 4]),
            ("row_number", ["a", "-b"], [2, 1, 4, 3]),
            ("row_number", ["b", "a"], [1, 3, 2, 4]),
            ("dense_rank", ["a", "b"], [1, 2, 3, 4]),
            ("dense_rank", ["a", "-b"], [2, 1, 4, 3]),
            ("rank", ["a", "b"], [1, 2, 3, 4]),
        ],
    )
    def test_all_keys_ordered(self, backend_name, backend_factory, fn, order_by, expected):
        kwargs = {"method": "min"} if fn == "rank" else {}
        expr = getattr(ma.col("a"), fn)(**kwargs).over("g", order_by=order_by)
        df = backend_factory.create(self.DATA, backend_name)
        # Narwhals row_number follows the .over() frame order for ascending keys;
        # tie-aware ranks and any descending key use only the first key.
        with expect_call_failure(
            when=backend_name in _NARWHALS_FAMILY
            and (fn != "row_number" or any(k.startswith("-") for k in order_by)),
            reason=_NW_364,
            errors=(AssertionError,),
        ):
            out = ma.relation(df).with_columns(expr.alias("r")).sort("a", "b").to_dict()
            assert out["r"] == expected

    def test_single_descending_key(self, backend_name, backend_factory):
        expr = ma.col("a").row_number().over("g", order_by="-b")
        df = backend_factory.create(self.DATA, backend_name)
        out = ma.relation(df).with_columns(expr.alias("r")).sort("b", "a").to_dict()
        # b descending: the two b=2 rows take 1-2, the two b=1 rows take 3-4
        assert sorted(out["r"][:2]) == [3, 4]
        assert sorted(out["r"][2:]) == [1, 2]

    def test_row_number_null_key_completes(self, backend_name, backend_factory):
        df = backend_factory.create({"g": [1, 1, 1], "a": [2, None, 1], "b": [1, 2, 3]}, backend_name)
        expr = ma.col("a").row_number().over("g", order_by=["a", "b"])
        # Narwhals ranks the first key alone, and a null key ranks as null.
        with expect_call_failure(
            when=backend_name in _NARWHALS_FAMILY,
            reason=_NW_364,
            errors=(AssertionError,),
        ):
            out = ma.relation(df).with_columns(expr.alias("r")).to_dict()
            assert None not in out["r"]
            assert sorted(out["r"]) == [1, 2, 3]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("fn", ["row_number", "dense_rank"])
def test_integral_rank_dtype(backend_name, backend_factory, fn):
    """Integral ranking functions return integers (backlog 367)."""
    df = backend_factory.create({"g": [1, 1], "a": [2, 1]}, backend_name)
    expr = getattr(ma.col("a"), fn)().over("g")
    with expect_call_failure(
        when=backend_name in ("pandas", "narwhals-pandas"),
        reason="backlog 367: pandas NumPy rank returns float64 (declared divergence)",
        errors=(AssertionError,),
    ):
        values = ma.relation(df).with_columns(expr.alias("r")).to_dict()["r"]
        assert all(type(v) is int for v in values)


class TestWindowRequiresOver:
    """Window functions that don't pre-populate window_spec must have .over()."""

    def test_percent_rank_without_over_raises(self):
        import polars as pl

        df = pl.DataFrame({"salary": [100, 120, 90]})
        expr = ma.col("salary").percent_rank()
        with pytest.raises(ValueError, match=r"\.over\(\)"):
            expr.compile(df)
