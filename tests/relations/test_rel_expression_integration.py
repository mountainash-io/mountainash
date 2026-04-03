"""Integration tests: mountainash expressions inside relational operations.

These tests exercise the full stack: mountainash expression API objects
(ma.col, ma.lit, ma.when, etc.) used inside Relation operations (filter,
with_columns, select, group_by+agg).  The key integration point is
``UnifiedRelationVisitor._compile_expression()``, which must detect
``BaseExpressionAPI`` objects, extract their ``._node``, and compile via
the expression visitor.
"""

from __future__ import annotations

import polars as pl
import pandas as pd
import pytest

import mountainash as ma
from mountainash import col, lit, when, coalesce, greatest, least
from mountainash.relations import relation

# Trigger backend registration (side-effect imports)
import mountainash.relations.backends.relation_systems.narwhals  # noqa: F401
import mountainash.expressions.backends  # noqa: F401


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def polars_df():
    return pl.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
            "category": ["A", "B", "A", "C", "B"],
            "value": [100.5, 200.7, 300.9, 400.2, 500.8],
            "score": [85, 92, 78, 95, 88],
            "active": [True, False, True, True, False],
        }
    )


@pytest.fixture
def pandas_df():
    return pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
            "category": ["A", "B", "A", "C", "B"],
            "value": [100.5, 200.7, 300.9, 400.2, 500.8],
            "score": [85, 92, 78, 95, 88],
            "active": [True, False, True, True, False],
        }
    )


# ===========================================================================
# 1. Filter with mountainash expressions (Polars)
# ===========================================================================


class TestFilterWithExpressions:
    """Test mountainash expressions as filter predicates."""

    def test_simple_comparison(self, polars_df):
        result = relation(polars_df).filter(col("score").gt(85)).to_polars()
        assert isinstance(result, pl.DataFrame)
        # score > 85: Bob(92), Diana(95), Eve(88)
        assert len(result) == 3
        assert set(result["name"].to_list()) == {"Bob", "Diana", "Eve"}

    def test_less_than(self, polars_df):
        result = relation(polars_df).filter(col("value").lt(250)).to_polars()
        # value < 250: Alice(100.5), Bob(200.7)
        assert len(result) == 2
        assert set(result["name"].to_list()) == {"Alice", "Bob"}

    def test_equal(self, polars_df):
        result = relation(polars_df).filter(col("name").eq("Charlie")).to_polars()
        assert len(result) == 1
        assert result["name"][0] == "Charlie"

    def test_not_equal(self, polars_df):
        result = relation(polars_df).filter(col("category").ne("A")).to_polars()
        # category != A: Bob(B), Diana(C), Eve(B)
        assert len(result) == 3
        assert set(result["name"].to_list()) == {"Bob", "Diana", "Eve"}

    def test_ge_le(self, polars_df):
        result = (
            relation(polars_df)
            .filter(col("score").ge(85))
            .filter(col("score").le(92))
            .to_polars()
        )
        # 85 <= score <= 92: Alice(85), Bob(92), Eve(88)
        assert len(result) == 3
        assert set(result["name"].to_list()) == {"Alice", "Bob", "Eve"}

    def test_compound_predicate_and(self, polars_df):
        result = (
            relation(polars_df)
            .filter(col("score").gt(80).and_(col("active").eq(True)))
            .to_polars()
        )
        # score > 80 AND active: Alice(85,T), Diana(95,T)
        assert len(result) == 2
        assert set(result["name"].to_list()) == {"Alice", "Diana"}

    def test_compound_predicate_or(self, polars_df):
        result = (
            relation(polars_df)
            .filter(col("score").gt(90).or_(col("value").lt(150)))
            .to_polars()
        )
        # score > 90: Bob(92), Diana(95)
        # value < 150: Alice(100.5)
        # union: Alice, Bob, Diana
        assert len(result) == 3
        assert set(result["name"].to_list()) == {"Alice", "Bob", "Diana"}

    def test_multiple_filter_predicates(self, polars_df):
        """Multiple predicates passed to filter() — each becomes a chained FilterRelNode."""
        result = (
            relation(polars_df)
            .filter(col("score").ge(80), col("active").eq(True))
            .to_polars()
        )
        # score >= 80 AND active: Alice(85,T), Diana(95,T)
        assert len(result) == 2
        assert set(result["name"].to_list()) == {"Alice", "Diana"}

    def test_filter_with_literal(self, polars_df):
        """Filter comparing column to a literal value via lit()."""
        result = (
            relation(polars_df)
            .filter(col("score").gt(lit(90)))
            .to_polars()
        )
        # score > 90: Bob(92), Diana(95)
        assert len(result) == 2
        assert set(result["name"].to_list()) == {"Bob", "Diana"}


