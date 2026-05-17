"""Tests for Relation.unnest() — struct field expansion."""

from __future__ import annotations

import ibis
import pandas as pd
import polars as pl
import pytest

from mountainash.relations import relation

import mountainash.relations.backends.relation_systems.ibis  # noqa: F401
import mountainash.relations.backends.relation_systems.narwhals  # noqa: F401
import mountainash.expressions.backends.expression_systems.ibis  # noqa: F401


@pytest.fixture
def struct_df():
    """DataFrame with a struct column."""
    return pl.DataFrame({
        "id": [1, 2, 3],
        "metadata": [{"x": 10, "y": "a"}, {"x": 20, "y": "b"}, {"x": 30, "y": "c"}],
    })


class TestUnnestAPI:
    def test_unnest_builds_ast(self, struct_df):
        """unnest() returns a Relation (doesn't crash at build time)."""
        r = relation(struct_df).unnest("metadata", separator="_")
        assert r is not None

    def test_unnest_requires_columns(self, struct_df):
        """unnest() with no columns raises ValueError."""
        with pytest.raises(ValueError, match="unnest requires at least one column"):
            relation(struct_df).unnest(separator="_")


class TestUnnestPolars:
    def test_single_struct_column(self, struct_df):
        """Unnest expands struct fields with separator prefix."""
        result = relation(struct_df).unnest("metadata", separator="_").to_polars()
        assert "metadata_x" in result.columns
        assert "metadata_y" in result.columns
        assert "metadata" not in result.columns
        assert result["metadata_x"].to_list() == [10, 20, 30]
        assert result["metadata_y"].to_list() == ["a", "b", "c"]
        assert result["id"].to_list() == [1, 2, 3]

    def test_empty_separator(self, struct_df):
        """Empty separator produces bare field names."""
        result = relation(struct_df).unnest("metadata", separator="").to_polars()
        assert "x" in result.columns
        assert "y" in result.columns
        assert "metadata" not in result.columns

    def test_multiple_struct_columns(self):
        """Unnest multiple struct columns in one call."""
        df = pl.DataFrame({
            "id": [1, 2],
            "meta": [{"a": 1}, {"a": 2}],
            "addr": [{"city": "X"}, {"city": "Y"}],
        })
        result = relation(df).unnest("meta", "addr", separator="_").to_polars()
        assert "meta_a" in result.columns
        assert "addr_city" in result.columns
        assert "meta" not in result.columns
        assert "addr" not in result.columns

    def test_null_rows(self):
        """Null struct rows produce null in expanded fields."""
        df = pl.DataFrame({
            "id": [1, 2],
            "s": [{"x": 10}, None],
        }, schema={"id": pl.Int64, "s": pl.Struct({"x": pl.Int64})})
        result = relation(df).unnest("s", separator="_").to_polars()
        assert result["s_x"].to_list() == [10, None]

    def test_nested_struct_single_level(self):
        """Only first level is expanded — nested structs stay as struct columns."""
        df = pl.DataFrame({
            "id": [1],
            "s": [{"inner": {"deep": 99}, "flat": 1}],
        })
        result = relation(df).unnest("s", separator="_").to_polars()
        assert "s_inner" in result.columns
        assert "s_flat" in result.columns
        assert result["s_inner"].dtype == pl.Struct({"deep": pl.Int64})


@pytest.fixture
def ibis_struct_table():
    """Ibis table with a struct column via DuckDB backend."""
    con = ibis.duckdb.connect()
    return con.create_table(
        "test_struct",
        pl.DataFrame({
            "id": [1, 2, 3],
            "metadata": [{"x": 10, "y": "a"}, {"x": 20, "y": "b"}, {"x": 30, "y": "c"}],
        }).to_pandas(),
    )


class TestUnnestIbis:
    def test_single_struct_column(self, ibis_struct_table):
        """Unnest expands struct fields with separator prefix on Ibis."""
        result = relation(ibis_struct_table).unnest("metadata", separator="_").to_polars()
        assert "metadata_x" in result.columns
        assert "metadata_y" in result.columns
        assert "metadata" not in result.columns
        assert sorted(result["metadata_x"].to_list()) == [10, 20, 30]
        assert sorted(result["metadata_y"].to_list()) == ["a", "b", "c"]

    def test_empty_separator(self, ibis_struct_table):
        """Empty separator produces bare field names on Ibis."""
        result = relation(ibis_struct_table).unnest("metadata", separator="").to_polars()
        assert "x" in result.columns
        assert "y" in result.columns
        assert "metadata" not in result.columns

    def test_multiple_struct_columns(self):
        """Unnest multiple struct columns on Ibis."""
        con = ibis.duckdb.connect()
        t = con.create_table(
            "multi_struct",
            pl.DataFrame({
                "id": [1, 2],
                "meta": [{"a": 1}, {"a": 2}],
                "addr": [{"city": "X"}, {"city": "Y"}],
            }).to_pandas(),
        )
        result = relation(t).unnest("meta", "addr", separator="_").to_polars()
        assert "meta_a" in result.columns
        assert "addr_city" in result.columns
        assert "meta" not in result.columns
        assert "addr" not in result.columns


class TestUnnestNarwhals:
    @pytest.mark.xfail(
        reason="Narwhals has no frame-level unnest — deferred to Phase 2",
        raises=NotImplementedError,
    )
    def test_unnest_not_supported(self):
        """Narwhals unnest raises NotImplementedError."""
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "metadata": [{"x": 10, "y": "a"}, {"x": 20, "y": "b"}, {"x": 30, "y": "c"}],
        })
        relation(df).unnest("metadata", separator="_").to_polars()
