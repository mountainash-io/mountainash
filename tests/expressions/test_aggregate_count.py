"""End-to-end tests: col().count() and ma.count_records() via the public API."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.relations import relation


@pytest.fixture
def sample_df() -> pl.DataFrame:
    return pl.DataFrame({
        "group": ["a", "a", "b", "b", "b"],
        "value": [1, None, 3, 4, None],
    })


def test_col_count_exposed_as_method(sample_df):
    """ma.col('value').count() should be callable from the public API."""
    expr = ma.col("value").count()
    # Shape check: should return an expression, not raise AttributeError
    assert expr is not None


def test_count_records_exposed_as_free_function(sample_df):
    """ma.count_records() should be callable from the top-level namespace."""
    expr = ma.count_records()
    assert expr is not None


def test_count_via_group_by_agg(sample_df):
    """col().count() compiles correctly through the aggregate pipeline."""
    result = (
        relation(sample_df)
        .group_by("group")
        .agg(ma.col("value").count().alias("non_null_count"))
        .to_polars()
        .sort("group")
    )
    # value has 2 non-null rows in group 'a' → 1, in group 'b' → 2
    assert result["non_null_count"].to_list() == [1, 2]


def test_count_records_via_group_by_agg(sample_df):
    """ma.count_records() compiles correctly through the aggregate pipeline."""
    result = (
        relation(sample_df)
        .group_by("group")
        .agg(ma.count_records().alias("row_count"))
        .to_polars()
        .sort("group")
    )
    # group 'a' has 2 rows total, group 'b' has 3 rows total
    assert result["row_count"].to_list() == [2, 3]


def test_count_records_narwhals_backend():
    """count_records via Narwhals-backed relation."""
    pytest.importorskip("narwhals")
    import narwhals as nw
    nw_df = nw.from_native(
        pl.DataFrame({"g": ["a", "b", "b"], "v": [1, 2, None]}),
        eager_only=True,
    )
    result = (
        relation(nw_df)
        .group_by("g")
        .agg(ma.count_records().alias("n"))
        .to_polars()
        .sort("g")
    )
    assert result["n"].to_list() == [1, 2]


def test_count_records_ibis_backend():
    """count_records via Ibis-backed relation."""
    pytest.importorskip("ibis")
    import ibis
    t = ibis.memtable({"g": ["a", "b", "b"], "v": [1, 2, None]})
    result = (
        relation(t)
        .group_by("g")
        .agg(ma.count_records().alias("n"))
        .to_polars()
        .sort("g")
    )
    assert result["n"].to_list() == [1, 2]
