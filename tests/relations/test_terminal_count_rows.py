"""Cross-backend tests for Relation.count_rows() terminal."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.relations import relation


@pytest.fixture
def df() -> pl.DataFrame:
    return pl.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "amount": [10, 20, 30, 40, 50],
        "status": ["a", "b", "a", "b", "a"],
    })


def test_count_rows_basic(df):
    assert relation(df).count_rows() == 5


def test_count_rows_after_head(df):
    assert relation(df).head(2).count_rows() == 2


def test_count_rows_after_filter_match(df):
    rel = relation(df).filter(ma.col("status").eq(ma.lit("a")))
    assert rel.count_rows() == 3


def test_count_rows_after_filter_empty(df):
    rel = relation(df).filter(ma.col("status").eq(ma.lit("zzz")))
    assert rel.count_rows() == 0


def test_count_rows_returns_int(df):
    result = relation(df).count_rows()
    assert isinstance(result, int)
    assert not isinstance(result, bool)


def test_count_rows_polars_lazyframe():
    lf = pl.DataFrame({"x": list(range(100))}).lazy()
    assert relation(lf).count_rows() == 100


def test_count_rows_narwhals():
    pytest.importorskip("narwhals")
    import narwhals as nw
    nw_df = nw.from_native(pl.DataFrame({"x": [1, 2, 3, 4]}), eager_only=True)
    assert relation(nw_df).count_rows() == 4


def test_count_rows_ibis():
    pytest.importorskip("ibis")
    import ibis
    t = ibis.memtable({"x": [1, 2, 3, 4, 5]})
    assert relation(t).count_rows() == 5
