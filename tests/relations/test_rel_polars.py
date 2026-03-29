"""Polars integration tests for the Relation API.

These tests exercise the full pipeline:
    relation(polars_df) → operations → .to_polars()

Real data flows through the full stack: Relation API → AST nodes →
unified visitor → Polars backend → Polars results.
"""

from __future__ import annotations

import polars as pl
import pytest

from mountainash.relations import relation


# ---------------------------------------------------------------------------
# Projection
# ---------------------------------------------------------------------------


class TestSelect:
    def test_select_two_columns(self, polars_df):
        result = relation(polars_df).select("id", "name").to_polars()
        assert isinstance(result, pl.DataFrame)
        assert result.columns == ["id", "name"]
        assert len(result) == 5

    def test_select_single_column(self, polars_df):
        result = relation(polars_df).select("category").to_polars()
        assert result.columns == ["category"]
        assert result["category"].to_list() == ["A", "B", "A", "C", "B"]


class TestWithColumns:
    def test_add_computed_column(self, polars_df):
        result = (
            relation(polars_df)
            .with_columns(pl.col("value") * 2)
            .to_polars()
        )
        assert isinstance(result, pl.DataFrame)
        # Original columns still present, value overwritten with doubled values
        assert "value" in result.columns
        assert result["value"].to_list() == [201.0, 401.4, 601.8, 800.4, 1001.6]

    def test_add_named_column(self, polars_df):
        result = (
            relation(polars_df)
            .with_columns((pl.col("value") + pl.col("score")).alias("total"))
            .to_polars()
        )
        assert "total" in result.columns
        assert len(result.columns) == 7  # original 6 + 1 new


class TestDrop:
    def test_drop_column(self, polars_df):
        result = relation(polars_df).drop("active").to_polars()
        assert "active" not in result.columns
        assert len(result.columns) == 5
        assert len(result) == 5


class TestRename:
    def test_rename_columns(self, polars_df):
        result = relation(polars_df).rename({"id": "user_id", "name": "user_name"}).to_polars()
        assert "user_id" in result.columns
        assert "user_name" in result.columns
        assert "id" not in result.columns
        assert "name" not in result.columns
        assert result["user_id"].to_list() == [1, 2, 3, 4, 5]


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------


class TestFilter:
    def test_filter_with_native_expression(self, polars_df):
        result = relation(polars_df).filter(pl.col("score") > 85).to_polars()
        assert isinstance(result, pl.DataFrame)
        # score > 85: Bob(92), Diana(95), Eve(88) → 3 rows
        assert len(result) == 3
        assert set(result["name"].to_list()) == {"Bob", "Diana", "Eve"}

    def test_filter_with_mountainash_expr(self, polars_df):
        """Test mountainash expression integration (ma.col → visitor pipeline)."""
        import mountainash as ma

        result = relation(polars_df).filter(ma.col("score").gt(85)).to_polars()
        assert len(result) == 3
        assert set(result["name"].to_list()) == {"Bob", "Diana", "Eve"}

    def test_filter_boolean_column(self, polars_df):
        result = relation(polars_df).filter(pl.col("active")).to_polars()
        # active=True: Alice, Charlie, Diana → 3 rows
        assert len(result) == 3
        assert set(result["name"].to_list()) == {"Alice", "Charlie", "Diana"}


# ---------------------------------------------------------------------------
# Sorting
# ---------------------------------------------------------------------------


class TestSort:
    def test_sort_ascending(self, polars_df):
        result = relation(polars_df).sort("name").to_polars()
        assert result["name"].to_list() == ["Alice", "Bob", "Charlie", "Diana", "Eve"]

    def test_sort_descending(self, polars_df):
        result = relation(polars_df).sort("value", descending=True).to_polars()
        assert result["name"][0] == "Eve"
        assert result["value"][0] == 500.8

    def test_sort_multi_column(self, polars_df):
        result = (
            relation(polars_df)
            .sort("category", "value", descending=[False, True])
            .to_polars()
        )
        # Category A: Charlie(300.9), Alice(100.5)
        # Category B: Eve(500.8), Bob(200.7)
        # Category C: Diana(400.2)
        assert result["category"].to_list() == ["A", "A", "B", "B", "C"]
        assert result["name"].to_list() == ["Charlie", "Alice", "Eve", "Bob", "Diana"]


# ---------------------------------------------------------------------------
# Fetch (head / tail / slice)
# ---------------------------------------------------------------------------


class TestHead:
    def test_head(self, polars_df):
        result = relation(polars_df).head(3).to_polars()
        assert isinstance(result, pl.DataFrame)
        assert len(result) == 3
        assert result["id"].to_list() == [1, 2, 3]


class TestTail:
    def test_tail(self, polars_df):
        result = relation(polars_df).tail(2).to_polars()
        assert len(result) == 2
        assert result["id"].to_list() == [4, 5]


