"""Cross-type join tests for the Relation API.

Tests that relation(polars_df).join(pandas_df, on="id") works — the visitor
coerces the right-side DataFrame to match the left side's backend type.
Also tests with PyArrow and dict inputs.
"""

from __future__ import annotations

import pandas as pd
import polars as pl
import pyarrow as pa
import pytest

from mountainash.relations import relation

# Trigger backend registration (side-effect imports)
import mountainash.relations.backends  # noqa: F401
import mountainash.expressions.backends  # noqa: F401


class TestPolarsJoinPandas:
    """Polars left side, Pandas right side."""

    def test_inner_join(self, polars_df):
        pandas_right = pd.DataFrame({"id": [1, 2, 3], "label": ["x", "y", "z"]})
        result = relation(polars_df).join(pandas_right, on="id", how="inner").to_polars()
        assert isinstance(result, pl.DataFrame)
        assert "label" in result.columns
        assert len(result) == 3
        assert set(result["id"].to_list()) == {1, 2, 3}

    def test_left_join_preserves_all_left_rows(self, polars_df):
        pandas_right = pd.DataFrame({"id": [1, 3], "color": ["red", "blue"]})
        result = relation(polars_df).join(pandas_right, on="id", how="left").to_polars()
        assert len(result) == 5  # All left rows preserved
        assert "color" in result.columns
        # Non-matching rows should have null color
        sorted_result = result.sort("id")
        colors = sorted_result["color"].to_list()
        assert colors[0] == "red"   # id=1
        assert colors[1] is None    # id=2
        assert colors[2] == "blue"  # id=3
        assert colors[3] is None    # id=4
        assert colors[4] is None    # id=5

    def test_anti_join(self, polars_df):
        pandas_right = pd.DataFrame({"id": [1, 2, 3], "label": ["x", "y", "z"]})
        result = relation(polars_df).join(pandas_right, on="id", how="anti").to_polars()
        assert len(result) == 2
        assert set(result["id"].to_list()) == {4, 5}


class TestPolarsJoinPyArrow:
    """Polars left side, PyArrow right side."""

    def test_inner_join(self, polars_df):
        pa_right = pa.table({"id": [1, 2], "tag": ["a", "b"]})
        result = relation(polars_df).join(pa_right, on="id", how="inner").to_polars()
        assert isinstance(result, pl.DataFrame)
        assert "tag" in result.columns
        assert len(result) == 2
        assert set(result["id"].to_list()) == {1, 2}

    def test_left_join(self, polars_df):
        pa_right = pa.table({"id": [2, 4], "tag": ["m", "n"]})
        result = relation(polars_df).join(pa_right, on="id", how="left").to_polars()
        assert len(result) == 5
        assert "tag" in result.columns


class TestPolarsJoinDict:
    """Polars left side, dict right side."""

    def test_inner_join_dict(self, polars_df):
        dict_right = {"id": [2, 4], "extra": ["m", "n"]}
        result = relation(polars_df).join(dict_right, on="id", how="inner").to_polars()
        assert isinstance(result, pl.DataFrame)
        assert "extra" in result.columns
        assert len(result) == 2
        assert set(result["id"].to_list()) == {2, 4}


class TestPolarsJoinPolarsRelation:
    """Polars left side joined with a Relation wrapping another Polars df.

    This is the standard case (no coercion needed) — ensures we haven't
    regressed same-backend joins.
    """

    def test_inner_join(self, polars_df, polars_join_df):
        result = (
            relation(polars_df)
            .join(relation(polars_join_df), on="id", how="inner")
            .to_polars()
        )
        assert len(result) == 3
        assert "label" in result.columns
        assert set(result["id"].to_list()) == {1, 2, 3}

    def test_left_join(self, polars_df, polars_join_df):
        result = (
            relation(polars_df)
            .join(relation(polars_join_df), on="id", how="left")
            .to_polars()
        )
        assert len(result) == 5


class TestCrossTypeJoinDataIntegrity:
    """Verify that data values survive the cross-type coercion correctly."""

    def test_values_preserved_pandas(self, polars_df):
        """Ensure no data corruption during pandas → polars coercion."""
        pandas_right = pd.DataFrame({
            "id": [1, 2, 3],
            "score_label": ["low", "mid", "high"],
            "weight": [1.1, 2.2, 3.3],
        })
        result = (
            relation(polars_df)
            .join(pandas_right, on="id", how="inner")
            .sort("id")
            .to_polars()
        )
        assert result["score_label"].to_list() == ["low", "mid", "high"]
        assert result["weight"].to_list() == pytest.approx([1.1, 2.2, 3.3])

    def test_values_preserved_pyarrow(self, polars_df):
        """Ensure no data corruption during pyarrow → polars coercion."""
        pa_right = pa.table({
            "id": [1, 2, 3],
            "score_label": ["low", "mid", "high"],
            "weight": [1.1, 2.2, 3.3],
        })
        result = (
            relation(polars_df)
            .join(pa_right, on="id", how="inner")
            .sort("id")
            .to_polars()
        )
        assert result["score_label"].to_list() == ["low", "mid", "high"]
        assert result["weight"].to_list() == pytest.approx([1.1, 2.2, 3.3])
