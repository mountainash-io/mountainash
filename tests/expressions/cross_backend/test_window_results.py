"""Cross-backend result verification for window operations.

Verifies that window expressions produce identical results across all 9
backends. Window functions require .over() context for partitioned operations.

Test data uses unique sort keys to ensure deterministic output ordering.

Known divergences (declaration-driven via DivergenceFact + xfail_divergence):
- ibis-polars: no translation rule for any WindowFunction (IB-WIN-01)
- ibis-duckdb/ibis-sqlite: rank/dense_rank/row_number are 0-based (IB-WIN-02)
- ibis: rank(method='average'/'max') has no SQL equivalent (IB-WIN-03)
- ibis: cum_prod unsupported (IB-WIN-04)
- ibis/narwhals/pandas: rank(method='dense'/'ordinal') via method param (MA-WIN-01),
  ntile (MA-WIN-02), .over() on elementwise expressions (MA-WIN-03)
- narwhals/pandas: percent_rank/cume_dist/nth_value/diff(n>1) (NW-WIN-02)
- narwhals-lazy: order-dependent window ops on a LazyFrame (NW-WIN-01)
"""

from __future__ import annotations

import pytest

import mountainash as ma
from fixtures.backend_registry import ALL_BACKENDS
from fixtures.capability_gating import xfail_divergence


def _win(*divergence_ids):
    """Backend params carrying the given divergence marks; xfail_divergence is a
    no-op when a divergence does not apply, so each backend self-selects."""
    return [
        pytest.param(b, marks=[xfail_divergence(i, backend=b) for i in divergence_ids])
        for b in ALL_BACKENDS
    ]


_RANK_FAMILY = _win("IB-WIN-01", "IB-WIN-02")   # ibis-polars native; ibis-duckdb/sqlite 0-based
_RANK_DESC = _win("IB-WIN-01")                    # ibis-polars native; sql 0-based still differs asc/desc
_LEAD_LAG = _win("IB-WIN-01", "NW-WIN-01")        # ibis-polars native; narwhals-lazy order-dependent
_CUM = _win("IB-WIN-01", "NW-WIN-01")
_CUM_PROD = _win("IB-WIN-04", "NW-WIN-01")        # cum_prod unsupported on ALL ibis
_DIFF = _win("IB-WIN-01", "NW-WIN-01")
_DIFF_N = _win("IB-WIN-01", "NW-WIN-02")          # narwhals: diff(n>1) unsupported
_RANK_METHOD = _win("MA-WIN-01")                  # rank(method=dense/ordinal): polars only
_RANK_AVG_MAX = _win("IB-WIN-03")                 # ibis no SQL equiv; narwhals now runs
_NTILE = _win("MA-WIN-02")
_PCT_CUME = _win("IB-WIN-01", "NW-WIN-02")        # ibis-polars native; narwhals unsupported; ibis sql runs
_NTH = _win("IB-WIN-01", "NW-WIN-02", "PL-WIN-01")
_OVER_SCALAR = _win("MA-WIN-03")


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _RANK_FAMILY)
class TestWindowRank:
    """Test rank(method='min') — equivalent to SQL RANK()."""

    def test_rank_basic(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "B", "B"],
                "score": [10, 30, 20, 15, 25]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").rank(method="min").over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), expr.alias("rnk"))
            .sort("group", "score")
            .to_dict()
        )
        # A: scores [10,20,30] -> ranks [1,2,3]; B: scores [15,25] -> ranks [1,2]
        assert result["rnk"] == [1, 2, 3, 1, 2]

    def test_rank_with_ties(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "A"],
                "score": [10, 20, 20, 30],
                "id": [1, 2, 3, 4]}
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
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), expr.alias("rnk"))
            .to_dict()
        )
        assert result["rnk"] == [1]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _RANK_FAMILY)
class TestWindowDenseRank:
    """Test dense_rank() — equivalent to SQL DENSE_RANK()."""

    def test_dense_rank_basic(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "B", "B"],
                "score": [10, 30, 20, 15, 25]}
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
        data = {"group": ["A", "A", "A", "A"],
                "score": [10, 20, 20, 30],
                "id": [1, 2, 3, 4]}
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
@pytest.mark.parametrize("backend_name", _RANK_FAMILY)
class TestWindowRowNumber:
    """Test row_number() — equivalent to SQL ROW_NUMBER()."""

    def test_row_number_basic(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "B", "B"],
                "score": [10, 30, 20, 15, 25]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").row_number().over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), expr.alias("rn"))
            .sort("group", "score")
            .to_dict()
        )
        assert result["rn"] == [1, 2, 3, 1, 2]

    def test_row_number_single_partition(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A"],
                "score": [30, 10, 20]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").row_number().over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), expr.alias("rn"))
            .sort("group", "score")
            .to_dict()
        )
        assert result["rn"] == [1, 2, 3]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _LEAD_LAG)
