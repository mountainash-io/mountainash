"""Cross-backend integration tests: mountainash expressions inside relational operations."""
from __future__ import annotations

import polars as pl
import pandas as pd
import narwhals as nw
import ibis
import pytest

from mountainash import col, lit, when, coalesce, greatest, least
from mountainash.relations import relation


ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals-polars",
    "narwhals-pandas",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]

SAMPLE_DATA = {
    "id": [1, 2, 3, 4, 5],
    "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
    "category": ["A", "B", "A", "C", "B"],
    "value": [100.5, 200.7, 300.9, 400.2, 500.8],
    "score": [85, 92, 78, 95, 88],
    "active": [True, False, True, True, False],
}


# ===========================================================================
# 1. Filter with mountainash expressions
# ===========================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestFilterWithExpressions:
    def _df(self, backend_name, backend_factory):
        return backend_factory.create(SAMPLE_DATA, backend_name)

    def test_simple_comparison(self, backend_name, backend_factory):
        df = self._df(backend_name, backend_factory)
        result = relation(df).filter(col("score").gt(85)).sort("name").to_dict()
        assert set(result["name"]) == {"Bob", "Diana", "Eve"}, f"[{backend_name}]"

    def test_less_than(self, backend_name, backend_factory):
        df = self._df(backend_name, backend_factory)
        result = relation(df).filter(col("value").lt(250)).sort("name").to_dict()
        assert set(result["name"]) == {"Alice", "Bob"}, f"[{backend_name}]"

    def test_equal(self, backend_name, backend_factory):
        df = self._df(backend_name, backend_factory)
        result = relation(df).filter(col("name").eq("Charlie")).to_dict()
        assert len(result["name"]) == 1, f"[{backend_name}]"
        assert result["name"][0] == "Charlie", f"[{backend_name}]"

    def test_not_equal(self, backend_name, backend_factory):
        df = self._df(backend_name, backend_factory)
        result = relation(df).filter(col("category").ne("A")).sort("name").to_dict()
        assert set(result["name"]) == {"Bob", "Diana", "Eve"}, f"[{backend_name}]"

    def test_ge_le(self, backend_name, backend_factory):
        df = self._df(backend_name, backend_factory)
        result = (
            relation(df)
            .filter(col("score").ge(85))
            .filter(col("score").le(92))
            .sort("name")
            .to_dict()
        )
        assert set(result["name"]) == {"Alice", "Bob", "Eve"}, f"[{backend_name}]"

    def test_compound_predicate_and(self, backend_name, backend_factory):
        df = self._df(backend_name, backend_factory)
        result = (
            relation(df)
            .filter(col("score").gt(80).and_(col("active").eq(True)))
            .sort("name")
            .to_dict()
        )
        assert set(result["name"]) == {"Alice", "Diana"}, f"[{backend_name}]"

    def test_compound_predicate_or(self, backend_name, backend_factory):
        df = self._df(backend_name, backend_factory)
        result = (
            relation(df)
            .filter(col("score").gt(90).or_(col("value").lt(150)))
            .sort("name")
            .to_dict()
        )
        assert set(result["name"]) == {"Alice", "Bob", "Diana"}, f"[{backend_name}]"

    def test_multiple_filter_predicates(self, backend_name, backend_factory):
        df = self._df(backend_name, backend_factory)
        result = (
            relation(df)
            .filter(col("score").ge(80), col("active").eq(True))
            .sort("name")
            .to_dict()
        )
        assert set(result["name"]) == {"Alice", "Diana"}, f"[{backend_name}]"

    def test_filter_with_literal(self, backend_name, backend_factory):
        df = self._df(backend_name, backend_factory)
        result = (
            relation(df)
            .filter(col("score").gt(lit(90)))
            .sort("name")
            .to_dict()
        )
        assert set(result["name"]) == {"Bob", "Diana"}, f"[{backend_name}]"


