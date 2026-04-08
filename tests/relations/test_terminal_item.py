"""Cross-backend tests for Relation.item() terminal."""
from __future__ import annotations

from datetime import datetime

import polars as pl
import pytest

import mountainash as ma
from mountainash.relations import relation


@pytest.fixture
def three_row_df() -> pl.DataFrame:
    return pl.DataFrame({
        "id": [10, 20, 30],
        "name": ["alice", "bob", "carol"],
        "score": [1.5, 2.5, 3.5],
    })


def test_item_first_row(three_row_df):
    assert relation(three_row_df).item("id") == 10


def test_item_explicit_row_zero(three_row_df):
    assert relation(three_row_df).item("id", row=0) == 10


def test_item_string_column(three_row_df):
    assert relation(three_row_df).item("name") == "alice"


def test_item_after_head_one(three_row_df):
    rel = relation(three_row_df).head(1)
    assert rel.item("id") == 10
    assert rel.item("name") == "alice"


def test_item_after_filter_to_one_row(three_row_df):
    rel = relation(three_row_df).filter(ma.col("id").eq(ma.lit(20)))
    assert rel.item("name") == "bob"


def test_item_explicit_row_index(three_row_df):
    assert relation(three_row_df).item("id", row=2) == 30


def test_item_empty_relation_raises_index_error(three_row_df):
    rel = relation(three_row_df).filter(ma.col("id").eq(ma.lit(999)))
    with pytest.raises(IndexError, match="row 0"):
        rel.item("id")


def test_item_missing_column_raises_key_error(three_row_df):
    with pytest.raises(KeyError, match="nope"):
        relation(three_row_df).item("nope")


def test_item_row_out_of_range_raises_index_error(three_row_df):
    with pytest.raises(IndexError, match="row 5"):
        relation(three_row_df).item("id", row=5)


def test_item_negative_row_raises_index_error(three_row_df):
    with pytest.raises(IndexError):
        relation(three_row_df).item("id", row=-1)


def test_item_datetime_column():
    df = pl.DataFrame({
        "ts": [datetime(2026, 4, 8, 12, 0), datetime(2026, 4, 9, 13, 0)],
    })
    result = relation(df).item("ts")
    assert isinstance(result, datetime)
    assert result == datetime(2026, 4, 8, 12, 0)