class TestWindowLead:
    """Test lead(n) — next value in partition."""

    def test_lead_basic(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "B", "B", "B"],
                "score": [10, 20, 30, 15, 25, 35]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").lead(1).over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), expr.alias("lead_val"))
            .sort("group", "score")
            .to_dict()
        )
        assert result["lead_val"] == [20, 30, None, 25, 35, None]

    def test_lead_n2(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "A"],
                "score": [10, 20, 30, 40]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").lead(2).over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), expr.alias("lead_val"))
            .sort("group", "score")
            .to_dict()
        )
        assert result["lead_val"] == [30, 40, None, None]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _LEAD_LAG)
class TestWindowLag:
    """Test lag(n) — previous value in partition."""

    def test_lag_basic(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "B", "B", "B"],
                "score": [10, 20, 30, 15, 25, 35]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").lag(1).over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), expr.alias("lag_val"))
            .sort("group", "score")
            .to_dict()
        )
        assert result["lag_val"] == [None, 10, 20, None, 15, 25]

    def test_lag_n2(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "A"],
                "score": [10, 20, 30, 40]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").lag(2).over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), expr.alias("lag_val"))
            .sort("group", "score")
            .to_dict()
        )
        assert result["lag_val"] == [None, None, 10, 20]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _LEAD_LAG)
class TestWindowShift:
    """Test shift(n) — shift values in partition (positive=lag, negative=lead)."""

    def test_shift_forward(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "A", "A"],
                "score": [10, 20, 30, 40, 50]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").shift(1).over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), expr.alias("shifted"))
            .sort("group", "score")
            .to_dict()
        )
        assert result["shifted"] == [None, 10, 20, 30, 40]

    def test_shift_backward(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "A", "A"],
                "score": [10, 20, 30, 40, 50]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").shift(-1).over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), expr.alias("shifted"))
            .sort("group", "score")
            .to_dict()
        )
        assert result["shifted"] == [20, 30, 40, 50, None]

    def test_shift_n2(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "A", "A"],
                "score": [10, 20, 30, 40, 50]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").shift(2).over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), expr.alias("shifted"))
            .sort("group", "score")
            .to_dict()
        )
        assert result["shifted"] == [None, None, 10, 20, 30]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _LEAD_LAG)
class TestWindowFirstValue:
    """Test first_value() — first value in partition."""

    def test_first_value_basic(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "B", "B"],
                "score": [10, 20, 30, 15, 25]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").first_value().over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), expr.alias("fv"))
            .sort("group", "score")
            .to_dict()
        )
        assert result["fv"] == [10, 10, 10, 15, 15]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _LEAD_LAG)
class TestWindowLastValue:
    """Test last_value() — last value in partition."""

    def test_last_value_basic(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "B", "B"],
                "score": [10, 20, 30, 15, 25]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").last_value().over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), expr.alias("lv"))
            .sort("group", "score")
            .to_dict()
        )
        assert result["lv"] == [30, 30, 30, 25, 25]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _NTILE)
class TestWindowNtile:
    """Test ntile(n) — divide partition into n roughly equal buckets."""

    def test_ntile_2(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "A"],
                "score": [10, 20, 30, 40]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").ntile(2).over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), expr.alias("bucket"))
            .sort("group", "score")
            .to_dict()
        )
        assert result["bucket"] == [1, 1, 2, 2]

    def test_ntile_3(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "A", "A", "A"],
                "score": [10, 20, 30, 40, 50, 60]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").ntile(3).over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), expr.alias("bucket"))
            .sort("group", "score")
            .to_dict()
        )
        assert result["bucket"] == [1, 1, 2, 2, 3, 3]


# ─── Cumulative Operations ─────────────────────────────────────────────────────


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _CUM)
class TestWindowCumSum:
    """Test cum_sum — cumulative sum."""

    def test_cum_sum_plain(self, backend_name, backend_factory):
        data = {"a": [1, 2, 3, 4, 5]}
        df = backend_factory.create(data, backend_name)
        result = (
            ma.relation(df)
            .select(ma.col("a"), ma.col("a").cum_sum().alias("cs"))
            .to_dict()
        )
        assert result["cs"] == [1, 3, 6, 10, 15]

    def test_cum_sum_over_partition(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "B", "B"],
                "val": [1, 2, 3, 10, 20]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").cum_sum().over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("val"), expr.alias("cs"))
            .sort("group", "val")
            .to_dict()
        )
        assert result["cs"] == [1, 3, 6, 10, 30]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _CUM)