# ===========================================================================
# 2. with_columns using mountainash expressions
# ===========================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWithColumnsExpressions:
    def _df(self, backend_name, backend_factory):
        return backend_factory.create(SAMPLE_DATA, backend_name)

    def test_arithmetic_mul(self, backend_name, backend_factory):
        df = self._df(backend_name, backend_factory)
        result = (
            relation(df)
            .with_columns(col("value").mul(2).name.alias("double_value"))
            .sort("id")
            .to_dict()
        )
        assert "double_value" in result, f"[{backend_name}]"
        expected = [v * 2 for v in [100.5, 200.7, 300.9, 400.2, 500.8]]
        assert result["double_value"] == pytest.approx(expected, rel=1e-6), f"[{backend_name}]"

    def test_arithmetic_add(self, backend_name, backend_factory):
        df = self._df(backend_name, backend_factory)
        result = (
            relation(df)
            .with_columns(col("score").add(10).name.alias("score_plus_10"))
            .sort("id")
            .to_dict()
        )
        assert result["score_plus_10"] == [95, 102, 88, 105, 98], f"[{backend_name}]"

    def test_arithmetic_sub(self, backend_name, backend_factory):
        df = self._df(backend_name, backend_factory)
        result = (
            relation(df)
            .with_columns(col("score").sub(col("id")).name.alias("score_minus_id"))
            .sort("id")
            .to_dict()
        )
        assert result["score_minus_id"] == [84, 90, 75, 91, 83], f"[{backend_name}]"

    def test_string_upper(self, backend_name, backend_factory):
        df = self._df(backend_name, backend_factory)
        result = (
            relation(df)
            .with_columns(col("name").str.upper().name.alias("upper_name"))
            .sort("id")
            .to_dict()
        )
        assert result["upper_name"] == ["ALICE", "BOB", "CHARLIE", "DIANA", "EVE"], f"[{backend_name}]"

    def test_string_lower(self, backend_name, backend_factory):
        df = self._df(backend_name, backend_factory)
        result = (
            relation(df)
            .with_columns(col("name").str.lower().name.alias("lower_name"))
            .sort("id")
            .to_dict()
        )
        assert result["lower_name"] == ["alice", "bob", "charlie", "diana", "eve"], f"[{backend_name}]"

    def test_multiple_expressions(self, backend_name, backend_factory):
        df = self._df(backend_name, backend_factory)
        result = (
            relation(df)
            .with_columns(
                col("value").mul(2).name.alias("double_value"),
                col("name").str.upper().name.alias("upper_name"),
            )
            .to_dict()
        )
        assert "double_value" in result, f"[{backend_name}]"
        assert "upper_name" in result, f"[{backend_name}]"


# ===========================================================================
# 3. select with mountainash expressions
# ===========================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestSelectWithExpressions:
    def _df(self, backend_name, backend_factory):
        return backend_factory.create(SAMPLE_DATA, backend_name)

    def test_select_with_computed(self, backend_name, backend_factory):
        df = self._df(backend_name, backend_factory)
        result = (
            relation(df)
            .select(col("name"), col("value").mul(2).name.alias("double_val"))
            .sort("name")
            .to_dict()
        )
        assert set(result.keys()) == {"name", "double_val"}, f"[{backend_name}]"
        assert len(result["name"]) == 5, f"[{backend_name}]"

    def test_select_mixed_string_and_ma(self, backend_name, backend_factory):
        df = self._df(backend_name, backend_factory)
        result = (
            relation(df)
            .select("id", col("name").str.upper().name.alias("upper_name"))
            .sort("id")
            .to_dict()
        )
        assert result["id"] == [1, 2, 3, 4, 5], f"[{backend_name}]"
        assert result["upper_name"] == ["ALICE", "BOB", "CHARLIE", "DIANA", "EVE"], f"[{backend_name}]"


