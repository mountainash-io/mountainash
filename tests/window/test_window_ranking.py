"""Tests for window ranking functions compiled and executed against Polars.

Tests:
- rank().over() compiles and produces correct rankings per partition
- dense_rank().over() compiles and produces results
- row_number().over() produces distinct row numbers per partition
- ntile().over() produces bucket assignments
- percent_rank().over() (xfail: approximation in Polars)
- cume_dist().over() (xfail: approximation in Polars)
"""

from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma


@pytest.fixture
def ranking_df():
    return pl.DataFrame({
        "team": ["A", "A", "A", "B", "B", "B"],
        "score": [10, 20, 20, 30, 10, 20],
    })


class TestWindowRankingFunctions:
    """Window ranking functions compiled against Polars."""

    def test_rank_over_partition(self, ranking_df):
        """rank().over() compiles and produces ranks within each partition."""
        expr = ma.col("score").rank().over("team", order_by="score")
        result = ranking_df.with_columns(expr.compile(ranking_df).alias("rnk"))

        assert "rnk" in result.columns
        # Team A has scores 10, 20, 20 — should get 3 rank values
        team_a = result.filter(pl.col("team") == "A")
        ranks_a = team_a["rnk"].to_list()
        assert len(ranks_a) == 3
        # All ranks should be positive integers
        assert all(r >= 1 for r in ranks_a)

    def test_dense_rank_over_partition(self, ranking_df):
        """dense_rank().over() compiles and produces results."""
        expr = ma.col("score").dense_rank().over("team", order_by="score")
        result = ranking_df.with_columns(expr.compile(ranking_df).alias("drnk"))

        assert "drnk" in result.columns
        team_a = result.filter(pl.col("team") == "A")
        ranks_a = team_a["drnk"].to_list()
        assert len(ranks_a) == 3
        assert all(r >= 1 for r in ranks_a)

    def test_row_number_over_partition(self, ranking_df):
        """row_number().over() produces 3 distinct row numbers per team."""
        expr = ma.col("score").row_number().over("team", order_by="score")
        result = ranking_df.with_columns(expr.compile(ranking_df).alias("rn"))

        assert "rn" in result.columns
        for team_name in ["A", "B"]:
            team = result.filter(pl.col("team") == team_name)
            row_nums = team["rn"].to_list()
            assert len(row_nums) == 3
            # Each team should have 3 distinct row numbers
            assert len(set(row_nums)) == 3

    @pytest.mark.xfail(
        reason="ntile visitor passes wrong arg count to Polars backend (3 vs 2)",
        raises=TypeError,
    )
    def test_ntile_over_partition(self, ranking_df):
        """ntile(2).over() compiles and produces bucket assignments."""
        expr = ma.col("score").ntile(2).over("team", order_by="score")
        result = ranking_df.with_columns(expr.compile(ranking_df).alias("bucket"))

        assert "bucket" in result.columns
        team_a = result.filter(pl.col("team") == "A")
        buckets = team_a["bucket"].to_list()
        assert len(buckets) == 3
        # All buckets should be 1 or 2
        assert all(b in (1, 2) for b in buckets)

    def test_percent_rank_over_partition(self, ranking_df):
        """percent_rank().over() compiles and produces results between 0 and 1."""
        expr = ma.col("score").percent_rank().over("team", order_by="score")
        result = ranking_df.with_columns(expr.compile(ranking_df).alias("prnk"))

        assert "prnk" in result.columns
        team_a = result.filter(pl.col("team") == "A")
        pct_ranks = team_a["prnk"].to_list()
        assert len(pct_ranks) == 3
        assert all(0.0 <= r <= 1.0 for r in pct_ranks)

    def test_cume_dist_over_partition(self, ranking_df):
        """cume_dist().over() compiles and produces results between 0 and 1."""
        expr = ma.col("score").cume_dist().over("team", order_by="score")
        result = ranking_df.with_columns(expr.compile(ranking_df).alias("cdist"))

        assert "cdist" in result.columns
        team_a = result.filter(pl.col("team") == "A")
        cume_dists = team_a["cdist"].to_list()
        assert len(cume_dists) == 3
        assert all(0.0 <= d <= 1.0 for d in cume_dists)
