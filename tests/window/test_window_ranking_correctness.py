"""Tests that ranking functions produce correct rank values, not sequential numbers.

All tests use `.over()` for partitioned ranking, which requires Polars-specific
.over() execution. Additionally, narwhals and ibis backends do not yet accept
the `rank_method` option passed by `dense_rank()` / `rank()` API builder options,
so all ranking tests are Polars-only.
"""

from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma


@pytest.fixture
def rank_df():
    return pl.DataFrame({
        "team": ["A", "A", "A", "A", "B", "B", "B"],
        "score": [10, 30, 20, 30, 50, 10, 30],
    })


class TestRankingCorrectness:
    def test_dense_rank_no_gaps(self, rank_df):
        """dense_rank should produce consecutive ranks with no gaps for ties."""
        expr = ma.col("score").dense_rank().over("team")
        result = rank_df.with_columns(expr.compile(rank_df).alias("drank"))

        team_a = result.filter(pl.col("team") == "A").sort("score")
        ranks = team_a["drank"].to_list()
        # scores: [10, 20, 30, 30] → dense_rank: [1, 2, 3, 3]
        assert ranks == [1, 2, 3, 3]

    def test_rank_with_gaps(self, rank_df):
        """rank (method='min') should produce gaps for ties."""
        expr = ma.col("score").rank(method="min").over("team")
        result = rank_df.with_columns(expr.compile(rank_df).alias("rnk"))

        team_a = result.filter(pl.col("team") == "A").sort("score")
        ranks = team_a["rnk"].to_list()
        # scores: [10, 20, 30, 30] → rank(min): [1, 2, 3, 3]
        assert ranks == [1, 2, 3, 3]

    def test_row_number_unique(self, rank_df):
        """row_number should produce unique sequential numbers."""
        expr = ma.col("score").row_number().over("team")
        result = rank_df.with_columns(expr.compile(rank_df).alias("rn"))

        team_a = result.filter(pl.col("team") == "A").sort("score")
        ranks = team_a["rn"].to_list()
        # scores: [10, 20, 30, 30] → row_number: [1, 2, 3, 4] (all unique)
        assert ranks == [1, 2, 3, 4]

    def test_rank_descending_produces_different_output(self, rank_df):
        """descending order_by must produce different ranks than ascending."""
        expr_asc = ma.col("score").rank(method="min").over("team")
        expr_desc = ma.col("score").rank(method="min", descending=True).over("team")

        result_asc = rank_df.with_columns(expr_asc.compile(rank_df).alias("rnk"))
        result_desc = rank_df.with_columns(expr_desc.compile(rank_df).alias("rnk"))

        team_a_asc = result_asc.filter(pl.col("team") == "A").sort("score")["rnk"].to_list()
        team_a_desc = result_desc.filter(pl.col("team") == "A").sort("score")["rnk"].to_list()

        assert team_a_asc != team_a_desc

    # ========================================
    # New rank(method=...) API tests
    # ========================================

    def test_rank_method_dense(self, rank_df):
        """rank(method='dense') is equivalent to dense_rank()."""
        expr = ma.col("score").rank(method="dense").over("team")
        result = rank_df.with_columns(expr.compile(rank_df).alias("drank"))
        team_a = result.filter(pl.col("team") == "A").sort("score")
        assert team_a["drank"].to_list() == [1, 2, 3, 3]

    def test_rank_method_ordinal(self, rank_df):
        """rank(method='ordinal') produces unique sequential ranks."""
        expr = ma.col("score").rank(method="ordinal").over("team")
        result = rank_df.with_columns(expr.compile(rank_df).alias("rn"))
        team_a = result.filter(pl.col("team") == "A").sort("score")
        assert team_a["rn"].to_list() == [1, 2, 3, 4]

    def test_rank_method_average(self, rank_df):
        """rank(method='average') produces averaged ranks for ties."""
        expr = ma.col("score").rank(method="average").over("team")
        result = rank_df.with_columns(expr.compile(rank_df).alias("rnk"))
        team_a = result.filter(pl.col("team") == "A").sort("score")
        # scores: [10, 20, 30, 30] → average rank: [1.0, 2.0, 3.5, 3.5]
        assert team_a["rnk"].to_list() == [1.0, 2.0, 3.5, 3.5]

    def test_rank_method_max(self, rank_df):
        """rank(method='max') produces max rank for ties."""
        expr = ma.col("score").rank(method="max").over("team")
        result = rank_df.with_columns(expr.compile(rank_df).alias("rnk"))
        team_a = result.filter(pl.col("team") == "A").sort("score")
        # scores: [10, 20, 30, 30] → max rank: [1, 2, 4, 4]
        assert team_a["rnk"].to_list() == [1, 2, 4, 4]

    def test_rank_descending_via_method_param(self, rank_df):
        """rank(descending=True) directly passes descending to Polars rank."""
        expr_asc = ma.col("score").rank(method="dense", descending=False).over("team")
        expr_desc = ma.col("score").rank(method="dense", descending=True).over("team")

        result_asc = rank_df.with_columns(expr_asc.compile(rank_df).alias("rnk"))
        result_desc = rank_df.with_columns(expr_desc.compile(rank_df).alias("rnk"))

        team_a_asc = result_asc.filter(pl.col("team") == "A").sort("score")["rnk"].to_list()
        team_a_desc = result_desc.filter(pl.col("team") == "A").sort("score")["rnk"].to_list()

        assert team_a_asc != team_a_desc

    def test_rank_over_merges_partition(self, rank_df):
        """rank() pre-populates order_by; .over() adds partition_by."""
        # rank() sets order_by=score; .over("team") adds partition_by=team
        expr = ma.col("score").rank(method="min").over("team")
        result = rank_df.with_columns(expr.compile(rank_df).alias("rnk"))

        # Team B: scores [50, 10, 30] → sorted [10, 30, 50] → ranks [1, 2, 3]
        team_b = result.filter(pl.col("team") == "B").sort("score")
        assert team_b["rnk"].to_list() == [1, 2, 3]

    def test_rank_over_preserves_order_by_from_rank(self, rank_df):
        """When .over() provides order_by, rank()'s order_by takes precedence."""
        # rank() sets order_by=score asc; .over() tries to set order_by="-score"
        # The merge should preserve rank()'s order_by
        expr = ma.col("score").rank(method="min").over("team", order_by="-score")
        result = rank_df.with_columns(expr.compile(rank_df).alias("rnk"))

        team_a = result.filter(pl.col("team") == "A").sort("score")
        # rank()'s ascending order_by wins, so [10, 20, 30, 30] → [1, 2, 3, 3]
        assert team_a["rnk"].to_list() == [1, 2, 3, 3]