class TestSlice:
    def test_slice(self, polars_df):
        result = relation(polars_df).slice(1, 3).to_polars()
        assert len(result) == 3
        # Rows at offset 1: id=2, id=3, id=4
        assert result["id"].to_list() == [2, 3, 4]


# ---------------------------------------------------------------------------
# Joins
# ---------------------------------------------------------------------------


class TestJoin:
    def test_inner_join(self, polars_df, polars_join_df):
        result = (
            relation(polars_df)
            .join(relation(polars_join_df), on="id")
            .to_polars()
        )
        assert isinstance(result, pl.DataFrame)
        # Inner join: ids 1,2,3 match → 3 rows
        assert len(result) == 3
        assert "label" in result.columns
        assert set(result["id"].to_list()) == {1, 2, 3}

    def test_left_join(self, polars_df, polars_join_df):
        result = (
            relation(polars_df)
            .join(relation(polars_join_df), on="id", how="left")
            .to_polars()
        )
        # All left rows present
        assert len(result) == 5
        assert "label" in result.columns
        # ids 4,5 have null labels
        labels = result.sort("id")["label"].to_list()
        assert labels[:3] == ["x", "y", "z"]
        assert labels[3] is None
        assert labels[4] is None

    def test_anti_join(self, polars_df, polars_join_df):
        result = (
            relation(polars_df)
            .join(relation(polars_join_df), on="id", how="anti")
            .to_polars()
        )
        # Anti join: ids NOT in join_df → ids 4,5
        assert len(result) == 2
        assert set(result["id"].to_list()) == {4, 5}


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


class TestGroupByAgg:
    def test_group_by_sum(self, polars_df):
        result = (
            relation(polars_df)
            .group_by("category")
            .agg(pl.col("value").sum())
            .to_polars()
        )
        assert isinstance(result, pl.DataFrame)
        # 3 unique categories: A, B, C
        assert len(result) == 3
        # Verify sums by sorting for deterministic order
        result = result.sort("category")
        assert result["category"].to_list() == ["A", "B", "C"]
        # A: 100.5 + 300.9 = 401.4
        # B: 200.7 + 500.8 = 701.5
        # C: 400.2
        values = result["value"].to_list()
        assert pytest.approx(values[0], rel=1e-6) == 401.4
        assert pytest.approx(values[1], rel=1e-6) == 701.5
        assert pytest.approx(values[2], rel=1e-6) == 400.2


class TestUnique:
    def test_unique_on_column(self, polars_df):
        result = relation(polars_df).unique("category").to_polars()
        assert isinstance(result, pl.DataFrame)
        # 3 unique categories
        assert len(result) == 3
        assert set(result["category"].to_list()) == {"A", "B", "C"}


# ---------------------------------------------------------------------------
# Extension operations
# ---------------------------------------------------------------------------


class TestDropNulls:
    def test_drop_nulls(self, polars_df):
        # Create a df with some nulls
        df_with_nulls = polars_df.with_columns(
            pl.when(pl.col("id") > 3).then(None).otherwise(pl.col("name")).alias("name")
        )
        result = relation(df_with_nulls).drop_nulls(subset=["name"]).to_polars()
        assert len(result) == 3
        assert all(v is not None for v in result["name"].to_list())


class TestWithRowIndex:
    def test_with_row_index(self, polars_df):
        result = relation(polars_df).with_row_index(name="idx").to_polars()
        assert "idx" in result.columns
        assert result["idx"].to_list() == [0, 1, 2, 3, 4]
        assert len(result.columns) == 7  # original 6 + idx


# ---------------------------------------------------------------------------
# Pipeline chain
# ---------------------------------------------------------------------------


class TestPipelineChain:
    def test_filter_sort_head_select(self, polars_df):
        """Real workflow: filter → sort → head → select → to_polars()."""
        result = (
            relation(polars_df)
            .filter(pl.col("score") > 80)
            .sort("value", descending=True)
            .head(3)
            .select("name", "value")
            .to_polars()
        )
        assert isinstance(result, pl.DataFrame)
        assert result.columns == ["name", "value"]
        # score > 80: Alice(85), Bob(92), Diana(95), Eve(88) → 4 rows
        # sorted by value desc: Eve(500.8), Diana(400.2), Bob(200.7), Alice(100.5)
        # head 3: Eve, Diana, Bob
        assert len(result) == 3
        assert result["name"].to_list() == ["Eve", "Diana", "Bob"]

    def test_with_columns_filter_sort(self, polars_df):
        """Pipeline: add column → filter on it → sort."""
        result = (
            relation(polars_df)
            .with_columns((pl.col("value") / pl.col("score")).alias("efficiency"))
            .filter(pl.col("efficiency") > 2.0)
            .sort("efficiency", descending=True)
            .to_polars()
        )
        assert "efficiency" in result.columns
        assert len(result) > 0
        # All efficiency values should be > 2.0
        assert all(v > 2.0 for v in result["efficiency"].to_list())
        # Should be sorted descending
        eff = result["efficiency"].to_list()
        assert eff == sorted(eff, reverse=True)
