"""Cross-type join tests for the Relation API.

Tests that relation(polars_df).join(pandas_df, on="id") works — the visitor
coerces the right-side DataFrame to match the left side's backend type.
Also tests with PyArrow and dict inputs.
"""

from __future__ import annotations

import ibis
import narwhals as nw
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


class TestPolarsJoinListOfDicts:
    """Polars left side, list[dict] right side (design spec Revision 2
    finding 5 -- a pre-existing gap in cross-type-joins.md's own documented
    contract, closed here since this item already touches this function)."""

    def test_inner_join_list_of_dicts(self, polars_df):
        list_right = [{"id": 2, "extra": "m"}, {"id": 4, "extra": "n"}]
        result = relation(polars_df).join(list_right, on="id", how="inner").to_polars()
        assert isinstance(result, pl.DataFrame)
        assert sorted(zip(result["id"].to_list(), result["extra"].to_list())) == [
            (2, "m"),
            (4, "n"),
        ]

    def test_left_join_list_of_dicts(self, polars_df):
        list_right = [{"id": 1, "extra": "a"}, {"id": 3, "extra": "b"}]
        result = relation(polars_df).join(list_right, on="id", how="left").to_polars()
        assert isinstance(result, pl.DataFrame)
        assert "extra" in result.columns
        # Exact null placement for unmatched left rows (id 2/4/5), same
        # style as the pre-existing TestPolarsJoinPandas left-join test.
        extras = result.sort("id")["extra"].to_list()
        assert extras == ["a", None, "b", None, None]


class TestPolarsJoinFallbackPaths:
    """Design spec testing plan #19: the two pre-existing Polars-branch
    fallbacks -- the .to_pyarrow() duck-type path (an Ibis Table) and the
    generic nw.from_native() path (a Narwhals frame) -- exercised end-to-
    end. These are unchanged code paths, so they are GREEN-before/GREEN-
    after regression coverage guarding against Task 2's edits accidentally
    perturbing them."""

    def test_ibis_table_right_uses_to_pyarrow_fallback(self, polars_df):
        con = ibis.duckdb.connect()
        ibis_right = con.create_table("ib", {"id": [2, 3], "extra": ["m", "n"]})
        result = relation(polars_df).join(ibis_right, on="id", how="inner").to_polars()
        assert isinstance(result, pl.DataFrame)
        assert sorted(zip(result["id"].to_list(), result["extra"].to_list())) == [
            (2, "m"),
            (3, "n"),
        ]

    def test_narwhals_frame_right_uses_native_fallback(self, polars_df):
        nw_right = nw.from_native(
            pd.DataFrame({"id": [2, 3], "extra": ["m", "n"]}), eager_only=True
        )
        result = relation(polars_df).join(nw_right, on="id", how="inner").to_polars()
        assert isinstance(result, pl.DataFrame)
        assert sorted(zip(result["id"].to_list(), result["extra"].to_list())) == [
            (2, "m"),
            (3, "n"),
        ]


class TestPolarsJoinScalarListRejected:
    """Design spec Revision 2 finding 4: a scalar (non-dict) list right-hand
    value must NOT silently take the dict-sequence fast path -- it falls
    through to the generic narwhals fallback, which raises its own clean
    TypeError rather than producing a meaningless one-column frame.

    GREEN-before/GREEN-after: the pre-existing Polars branch ALREADY rejects
    a scalar list with this exact message (its generic fallback path), so
    this is a characterization guard against Task 2's narrowed-predicate
    edit accidentally BROADENING to accept scalar lists -- NOT a RED-first
    test."""

    def test_scalar_list_raises_clean_typeerror(self, polars_df):
        with pytest.raises(TypeError, match="Cannot coerce list to Polars"):
            relation(polars_df).join([1, 2, 3], on="id", how="inner").to_polars()
