"""Cross-backend tests for Relation.<agg>(col) scalar terminal methods."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.relations import relation


@pytest.fixture
def df() -> pl.DataFrame:
    return pl.DataFrame({"x": [1, 2, 3, 4, 6]})


def test_sum(df):
    assert relation(df).sum("x") == 16


def test_avg(df):
    assert relation(df).avg("x") == pytest.approx(3.2)


def test_mean_alias(df):
    assert relation(df).mean("x") == relation(df).avg("x")


def test_min(df):
    assert relation(df).min("x") == 1


def test_max(df):
    assert relation(df).max("x") == 6


def test_product(df):
    assert relation(df).product("x") == 144


def test_std_dev():
    df = pl.DataFrame({"x": [1.0, 2.0, 3.0]})
    assert relation(df).std_dev("x") == pytest.approx(1.0)


def test_variance():
    df = pl.DataFrame({"x": [1.0, 2.0, 3.0]})
    assert relation(df).variance("x") == pytest.approx(1.0)


def test_any_value(df):
    val = relation(df).any_value("x")
    assert val in {1, 2, 3, 4, 6}


# Cross-backend smoke for sum

def test_sum_narwhals():
    pytest.importorskip("narwhals")
    import narwhals as nw
    nw_df = nw.from_native(pl.DataFrame({"x": [1, 2, 3]}), eager_only=True)
    assert relation(nw_df).sum("x") == 6


def test_sum_ibis():
    pytest.importorskip("ibis")
    import ibis
    t = ibis.memtable({"x": [1, 2, 3]})
    assert relation(t).sum("x") == 6


# After filter

def test_sum_after_filter(df):
    rel = relation(df).filter(ma.col("x").gt(ma.lit(2)))
    assert rel.sum("x") == 13  # 3+4+6