# ===========================================================================
# 2. with_columns using mountainash expressions (Polars)
# ===========================================================================


class TestWithColumnsExpressions:
    """Test mountainash expressions in with_columns()."""

    def test_arithmetic_mul(self, polars_df):
        result = (
            relation(polars_df)
            .with_columns(col("value").mul(2).name.alias("double_value"))
            .to_polars()
        )
        assert "double_value" in result.columns
        expected = [v * 2 for v in [100.5, 200.7, 300.9, 400.2, 500.8]]
        assert result["double_value"].to_list() == pytest.approx(expected, rel=1e-6)

    def test_arithmetic_add(self, polars_df):
        result = (
            relation(polars_df)
            .with_columns(col("score").add(10).name.alias("score_plus_10"))
            .to_polars()
        )
        assert "score_plus_10" in result.columns
        assert result["score_plus_10"].to_list() == [95, 102, 88, 105, 98]

    def test_arithmetic_sub(self, polars_df):
        result = (
            relation(polars_df)
            .with_columns(col("score").sub(col("id")).name.alias("score_minus_id"))
            .to_polars()
        )
        assert "score_minus_id" in result.columns
        assert result["score_minus_id"].to_list() == [84, 90, 75, 91, 83]

    def test_string_upper(self, polars_df):
        result = (
            relation(polars_df)
            .with_columns(col("name").str.upper().name.alias("upper_name"))
            .to_polars()
        )
        assert "upper_name" in result.columns
        assert result["upper_name"].to_list() == [
            "ALICE", "BOB", "CHARLIE", "DIANA", "EVE",
        ]

    def test_string_lower(self, polars_df):
        result = (
            relation(polars_df)
            .with_columns(col("name").str.lower().name.alias("lower_name"))
            .to_polars()
        )
        assert "lower_name" in result.columns
        assert result["lower_name"].to_list() == [
            "alice", "bob", "charlie", "diana", "eve",
        ]

    def test_multiple_expressions(self, polars_df):
        result = (
            relation(polars_df)
            .with_columns(
                col("value").mul(2).name.alias("double_value"),
                col("name").str.upper().name.alias("upper_name"),
            )
            .to_polars()
        )
        assert "double_value" in result.columns
        assert "upper_name" in result.columns


# ===========================================================================
# 3. select with mountainash expressions
# ===========================================================================


class TestSelectWithExpressions:
    """Test mountainash expressions in select()."""

    def test_select_with_computed(self, polars_df):
        result = (
            relation(polars_df)
            .select(col("name"), col("value").mul(2).name.alias("double_val"))
            .to_polars()
        )
        assert result.columns == ["name", "double_val"]
        assert len(result) == 5
        assert result["double_val"].to_list() == pytest.approx(
            [201.0, 401.4, 601.8, 800.4, 1001.6], rel=1e-6
        )

    def test_select_mixed_native_and_ma(self, polars_df):
        """Mix of native string columns and mountainash expressions in select."""
        result = (
            relation(polars_df)
            .select("id", col("name").str.upper().name.alias("upper_name"))
            .to_polars()
        )
        assert result.columns == ["id", "upper_name"]
        assert result["id"].to_list() == [1, 2, 3, 4, 5]
        assert result["upper_name"].to_list() == [
            "ALICE", "BOB", "CHARLIE", "DIANA", "EVE",
        ]


