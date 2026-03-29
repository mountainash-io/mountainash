"""Cross-backend value access function tests for window operations.

Tests lead, lag, first_value, last_value, nth_value against a real Polars
DataFrame to verify that the full build-then-compile pipeline produces
correct results when combined with .over() partitioning.
"""

from __future__ import annotations

import pytest
import polars as pl
import mountainash as ma


# ========================================
# Fixtures
# ========================================


@pytest.fixture
def ts_df():
    return pl.DataFrame({
        "id": ["A", "A", "A", "B", "B", "B"],
        "ts": [1, 2, 3, 1, 2, 3],
        "value": [10, 20, 30, 100, 200, 300],
    })


# ========================================
# Value Access Window Function Tests
# ========================================


class TestLag:
    """Test lag() with .over() partition context."""

    def test_lag_over_partition(self, ts_df):
        """ma.col('value').lag(1).over('id', order_by='ts') should return
        the previous row's value within each partition.

        Expected for id=A sorted by ts:
          ts=1 -> null (no previous row)
          ts=2 -> 10
          ts=3 -> 20
        """
        expr = ma.col("value").lag(1).over("id", order_by="ts")
        result = ts_df.sort(["id", "ts"]).with_columns(
            expr.compile(ts_df).alias("prev")
        )

        a_rows = result.filter(pl.col("id") == "A").sort("ts")
        assert a_rows["prev"].to_list() == [None, 10, 20]

        b_rows = result.filter(pl.col("id") == "B").sort("ts")
        assert b_rows["prev"].to_list() == [None, 100, 200]


class TestLead:
    """Test lead() with .over() partition context."""

    def test_lead_over_partition(self, ts_df):
        """ma.col('value').lead(1).over('id', order_by='ts') should return
        the next row's value within each partition.

        Expected for id=A sorted by ts:
          ts=1 -> 20
          ts=2 -> 30
          ts=3 -> null (no next row)
        """
        expr = ma.col("value").lead(1).over("id", order_by="ts")
        result = ts_df.sort(["id", "ts"]).with_columns(
            expr.compile(ts_df).alias("next_val")
        )

        a_rows = result.filter(pl.col("id") == "A").sort("ts")
        assert a_rows["next_val"].to_list() == [20, 30, None]

        b_rows = result.filter(pl.col("id") == "B").sort("ts")
        assert b_rows["next_val"].to_list() == [200, 300, None]


class TestFirstValue:
    """Test first_value() with .over() partition context."""

    def test_first_value_over_partition(self, ts_df):
        """ma.col('value').first_value().over('id', order_by='ts') should
        return the first value in each partition.

        All rows in group A should have first_value = 10.
        All rows in group B should have first_value = 100.
        """
        expr = ma.col("value").first_value().over("id", order_by="ts")
        result = ts_df.sort(["id", "ts"]).with_columns(
            expr.compile(ts_df).alias("first")
        )

        a_rows = result.filter(pl.col("id") == "A")
        assert a_rows["first"].to_list() == [10, 10, 10]

        b_rows = result.filter(pl.col("id") == "B")
        assert b_rows["first"].to_list() == [100, 100, 100]


class TestLastValue:
    """Test last_value() with .over() partition context."""

    def test_last_value_over_partition(self, ts_df):
        """ma.col('value').last_value().over('id', order_by='ts') should
        return the last value in each partition.

        All rows in group A should have last_value = 30.
        All rows in group B should have last_value = 300.
        """
        expr = ma.col("value").last_value().over("id", order_by="ts")
        result = ts_df.sort(["id", "ts"]).with_columns(
            expr.compile(ts_df).alias("last")
        )

        a_rows = result.filter(pl.col("id") == "A")
        assert a_rows["last"].to_list() == [30, 30, 30]

        b_rows = result.filter(pl.col("id") == "B")
        assert b_rows["last"].to_list() == [300, 300, 300]


class TestNthValue:
    """Test nth_value() with .over() partition context."""

    @pytest.mark.xfail(reason="nth_value may not be supported in Polars .over() context")
    def test_nth_value_over_partition(self, ts_df):
        """ma.col('value').nth_value(2).over('id', order_by='ts') should
        return the 2nd value in each partition.

        All rows in group A should have nth_value = 20.
        All rows in group B should have nth_value = 200.
        """
        expr = ma.col("value").nth_value(2).over("id", order_by="ts")
        result = ts_df.sort(["id", "ts"]).with_columns(
            expr.compile(ts_df).alias("nth")
        )

        a_rows = result.filter(pl.col("id") == "A")
        assert a_rows["nth"].to_list() == [20, 20, 20]

        b_rows = result.filter(pl.col("id") == "B")
        assert b_rows["nth"].to_list() == [200, 200, 200]
