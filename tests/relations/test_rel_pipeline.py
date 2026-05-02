"""Multi-operation pipeline tests for the Relation API.

Exercises real-world workflows that chain multiple operations together.
Tests both Polars-native and Narwhals (pandas/PyArrow) backends.
"""

from __future__ import annotations

import narwhals as nw
import pandas as pd
import polars as pl
import pyarrow as pa
import pytest

from mountainash.relations import relation

# Trigger backend registration (side-effect imports)
import mountainash.relations.backends  # noqa: F401
import mountainash.expressions.backends  # noqa: F401


# ---------------------------------------------------------------------------
# Helpers for narwhals results
# ---------------------------------------------------------------------------


def _to_pydict(result) -> dict[str, list]:
    """Convert any backend result to a column-oriented dict."""
    if hasattr(result, "to_pandas"):
        df = result.to_pandas()
        return {c: df[c].tolist() for c in df.columns}
    if isinstance(result, pd.DataFrame):
        return {c: result[c].tolist() for c in result.columns}
    if hasattr(result, "to_pydict"):
        return {k: list(v) for k, v in result.to_pydict().items()}
    raise TypeError(f"Cannot convert {type(result)} to pydict")


def _row_count(result) -> int:
    """Get the row count from any result type."""
    if hasattr(result, "shape"):
        return result.shape[0]
    if hasattr(result, "num_rows"):
        return result.num_rows
    raise TypeError(f"Cannot get row count from {type(result)}")


def _columns(result) -> list[str]:
    """Get column names from any result type."""
    if hasattr(result, "column_names"):
        return result.column_names
    if hasattr(result, "columns"):
        cols = result.columns
        return list(cols) if not isinstance(cols, list) else cols
    raise TypeError(f"Cannot get columns from {type(result)}")


# ---------------------------------------------------------------------------
# Polars pipelines
# ---------------------------------------------------------------------------


class TestPolarisPipelines:
    """Multi-operation chains on Polars data."""

    def test_filter_sort_head(self, polars_df):
        result = (
            relation(polars_df)
            .filter(pl.col("score") > 80)
            .sort("name")
            .head(3)
            .to_polars()
        )
        assert len(result) <= 3
        assert all(s > 80 for s in result["score"].to_list())

    def test_select_filter_sort(self, polars_df):
        result = (
            relation(polars_df)
            .select("id", "name", "score")
            .filter(pl.col("score") >= 85)
            .sort("score", descending=True)
            .to_polars()
        )
        assert result.columns == ["id", "name", "score"]
        scores = result["score"].to_list()
        assert scores == sorted(scores, reverse=True)
        assert all(s >= 85 for s in scores)

    def test_with_columns_filter_group(self, polars_df):
        result = (
            relation(polars_df)
            .with_columns(pl.col("value").round(0).alias("rounded"))
            .filter(pl.col("active") == True)  # noqa: E712
            .group_by("category")
            .agg(pl.col("rounded").sum().alias("total"))
            .sort("category")
            .to_polars()
        )
        assert "total" in result.columns
        assert "category" in result.columns
        # active=True rows: Alice(A, 100.5→101), Charlie(A, 300.9→301), Diana(C, 400.2→400)
        result_sorted = result.sort("category")
        categories = result_sorted["category"].to_list()
        assert "A" in categories
        assert "C" in categories

    def test_join_then_aggregate(self, polars_df, polars_join_df):
        result = (
            relation(polars_df)
            .join(relation(polars_join_df), on="id", how="inner")
            .group_by("label")
            .agg(pl.col("value").mean().alias("avg_value"))
            .sort("label")
            .to_polars()
        )
        assert "label" in result.columns
        assert "avg_value" in result.columns
        assert len(result) == 3  # labels x, y, z
        assert result["label"].to_list() == ["x", "y", "z"]

    def test_filter_rename_select(self, polars_df):
        result = (
            relation(polars_df)
            .filter(pl.col("active") == True)  # noqa: E712
            .rename({"name": "full_name", "score": "grade"})
            .select("full_name", "grade")
            .sort("grade", descending=True)
            .to_polars()
        )
        assert result.columns == ["full_name", "grade"]
        grades = result["grade"].to_list()
        assert grades == sorted(grades, reverse=True)

    def test_drop_with_columns_sort(self, polars_df):
        result = (
            relation(polars_df)
            .drop("active")
            .with_columns((pl.col("value") * pl.col("score")).alias("weighted"))
            .sort("weighted", descending=True)
            .head(3)
            .to_polars()
        )
        assert "active" not in result.columns
        assert "weighted" in result.columns
        assert len(result) == 3
        weighted = result["weighted"].to_list()
        assert weighted == sorted(weighted, reverse=True)

    def test_unique_sort(self, polars_df):
        result = (
            relation(polars_df)
            .unique("category")
            .sort("category")
            .to_polars()
        )
        assert result["category"].to_list() == ["A", "B", "C"]


