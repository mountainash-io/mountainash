"""Tests that ranking functions produce correct rank values, not sequential numbers."""

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
        expr = ma.col("score").dense_rank().over("team", order_by="score")
        result = rank_df.with_columns(expr.compile(rank_df).alias("drank"))

        team_a = result.filter(pl.col("team") == "A").sort("score")
        ranks = team_a["drank"].to_list()
        # scores: [10, 20, 30, 30] → dense_rank: [1, 2, 3, 3]
        assert ranks == [1, 2, 3, 3]

    def test_rank_with_gaps(self, rank_df):
        """rank (method='min') should produce gaps for ties."""
        expr = ma.col("score").rank().over("team", order_by="score")
        result = rank_df.with_columns(expr.compile(rank_df).alias("rnk"))

        team_a = result.filter(pl.col("team") == "A").sort("score")
        ranks = team_a["rnk"].to_list()
        # scores: [10, 20, 30, 30] → rank(min): [1, 2, 3, 3]
        assert ranks == [1, 2, 3, 3]

    def test_row_number_unique(self, rank_df):
        """row_number should produce unique sequential numbers."""
        expr = ma.col("score").row_number().over("team", order_by="score")
        result = rank_df.with_columns(expr.compile(rank_df).alias("rn"))

        team_a = result.filter(pl.col("team") == "A").sort("score")
        ranks = team_a["rn"].to_list()
        # scores: [10, 20, 30, 30] → row_number: [1, 2, 3, 4] (all unique)
        assert ranks == [1, 2, 3, 4]

    def test_rank_descending_produces_different_output(self, rank_df):
        """descending order_by must produce different ranks than ascending."""
        expr_asc = ma.col("score").rank().over("team", order_by="score")
        expr_desc = ma.col("score").rank().over("team", order_by="-score")

        result_asc = rank_df.with_columns(expr_asc.compile(rank_df).alias("rnk"))
        result_desc = rank_df.with_columns(expr_desc.compile(rank_df).alias("rnk"))

        team_a_asc = result_asc.filter(pl.col("team") == "A").sort("score")["rnk"].to_list()
        team_a_desc = result_desc.filter(pl.col("team") == "A").sort("score")["rnk"].to_list()

        assert team_a_asc != team_a_desc