class TestWindowCumMax:
    """Test cum_max — cumulative maximum."""

    def test_cum_max_plain(self, backend_name, backend_factory):
        data = {"a": [3, 1, 4, 1, 5]}
        df = backend_factory.create(data, backend_name)
        result = (
            ma.relation(df)
            .select(ma.col("a"), ma.col("a").cum_max().alias("cm"))
            .to_dict()
        )
        assert result["cm"] == [3, 3, 4, 4, 5]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _CUM)
class TestWindowCumMin:
    """Test cum_min — cumulative minimum."""

    def test_cum_min_plain(self, backend_name, backend_factory):
        data = {"a": [5, 3, 4, 1, 2]}
        df = backend_factory.create(data, backend_name)
        result = (
            ma.relation(df)
            .select(ma.col("a"), ma.col("a").cum_min().alias("cm"))
            .to_dict()
        )
        assert result["cm"] == [5, 3, 3, 1, 1]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _CUM)
class TestWindowCumCount:
    """Test cum_count — cumulative count (non-null values)."""

    def test_cum_count_plain(self, backend_name, backend_factory):
        data = {"a": [10, 20, 30, 40, 50]}
        df = backend_factory.create(data, backend_name)
        result = (
            ma.relation(df)
            .select(ma.col("a"), ma.col("a").cum_count().alias("cc"))
            .to_dict()
        )
        assert result["cc"] == [1, 2, 3, 4, 5]

    def test_cum_count_with_nulls(self, backend_name, backend_factory):
        data = {"a": [10, None, 30, None, 50]}
        df = backend_factory.create(data, backend_name)
        result = (
            ma.relation(df)
            .select(ma.col("a"), ma.col("a").cum_count().alias("cc"))
            .to_dict()
        )
        assert result["cc"] == [1, 1, 2, 2, 3]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _CUM_PROD)
class TestWindowCumProd:
    """Test cum_prod — cumulative product."""

    def test_cum_prod_plain(self, backend_name, backend_factory):
        data = {"a": [1, 2, 3, 4]}
        df = backend_factory.create(data, backend_name)
        result = (
            ma.relation(df)
            .select(ma.col("a"), ma.col("a").cum_prod().alias("cp"))
            .to_dict()
        )
        assert result["cp"] == [1, 2, 6, 24]


@pytest.mark.cross_backend
class TestWindowDiff:
    """Test diff — element-wise difference with lag."""

    @pytest.mark.parametrize("backend_name", _DIFF)
    def test_diff_basic(self, backend_name, backend_factory):
        data = {"a": [10, 20, 35, 50]}
        df = backend_factory.create(data, backend_name)
        result = (
            ma.relation(df)
            .select(ma.col("a"), ma.col("a").diff().alias("d"))
            .to_dict()
        )
        assert result["d"] == [None, 10, 15, 15]

    @pytest.mark.parametrize("backend_name", _DIFF_N)
    def test_diff_n2(self, backend_name, backend_factory):
        data = {"a": [10, 20, 30, 40, 50]}
        df = backend_factory.create(data, backend_name)
        result = (
            ma.relation(df)
            .select(ma.col("a"), ma.col("a").diff(n=2).alias("d"))
            .to_dict()
        )
        assert result["d"] == [None, None, 20, 20, 20]


# ─── Rank Variants ────────────────────────────────────────────────────────────


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _RANK_DESC)
class TestWindowRankDescending:
    """Test rank(descending=True) produces reversed ordering."""

    def test_rank_descending_differs_from_ascending(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "A"],
                "score": [10, 20, 30, 30],
                "id": [1, 2, 3, 4]}
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
@pytest.mark.parametrize("backend_name", _RANK_METHOD)
class TestWindowRankMethodDense:
    """Test rank(method='dense') — consecutive ranks, no gaps on ties."""

    def test_rank_method_dense(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "A"],
                "score": [10, 20, 30, 30],
                "id": [1, 2, 3, 4]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").rank(method="dense").over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), ma.col("id"), expr.alias("drnk"))
            .sort("group", "score", "id")
            .to_dict()
        )
        assert result["drnk"] == [1, 2, 3, 3]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _RANK_METHOD)
class TestWindowRankMethodOrdinal:
    """Test rank(method='ordinal') — unique sequential ranks."""

    def test_rank_method_ordinal(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "A"],
                "score": [10, 20, 30, 30],
                "id": [1, 2, 3, 4]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").rank(method="ordinal").over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), ma.col("id"), expr.alias("rn"))
            .sort("group", "score", "id")
            .to_dict()
        )
        assert result["rn"] == [1, 2, 3, 4]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _RANK_AVG_MAX)