# ===========================================================================
# 4. when/then/otherwise (conditional expressions)
# ===========================================================================


class TestWhenThenOtherwise:
    """Test conditional expressions inside relational operations."""

    def test_simple_when_then_otherwise(self, polars_df):
        result = (
            relation(polars_df)
            .with_columns(
                when(col("score").gt(90))
                .then(lit("high"))
                .otherwise(lit("low"))
                .name.alias("tier")
            )
            .to_polars()
        )
        assert "tier" in result.columns
        # score > 90: Bob(92)=high, Diana(95)=high; rest=low
        tiers = result.sort("id")["tier"].to_list()
        assert tiers == ["low", "high", "low", "high", "low"]

    def test_chained_when(self, polars_df):
        result = (
            relation(polars_df)
            .with_columns(
                when(col("score").gt(90)).then(lit("A"))
                .when(col("score").gt(80)).then(lit("B"))
                .otherwise(lit("C"))
                .name.alias("grade")
            )
            .to_polars()
        )
        assert "grade" in result.columns
        grades = result.sort("id")["grade"].to_list()
        # Alice(85)->B, Bob(92)->A, Charlie(78)->C, Diana(95)->A, Eve(88)->B
        assert grades == ["B", "A", "C", "A", "B"]


# ===========================================================================
# 5. coalesce, greatest, least
# ===========================================================================


class TestHorizontalFunctions:
    """Test coalesce, greatest, least inside relational operations."""

    def test_greatest(self, polars_df):
        result = (
            relation(polars_df)
            .with_columns(
                greatest(col("score"), lit(90)).name.alias("at_least_90")
            )
            .to_polars()
        )
        assert "at_least_90" in result.columns
        vals = result.sort("id")["at_least_90"].to_list()
        # max(85,90)=90, max(92,90)=92, max(78,90)=90, max(95,90)=95, max(88,90)=90
        assert vals == [90, 92, 90, 95, 90]

    def test_least(self, polars_df):
        result = (
            relation(polars_df)
            .with_columns(
                least(col("score"), lit(90)).name.alias("capped_at_90")
            )
            .to_polars()
        )
        assert "capped_at_90" in result.columns
        vals = result.sort("id")["capped_at_90"].to_list()
        # min(85,90)=85, min(92,90)=90, min(78,90)=78, min(95,90)=90, min(88,90)=88
        assert vals == [85, 90, 78, 90, 88]

    def test_coalesce_with_nulls(self, polars_df):
        """Coalesce should return first non-null value."""
        df_with_nulls = polars_df.with_columns(
            pl.when(pl.col("id") > 3).then(None).otherwise(pl.col("name")).alias("name")
        )
        result = (
            relation(df_with_nulls)
            .with_columns(
                coalesce(col("name"), lit("Unknown")).name.alias("name_or_default")
            )
            .to_polars()
        )
        assert "name_or_default" in result.columns
        vals = result.sort("id")["name_or_default"].to_list()
        assert vals == ["Alice", "Bob", "Charlie", "Unknown", "Unknown"]


# ===========================================================================
# 6. Full pipeline combining relations and expressions
# ===========================================================================