# ===========================================================================
# 4. when/then/otherwise (conditional expressions)
# ===========================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWhenThenOtherwise:
    def _df(self, backend_name, backend_factory):
        return backend_factory.create(SAMPLE_DATA, backend_name)

    def test_simple_when_then_otherwise(self, backend_name, backend_factory):
        df = self._df(backend_name, backend_factory)
        result = (
            relation(df)
            .with_columns(
                when(col("score").gt(90))
                .then(lit("high"))
                .otherwise(lit("low"))
                .name.alias("tier")
            )
            .sort("id")
            .to_dict()
        )
        assert result["tier"] == ["low", "high", "low", "high", "low"], f"[{backend_name}]"

    def test_chained_when(self, backend_name, backend_factory):
        df = self._df(backend_name, backend_factory)
        result = (
            relation(df)
            .with_columns(
                when(col("score").gt(90)).then(lit("A"))
                .when(col("score").gt(80)).then(lit("B"))
                .otherwise(lit("C"))
                .name.alias("grade")
            )
            .sort("id")
            .to_dict()
        )
        assert result["grade"] == ["B", "A", "C", "A", "B"], f"[{backend_name}]"


# ===========================================================================
# 5. coalesce, greatest, least
# ===========================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestHorizontalFunctions:
    def _df(self, backend_name, backend_factory):
        return backend_factory.create(SAMPLE_DATA, backend_name)

    def test_greatest(self, backend_name, backend_factory):
        if backend_name in ("pandas", "narwhals-pandas"):
            pytest.xfail(
                f"[{backend_name}] greatest() with a literal scalar does not clamp "
                "correctly on pandas/narwhals-pandas — nw.max_horizontal returns "
                "original column values unchanged when mixed with a scalar literal"
            )
        df = self._df(backend_name, backend_factory)
        result = (
            relation(df)
            .with_columns(
                greatest(col("score"), lit(90)).name.alias("at_least_90")
            )
            .sort("id")
            .to_dict()
        )
        assert result["at_least_90"] == [90, 92, 90, 95, 90], f"[{backend_name}]"

    def test_least(self, backend_name, backend_factory):
        if backend_name in ("pandas", "narwhals-pandas"):
            pytest.xfail(
                f"[{backend_name}] least() with a literal scalar does not clamp "
                "correctly on pandas/narwhals-pandas — nw.min_horizontal returns "
                "original column values unchanged when mixed with a scalar literal"
            )
        df = self._df(backend_name, backend_factory)
        result = (
            relation(df)
            .with_columns(
                least(col("score"), lit(90)).name.alias("capped_at_90")
            )
            .sort("id")
            .to_dict()
        )
        assert result["capped_at_90"] == [85, 90, 78, 90, 88], f"[{backend_name}]"

    def test_coalesce_with_nulls(self, backend_name, backend_factory):
        data = {
            "id": [1, 2, 3, 4, 5],
            "name": ["Alice", "Bob", "Charlie", None, None],
        }
        df = backend_factory.create(data, backend_name)
        result = (
            relation(df)
            .with_columns(
                coalesce(col("name"), lit("Unknown")).name.alias("name_or_default")
            )
            .sort("id")
            .to_dict()
        )
        assert result["name_or_default"] == ["Alice", "Bob", "Charlie", "Unknown", "Unknown"], f"[{backend_name}]"


# ===========================================================================
# 6. Full pipeline combining relations and expressions
# ===========================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestFullPipeline:
    def _df(self, backend_name, backend_factory):
        return backend_factory.create(SAMPLE_DATA, backend_name)

    def test_filter_with_columns_sort(self, backend_name, backend_factory):
        df = self._df(backend_name, backend_factory)
        result = (
            relation(df)
            .filter(col("active").eq(True))
            .with_columns(
                col("value").mul(1.1).name.alias("adjusted_value"),
                col("name").str.upper().name.alias("upper_name"),
            )
            .sort("upper_name")
            .to_dict()
        )
        assert len(result["upper_name"]) == 3, f"[{backend_name}]"
        assert result["upper_name"] == ["ALICE", "CHARLIE", "DIANA"], f"[{backend_name}]"
        assert "adjusted_value" in result, f"[{backend_name}]"

    def test_filter_select_head(self, backend_name, backend_factory):
        df = self._df(backend_name, backend_factory)
        result = (
            relation(df)
            .filter(col("score").ge(85))
            .sort("score", descending=True)
            .head(2)
            .select("name", "score")
            .to_dict()
        )
        assert set(result.keys()) == {"name", "score"}, f"[{backend_name}]"
        assert len(result["name"]) == 2, f"[{backend_name}]"
        assert result["name"] == ["Diana", "Bob"], f"[{backend_name}]"

    def test_with_columns_then_filter(self, backend_name, backend_factory):
        df = self._df(backend_name, backend_factory)
        result = (
            relation(df)
            .with_columns(col("value").mul(2).name.alias("double_value"))
            .filter(col("double_value").gt(lit(500)))
            .sort("name")
            .to_dict()
        )
        assert set(result["name"]) == {"Charlie", "Diana", "Eve"}, f"[{backend_name}]"


