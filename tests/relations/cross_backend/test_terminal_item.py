"""Cross-backend tests for Relation.item() terminal."""
from __future__ import annotations

from datetime import datetime

import polars as pl
import pytest

import mountainash as ma
from mountainash.relations import relation


ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals-polars",
    "narwhals-pandas",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestItem:
    def _three_row_df(self, backend_name, backend_factory):
        return backend_factory.create(
            {"id": [10, 20, 30], "name": ["alice", "bob", "carol"], "score": [1.5, 2.5, 3.5]},
            backend_name,
        )

    def test_item_first_row(self, backend_name, backend_factory):
        df = self._three_row_df(backend_name, backend_factory)
        assert relation(df).item("id") == 10, f"[{backend_name}]"

    def test_item_explicit_row_zero(self, backend_name, backend_factory):
        df = self._three_row_df(backend_name, backend_factory)
        assert relation(df).item("id", row=0) == 10, f"[{backend_name}]"

    def test_item_string_column(self, backend_name, backend_factory):
        df = self._three_row_df(backend_name, backend_factory)
        assert relation(df).item("name") == "alice", f"[{backend_name}]"

    def test_item_after_head_one(self, backend_name, backend_factory):
        df = self._three_row_df(backend_name, backend_factory)
        rel = relation(df).head(1)
        assert rel.item("id") == 10, f"[{backend_name}]"
        assert rel.item("name") == "alice", f"[{backend_name}]"

    def test_item_after_filter_to_one_row(self, backend_name, backend_factory):
        df = self._three_row_df(backend_name, backend_factory)
        rel = relation(df).filter(ma.col("id").eq(ma.lit(20)))
        assert rel.item("name") == "bob", f"[{backend_name}]"

    def test_item_explicit_row_index(self, backend_name, backend_factory):
        df = self._three_row_df(backend_name, backend_factory)
        assert relation(df).item("id", row=2) == 30, f"[{backend_name}]"

    def test_item_empty_relation_raises_index_error(self, backend_name, backend_factory):
        df = self._three_row_df(backend_name, backend_factory)
        rel = relation(df).filter(ma.col("id").eq(ma.lit(999)))
        with pytest.raises(IndexError, match="row 0"):
            rel.item("id")

    def test_item_missing_column_raises_key_error(self, backend_name, backend_factory):
        df = self._three_row_df(backend_name, backend_factory)
        with pytest.raises(KeyError, match="nope"):
            relation(df).item("nope")

    def test_item_row_out_of_range_raises_index_error(self, backend_name, backend_factory):
        df = self._three_row_df(backend_name, backend_factory)
        with pytest.raises(IndexError, match="row 5"):
            relation(df).item("id", row=5)

    def test_item_negative_row_raises_index_error(self, backend_name, backend_factory):
        df = self._three_row_df(backend_name, backend_factory)
        with pytest.raises(IndexError):
            relation(df).item("id", row=-1)


# Polars-specific: datetime column type handling
def test_item_datetime_column():
    df = pl.DataFrame({
        "ts": [datetime(2026, 4, 8, 12, 0), datetime(2026, 4, 9, 13, 0)],
    })
    result = relation(df).item("ts")
    assert isinstance(result, datetime)
    assert result == datetime(2026, 4, 8, 12, 0)