class TestFullPipeline:
    """End-to-end pipeline tests combining relational and expression operations."""

    def test_filter_with_columns_sort(self, polars_df):
        """Pipeline: filter → with_columns → sort → to_polars."""
        result = (
            relation(polars_df)
            .filter(col("active").eq(True))
            .with_columns(
                col("value").mul(1.1).name.alias("adjusted_value"),
                col("name").str.upper().name.alias("upper_name"),
            )
            .sort("upper_name")
            .to_polars()
        )
        assert isinstance(result, pl.DataFrame)
        # active=True: Alice, Charlie, Diana
        assert len(result) == 3
        assert result["upper_name"].to_list() == ["ALICE", "CHARLIE", "DIANA"]
        assert "adjusted_value" in result.columns

    def test_filter_select_head(self, polars_df):
        """Pipeline: filter → select → head → to_polars."""
        result = (
            relation(polars_df)
            .filter(col("score").ge(85))
            .sort("score", descending=True)
            .head(2)
            .select("name", "score")
            .to_polars()
        )
        assert result.columns == ["name", "score"]
        assert len(result) == 2
        # Top 2 scores >= 85, sorted desc: Diana(95), Bob(92)
        assert result["name"].to_list() == ["Diana", "Bob"]

    def test_with_columns_then_filter(self, polars_df):
        """Pipeline: with_columns → filter on computed column."""
        result = (
            relation(polars_df)
            .with_columns(col("value").mul(2).name.alias("double_value"))
            .filter(col("double_value").gt(lit(500)))
            .to_polars()
        )
        # double_value > 500: Charlie(601.8), Diana(800.4), Eve(1001.6)
        assert len(result) == 3
        assert set(result["name"].to_list()) == {"Charlie", "Diana", "Eve"}


# ===========================================================================
# 7. Mixing native and mountainash expressions
# ===========================================================================


class TestMixedExpressions:
    """Test mixing native Polars expressions with mountainash expressions."""

    def test_native_filter_ma_with_columns(self, polars_df):
        """Native Polars filter, then mountainash with_columns."""
        result = (
            relation(polars_df)
            .filter(pl.col("score") > 80)
            .with_columns(col("name").str.upper().name.alias("upper_name"))
            .to_polars()
        )
        assert "upper_name" in result.columns
        # score > 80: Alice(85), Bob(92), Diana(95), Eve(88)
        assert len(result) == 4

    def test_ma_filter_native_with_columns(self, polars_df):
        """Mountainash filter, then native Polars with_columns."""
        result = (
            relation(polars_df)
            .filter(col("score").gt(80))
            .with_columns(pl.col("name").str.to_uppercase().alias("upper_name"))
            .to_polars()
        )
        assert "upper_name" in result.columns
        assert len(result) == 4


# ===========================================================================
# 8. Narwhals backend with mountainash expressions
# ===========================================================================


class TestNarwhalsBackendExpressions:
    """Test mountainash expressions with pandas input (Narwhals backend)."""

    def test_filter_simple(self, pandas_df):
        result = relation(pandas_df).filter(col("score").gt(85)).to_pandas()
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        assert set(result["name"].to_list()) == {"Bob", "Diana", "Eve"}

    def test_with_columns_arithmetic(self, pandas_df):
        result = (
            relation(pandas_df)
            .with_columns(col("value").mul(2).name.alias("double_value"))
            .to_pandas()
        )
        assert "double_value" in result.columns
        expected = [v * 2 for v in [100.5, 200.7, 300.9, 400.2, 500.8]]
        actual = result["double_value"].to_list()
        assert actual == pytest.approx(expected, rel=1e-6)

    def test_with_columns_string_upper(self, pandas_df):
        result = (
            relation(pandas_df)
            .with_columns(col("name").str.upper().name.alias("upper_name"))
            .to_pandas()
        )
        assert "upper_name" in result.columns
        assert result["upper_name"].to_list() == [
            "ALICE", "BOB", "CHARLIE", "DIANA", "EVE",
        ]

    def test_filter_and_select(self, pandas_df):
        result = (
            relation(pandas_df)
            .filter(col("active").eq(True))
            .select("name", "score")
            .to_pandas()
        )
        assert list(result.columns) == ["name", "score"]
        assert len(result) == 3

    def test_when_then_otherwise(self, pandas_df):
        result = (
            relation(pandas_df)
            .with_columns(
                when(col("score").gt(90))
                .then(lit("high"))
                .otherwise(lit("low"))
                .name.alias("tier")
            )
            .to_pandas()
        )
        assert "tier" in result.columns
