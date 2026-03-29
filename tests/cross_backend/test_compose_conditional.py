"""Cross-backend tests for conditional fluent composition."""

import pytest
import mountainash_expressions as ma


ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestComposeConditional:
    """Test when/then/otherwise with composed expressions."""

    def test_conditional_string_transform(self, backend_name, backend_factory, select_and_extract):
        """when(score >= 70) then uppercase name, else keep."""
        data = {"score": [85, 45, 70], "name": ["alice", "bob", "carol"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.when(ma.col("score").ge(70)).then(
            ma.col("name").str.upper()
        ).otherwise(ma.col("name"))

        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == ["ALICE", "bob", "CAROL"], f"[{backend_name}] got {actual}"

    def test_conditional_arithmetic(self, backend_name, backend_factory, select_and_extract):
        """when(a > 0) then a * 2, else 0."""
        data = {"a": [5, -3, 10, 0]}
        df = backend_factory.create(data, backend_name)

        expr = ma.when(ma.col("a").gt(0)).then(
            ma.col("a") * 2
        ).otherwise(ma.lit(0))

        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == [10, 0, 20, 0], f"[{backend_name}] got {actual}"

    def test_conditional_null_handling(self, backend_name, backend_factory, select_and_extract):
        """when(x is null) then -1, else x."""
        data = {"x": [10, None, 30, None]}
        df = backend_factory.create(data, backend_name)

        expr = ma.when(ma.col("x").is_null()).then(
            ma.lit(-1)
        ).otherwise(ma.col("x"))

        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == [10, -1, 30, -1], f"[{backend_name}] got {actual}"

    def test_conditional_composed_condition(self, backend_name, backend_factory, select_and_extract):
        """when(a > 0 AND b > 0) then a + b, else 0."""
        data = {"a": [5, -3, 10, 0], "b": [2, 4, -1, 5]}
        df = backend_factory.create(data, backend_name)

        expr = ma.when(
            ma.col("a").gt(0).and_(ma.col("b").gt(0))
        ).then(
            ma.col("a") + ma.col("b")
        ).otherwise(ma.lit(0))

        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        # Row 0: 5>0 AND 2>0 -> 7
        # Row 1: -3>0 -> no -> 0
        # Row 2: 10>0 AND -1>0 -> no -> 0
        # Row 3: 0>0 -> no -> 0
        assert actual == [7, 0, 0, 0], f"[{backend_name}] got {actual}"
