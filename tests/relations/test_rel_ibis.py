"""Ibis integration tests for the Relation API.

Exercises the full pipeline: relation(ibis_table) -> operations -> result.
Uses ibis.polars.connect() as the in-memory backend.
"""

from __future__ import annotations

import pytest
import ibis
import polars as pl

from mountainash.relations import relation

# Import backends to trigger registration of relation systems and expression systems.
import mountainash.relations.backends.relation_systems.ibis  # noqa: F401
import mountainash.expressions.backends.expression_systems.ibis  # noqa: F401


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def ibis_con():
    """Shared Ibis Polars connection for all tests in a function."""
    return ibis.polars.connect()


@pytest.fixture
def sample_data() -> pl.DataFrame:
    """Base sample data as a Polars DataFrame."""
    return pl.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "category": ["A", "B", "A", "C", "B"],
        "score": [90, 80, 95, 70, 85],
        "active": [True, False, True, True, False],
    })


@pytest.fixture
def join_data() -> pl.DataFrame:
    """Data for join tests."""
    return pl.DataFrame({
        "id": [1, 2, 3, 6],
        "department": ["Engineering", "Sales", "Engineering", "Marketing"],
    })


@pytest.fixture
def ibis_table(ibis_con, sample_data: pl.DataFrame):
    """Create an Ibis table using the Polars backend (in-memory)."""
    return ibis_con.create_table("test_data", sample_data)


@pytest.fixture
def ibis_join_table(ibis_con, join_data: pl.DataFrame):
    """Create an Ibis join table on the same connection."""
    return ibis_con.create_table("join_data", join_data)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_polars(rel) -> pl.DataFrame:
    """Execute a Relation and return a Polars DataFrame for assertions."""
    return rel.to_polars()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSelect:
    def test_select_columns(self, ibis_table):
        result = _to_polars(relation(ibis_table).select("id", "name"))
        assert result.columns == ["id", "name"]
        assert result.shape[0] == 5

    def test_select_single_column(self, ibis_table):
        result = _to_polars(relation(ibis_table).select("score"))
        assert result.columns == ["score"]
        assert result["score"].to_list() == [90, 80, 95, 70, 85]


class TestDrop:
    def test_drop_column(self, ibis_table):
        result = _to_polars(relation(ibis_table).drop("active"))
        assert "active" not in result.columns
        assert len(result.columns) == 4

    def test_drop_multiple_columns(self, ibis_table):
        result = _to_polars(relation(ibis_table).drop("active", "category"))
        assert "active" not in result.columns
        assert "category" not in result.columns
        assert len(result.columns) == 3


class TestRename:
    @pytest.mark.xfail(
        reason="Ibis backend rename mapping is inverted: Ibis expects {new: old} "
               "but the Relation API passes {old: new}. See relsys_ib_project.py.",
        strict=True,
    )
    def test_rename_columns(self, ibis_table):
        result = _to_polars(relation(ibis_table).rename({"name": "full_name", "score": "grade"}))
        assert "full_name" in result.columns
        assert "grade" in result.columns
        assert "name" not in result.columns
        assert "score" not in result.columns
        assert result.shape[0] == 5


class TestFilter:
    def test_filter_with_ibis_expression(self, ibis_table):
        result = _to_polars(relation(ibis_table).filter(ibis._.score > 85))
        assert result.shape[0] == 2
        assert set(result["name"].to_list()) == {"Alice", "Charlie"}

    def test_filter_with_equality(self, ibis_table):
        result = _to_polars(relation(ibis_table).filter(ibis._.category == "A"))
        assert result.shape[0] == 2
        assert all(c == "A" for c in result["category"].to_list())

    def test_filter_chained(self, ibis_table):
        result = _to_polars(
            relation(ibis_table)
            .filter(ibis._.score > 70)
            .filter(ibis._.active == True)  # noqa: E712
        )
        assert result.shape[0] == 2
        assert set(result["name"].to_list()) == {"Alice", "Charlie"}


class TestSort:
    def test_sort_ascending(self, ibis_table):
        result = _to_polars(relation(ibis_table).sort("score"))
        scores = result["score"].to_list()
        assert scores == sorted(scores)

    def test_sort_descending(self, ibis_table):
        result = _to_polars(relation(ibis_table).sort("score", descending=True))
        scores = result["score"].to_list()
        assert scores == sorted(scores, reverse=True)


class TestHead:
    def test_head(self, ibis_table):
        result = _to_polars(relation(ibis_table).head(3))
        assert result.shape[0] == 3

    def test_head_default(self, ibis_table):
        result = _to_polars(relation(ibis_table).head())
        assert result.shape[0] == 5  # Only 5 rows, default head is 5


class TestJoinInner:
    def test_inner_join(self, ibis_table, ibis_join_table):
        result = _to_polars(
            relation(ibis_table).join(relation(ibis_join_table), on="id")
        )
        # Inner join: only ids 1, 2, 3 match
        assert result.shape[0] == 3
        assert "department" in result.columns


class TestGroupByAgg:
    def test_group_by_with_ibis_agg(self, ibis_table):
        result = _to_polars(
            relation(ibis_table)
            .group_by("category")
            .agg(ibis._.score.mean().name("avg_score"))
        )
        assert result.shape[0] == 3  # A, B, C
        assert "avg_score" in result.columns
        assert "category" in result.columns

    def test_group_by_count(self, ibis_table):
        result = _to_polars(
            relation(ibis_table)
            .group_by("category")
            .agg(ibis._.id.count().name("count"))
        )
        assert result.shape[0] == 3
        # Sort for deterministic assertion
        result = result.sort("category")
        counts = result["count"].to_list()
        assert counts == [2, 2, 1]  # A: 2, B: 2, C: 1


class TestUnique:
    def test_unique_on_column(self, ibis_table):
        result = _to_polars(relation(ibis_table).unique("category"))
        assert result.shape[0] == 3  # A, B, C
        assert set(result["category"].to_list()) == {"A", "B", "C"}

    def test_distinct_all_columns(self, ibis_table):
        result = _to_polars(relation(ibis_table).unique())
        # All rows are already unique
        assert result.shape[0] == 5


class TestPipeline:
    def test_filter_sort_head(self, ibis_table):
        """Chain filter -> sort -> head."""
        result = _to_polars(
            relation(ibis_table)
            .filter(ibis._.score > 70)
            .sort("score", descending=True)
            .head(3)
        )
        assert result.shape[0] == 3
        scores = result["score"].to_list()
        assert scores == sorted(scores, reverse=True)
        assert all(s > 70 for s in scores)

    @pytest.mark.xfail(
        reason="Ibis backend rename mapping is inverted: Ibis expects {new: old} "
               "but the Relation API passes {old: new}. See relsys_ib_project.py.",
        strict=True,
    )
    def test_select_rename_sort(self, ibis_table):
        """Chain select -> rename -> sort."""
        result = _to_polars(
            relation(ibis_table)
            .select("id", "name", "score")
            .rename({"score": "grade"})
            .sort("grade")
        )
        assert result.columns == ["id", "name", "grade"]
        grades = result["grade"].to_list()
        assert grades == sorted(grades)

    def test_filter_group_by_agg(self, ibis_table):
        """Chain filter -> group_by -> agg."""
        result = _to_polars(
            relation(ibis_table)
            .filter(ibis._.active == True)  # noqa: E712
            .group_by("category")
            .agg(ibis._.score.max().name("max_score"))
        )
        # Active rows: Alice(A,90), Charlie(A,95), Diana(C,70)
        assert result.shape[0] == 2  # A and C
        result = result.sort("category")
        assert result["max_score"].to_list() == [95, 70]