class TestWindowRankMethodAverage:
    """Test rank(method='average') — averaged ranks for ties (no SQL equivalent)."""

    def test_rank_method_average(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "A"],
                "score": [10, 20, 30, 30],
                "id": [1, 2, 3, 4]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").rank(method="average").over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), ma.col("id"), expr.alias("rnk"))
            .sort("group", "score", "id")
            .to_dict()
        )
        assert result["rnk"] == [1.0, 2.0, 3.5, 3.5]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _RANK_AVG_MAX)
class TestWindowRankMethodMax:
    """Test rank(method='max') — max rank for ties (no SQL equivalent)."""

    def test_rank_method_max(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "A"],
                "score": [10, 20, 30, 30],
                "id": [1, 2, 3, 4]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").rank(method="max").over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), ma.col("id"), expr.alias("rnk"))
            .sort("group", "score", "id")
            .to_dict()
        )
        assert result["rnk"] == [1, 2, 4, 4]


# TestWindowRankMethodGuard retired (SP2-B): its two pytest.raises(BackendCapabilityError)
# assertions duplicated the IB-WIN-03 divergence, which the xfail'd
# TestWindowRankMethodAverage/Max[ibis] cases now document and the IB-WIN-03 mutation
# probe verifies as load-bearing. The bare BCE is unenriched (.limitation is None), so it
# is a DivergenceFact, not an assert_capability_gated gate.


# ─── Percent Rank & Cume Dist ─────────────────────────────────────────────────


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _PCT_CUME)
class TestWindowPercentRank:
    """Test percent_rank() — values between 0 and 1."""

    def test_percent_rank_basic(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "B", "B", "B"],
                "score": [10, 20, 20, 30, 10, 20]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").percent_rank().over("group", order_by="score")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), expr.alias("prnk"))
            .sort("group", "score")
            .to_dict()
        )
        for val in result["prnk"]:
            assert 0.0 <= val <= 1.0


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _PCT_CUME)
class TestWindowCumeDist:
    """Test cume_dist() — cumulative distribution, values between 0 and 1."""

    def test_cume_dist_basic(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A", "B", "B", "B"],
                "score": [10, 20, 20, 30, 10, 20]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").cume_dist().over("group", order_by="score")
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
@pytest.mark.parametrize("backend_name", _NTH)
class TestWindowNthValue:
    """Test nth_value(n) — nth value in partition."""

    def test_nth_value_basic(self, backend_name, backend_factory):
        data = {"group": ["A", "A", "A"],
                "score": [10, 20, 30]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("score").nth_value(2).over("group")
        result = (
            ma.relation(df)
            .select(ma.col("group"), ma.col("score"), expr.alias("nth"))
            .sort("group", "score")
            .to_dict()
        )
        assert all(v == 20 for v in result["nth"])


# ─── Over Modifier Variants ──────────────────────────────────────────────────


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _OVER_SCALAR)
class TestWindowOverScalar:
    """Test .over() wrapping a non-window expression (scalar windowed)."""

    def test_over_scalar_expression(self, backend_name, backend_factory):
        data = {"dept": ["eng", "eng", "sales", "sales"],
                "salary": [100, 120, 80, 110]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("salary").add(ma.lit(0)).over("dept")
        result = (
            ma.relation(df)
            .select(ma.col("dept"), ma.col("salary"), expr.alias("windowed"))
            .sort("dept", "salary")
            .to_dict()
        )
        assert len(result["windowed"]) == 4


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _RANK_FAMILY)
class TestWindowMultiPartition:
    """Test .over() with multiple partition columns."""

    def test_rank_multi_partition(self, backend_name, backend_factory):
        data = {"dept": ["eng", "eng", "eng", "sales", "sales"],
                "level": ["jr", "sr", "jr", "jr", "sr"],
                "salary": [100, 120, 90, 80, 110]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("salary").rank(method="min").over("dept", "level")
        result = (
            ma.relation(df)
            .select(
                ma.col("dept"), ma.col("level"), ma.col("salary"),
                expr.alias("rnk"),
            )
            .sort("dept", "level", "salary")
            .to_dict()
        )
        assert len(result["rnk"]) == 5
        assert all(r >= 1 for r in result["rnk"])


class TestWindowRequiresOver:
    """Window functions that don't pre-populate window_spec must have .over()."""

    def test_percent_rank_without_over_raises(self):
        import polars as pl
        df = pl.DataFrame({"salary": [100, 120, 90]})
        expr = ma.col("salary").percent_rank()
        with pytest.raises(ValueError, match=r"\.over\(\)"):
            expr.compile(df)
