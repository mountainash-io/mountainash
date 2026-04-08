"""Cross-backend tests for the 9 fluent aggregate reducers."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.relations import relation


@pytest.fixture
def df() -> pl.DataFrame:
    return pl.DataFrame({
        "g": ["a", "a", "a", "b", "b"],
        "x": [1, 2, 3, 4, 6],
    })


def _agg_via_polars(df, expr_factory):
    return (
        relation(df)
        .group_by("g")
        .agg(expr_factory(ma.col("x")).alias("v"))
        .to_polars()
        .sort("g")
    )


def test_sum(df):
    result = _agg_via_polars(df, lambda c: c.sum())
    assert result["v"].to_list() == [6, 10]


def test_avg(df):
    result = _agg_via_polars(df, lambda c: c.avg())
    assert result["v"].to_list() == [2.0, 5.0]


def test_min(df):
    result = _agg_via_polars(df, lambda c: c.min())
    assert result["v"].to_list() == [1, 4]


def test_max(df):
    result = _agg_via_polars(df, lambda c: c.max())
    assert result["v"].to_list() == [3, 6]


def test_product(df):
    result = _agg_via_polars(df, lambda c: c.product())
    assert result["v"].to_list() == [6, 24]


def test_std_dev(df):
    result = _agg_via_polars(df, lambda c: c.std_dev())
    # group a: [1,2,3] sample std_dev == 1.0; group b: [4,6] == sqrt(2) ≈ 1.414
    assert result["v"].to_list()[0] == pytest.approx(1.0)
    assert result["v"].to_list()[1] == pytest.approx(1.4142135623730951)


def test_variance(df):
    result = _agg_via_polars(df, lambda c: c.variance())
    # group a: var=1.0; group b: var=2.0
    assert result["v"].to_list()[0] == pytest.approx(1.0)
    assert result["v"].to_list()[1] == pytest.approx(2.0)


def test_mode(df):
    # mode is not deterministic on uniform groups; use a group with a clear mode
    df2 = pl.DataFrame({"g": ["a", "a", "a", "b"], "x": [1, 1, 2, 5]})
    result = (
        relation(df2)
        .group_by("g")
        .agg(ma.col("x").mode().alias("v"))
        .to_polars()
        .sort("g")
    )
    # mode of [1,1,2] = 1; mode of [5] = 5
    # Some backends return a list, some a scalar — check membership
    a_val = result.filter(pl.col("g") == "a")["v"].to_list()[0]
    b_val = result.filter(pl.col("g") == "b")["v"].to_list()[0]
    if isinstance(a_val, list):
        assert 1 in a_val
        assert 5 in b_val
    else:
        assert a_val == 1
        assert b_val == 5


def test_any_value(df):
    result = _agg_via_polars(df, lambda c: c.any_value())
    # Nondeterministic representative — just verify it's in the source set
    a_val = result.filter(pl.col("g") == "a")["v"].to_list()[0]
    b_val = result.filter(pl.col("g") == "b")["v"].to_list()[0]
    assert a_val in {1, 2, 3}
    assert b_val in {4, 6}


def test_mean_alias_for_avg(df):
    """ma.col('x').mean() is a short alias for .avg() — same numeric result."""
    avg_result = _agg_via_polars(df, lambda c: c.avg())
    mean_result = _agg_via_polars(df, lambda c: c.mean())
    assert avg_result["v"].to_list() == mean_result["v"].to_list()


# Cross-backend smoke tests for sum (representative of the wiring path)

def test_sum_narwhals():
    pytest.importorskip("narwhals")
    import narwhals as nw
    nw_df = nw.from_native(
        pl.DataFrame({"g": ["a", "b", "b"], "x": [1, 2, 3]}),
        eager_only=True,
    )
    result = (
        relation(nw_df)
        .group_by("g")
        .agg(ma.col("x").sum().alias("v"))
        .to_polars()
        .sort("g")
    )
    assert result["v"].to_list() == [1, 5]


def test_sum_ibis():
    pytest.importorskip("ibis")
    import ibis
    t = ibis.memtable({"g": ["a", "b", "b"], "x": [1, 2, 3]})
    result = (
        relation(t)
        .group_by("g")
        .agg(ma.col("x").sum().alias("v"))
        .to_polars()
        .sort("g")
    )
    assert result["v"].to_list() == [1, 5]