# ---------------------------------------------------------------------------
# Narwhals pipelines (pandas input)
# ---------------------------------------------------------------------------


class TestNarwhalsPipelinesPandas:
    """Multi-operation chains on pandas data via Narwhals."""

    def test_filter_sort_head(self, pandas_df):
        result = (
            relation(pandas_df)
            .filter(nw.col("score") > 80)
            .sort("name")
            .head(3)
            .collect()
        )
        count = _row_count(result)
        assert count <= 3
        data = _to_pydict(result)
        assert all(s > 80 for s in data["score"])

    def test_select_filter_sort(self, pandas_df):
        result = (
            relation(pandas_df)
            .select("id", "name", "score")
            .filter(nw.col("score") >= 85)
            .sort("score", descending=True)
            .collect()
        )
        cols = _columns(result)
        assert set(cols) == {"id", "name", "score"}
        data = _to_pydict(result)
        assert data["score"] == sorted(data["score"], reverse=True)

    def test_filter_rename_sort(self, pandas_df):
        result = (
            relation(pandas_df)
            .filter(nw.col("active") == True)  # noqa: E712
            .rename({"name": "full_name"})
            .select("full_name", "score")
            .sort("score")
            .collect()
        )
        cols = _columns(result)
        assert "full_name" in cols
        assert "name" not in cols
        data = _to_pydict(result)
        assert data["score"] == sorted(data["score"])

    def test_drop_sort_head(self, pandas_df):
        result = (
            relation(pandas_df)
            .drop("active", "category")
            .sort("value", descending=True)
            .head(2)
            .collect()
        )
        cols = _columns(result)
        assert "active" not in cols
        assert "category" not in cols
        assert _row_count(result) == 2


# ---------------------------------------------------------------------------
# Narwhals pipelines (PyArrow input)
# ---------------------------------------------------------------------------


class TestNarwhalsPipelinesPyArrow:
    """Multi-operation chains on PyArrow data via Narwhals."""

    def test_filter_sort_head(self, pyarrow_table):
        result = (
            relation(pyarrow_table)
            .filter(nw.col("score") > 80)
            .sort("name")
            .head(3)
            .collect()
        )
        count = _row_count(result)
        assert count <= 3

    def test_select_rename(self, pyarrow_table):
        result = (
            relation(pyarrow_table)
            .select("id", "name", "value")
            .rename({"value": "amount"})
            .sort("amount")
            .collect()
        )
        cols = _columns(result)
        assert "amount" in cols
        assert "value" not in cols
        data = _to_pydict(result)
        assert data["amount"] == sorted(data["amount"])

    def test_unique_sort(self, pyarrow_table):
        result = (
            relation(pyarrow_table)
            .unique("category")
            .sort("category")
            .collect()
        )
        data = _to_pydict(result)
        assert sorted(data["category"]) == ["A", "B", "C"]