# ===========================================================================
# 7. Mixing native and mountainash expressions
# ===========================================================================


def _native_col_gt(backend_name, col_name, value):
    """Build a native backend expression: col_name > value."""
    if backend_name == "polars":
        return pl.col(col_name) > value
    elif backend_name.startswith("narwhals") or backend_name == "pandas":
        return nw.col(col_name) > value
    elif backend_name.startswith("ibis-"):
        return getattr(ibis._, col_name) > value
    raise ValueError(f"Unknown backend: {backend_name}")


def _native_upper(backend_name, col_name, alias):
    """Build a native backend expression: upper(col_name).alias(alias)."""
    if backend_name == "polars":
        return pl.col(col_name).str.to_uppercase().alias(alias)
    elif backend_name.startswith("narwhals") or backend_name == "pandas":
        return nw.col(col_name).str.to_uppercase().alias(alias)
    elif backend_name.startswith("ibis-"):
        return getattr(ibis._, col_name).upper().name(alias)
    raise ValueError(f"Unknown backend: {backend_name}")


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestMixedNativeAndMa:
    """Test mixing native backend expressions with mountainash expressions."""

    def _df(self, backend_name, backend_factory):
        return backend_factory.create(SAMPLE_DATA, backend_name)

    def test_native_filter_ma_with_columns(self, backend_name, backend_factory):
        df = self._df(backend_name, backend_factory)
        native_filter = _native_col_gt(backend_name, "score", 80)
        result = (
            relation(df)
            .filter(native_filter)
            .with_columns(col("name").str.upper().name.alias("upper_name"))
            .sort("name")
            .to_dict()
        )
        assert "upper_name" in result, f"[{backend_name}]"
        assert len(result["name"]) == 4, f"[{backend_name}]"

    def test_ma_filter_native_with_columns(self, backend_name, backend_factory):
        df = self._df(backend_name, backend_factory)
        native_upper = _native_upper(backend_name, "name", "upper_name")
        result = (
            relation(df)
            .filter(col("score").gt(80))
            .with_columns(native_upper)
            .sort("name")
            .to_dict()
        )
        assert "upper_name" in result, f"[{backend_name}]"
        assert len(result["name"]) == 4, f"[{backend_name}]"


class TestMixedExpressionMismatch:
    """Test that wrong-backend native expressions raise at compile time."""

    def test_polars_expr_on_narwhals_raises(self, backend_factory):
        df = backend_factory.create({"score": [85, 92]}, "pandas")
        rel = relation(df).filter(pl.col("score") > 80)
        with pytest.raises(TypeError):
            rel.to_pandas()

    def test_narwhals_expr_on_polars_raises(self, backend_factory):
        df = backend_factory.create({"score": [85, 92]}, "polars")
        rel = relation(df).filter(nw.col("score") > 80)
        with pytest.raises(TypeError):
            rel.to_polars()

    def test_polars_expr_on_ibis_raises(self, backend_factory):
        df = backend_factory.create({"score": [85, 92]}, "ibis-duckdb")
        rel = relation(df).filter(pl.col("score") > 80)
        with pytest.raises((TypeError, Exception)):
            rel.to_polars()

    def test_ibis_expr_on_polars_raises(self, backend_factory):
        df = backend_factory.create({"score": [85, 92]}, "polars")
        rel = relation(df).filter(ibis._.score > 80)
        with pytest.raises(TypeError):
            rel.to_polars()


# ===========================================================================
# 8. Narwhals backend with mountainash expressions (stays as-is)
# ===========================================================================


@pytest.fixture
def pandas_df():
    return pd.DataFrame(SAMPLE_DATA)


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
