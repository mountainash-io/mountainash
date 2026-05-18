"""Cross-backend tests for cast operation behavior.

Validates that type casting produces correct values consistently across
all backends: Polars, Pandas, Narwhals, and Ibis (DuckDB, Polars, SQLite).

Uses canonical mountainash type strings ("i64", "string", "fp64", etc.)
instead of backend-specific types.
"""

import pytest
import math
import mountainash.expressions as ma


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
class TestCastToInteger:
    """Test casting to integer types."""

    def test_cast_float_to_int(self, backend_name, backend_factory, collect_expr):
        if backend_name == "ibis-duckdb":
            pytest.xfail(
                "DuckDB uses banker's rounding for float-to-int cast, not truncation."
            )
        data = {"value": [1.1, 2.9, 3.5, -1.7, -2.3]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("i64")
        values = collect_expr(df, expr)
        assert values == [1, 2, 3, -1, -2], f"[{backend_name}] Expected [1, 2, 3, -1, -2], got {values}"

    def test_cast_string_to_int(self, backend_name, backend_factory, collect_expr):
        data = {"value": ["10", "20", "30", "40", "50"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("i64")
        values = collect_expr(df, expr)
        assert values == [10, 20, 30, 40, 50], f"[{backend_name}] Expected [10, 20, 30, 40, 50], got {values}"

    def test_cast_bool_to_int(self, backend_name, backend_factory, collect_expr):
        data = {"flag": [True, False, True, False, True]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("flag").cast("i64")
        values = collect_expr(df, expr)
        assert values == [1, 0, 1, 0, 1], f"[{backend_name}] Expected [1, 0, 1, 0, 1], got {values}"

    def test_cast_int64_to_int32(self, backend_name, backend_factory, collect_expr):
        data = {"value": [100, 200, 300]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("i32")
        values = collect_expr(df, expr)
        assert values == [100, 200, 300], f"[{backend_name}] Expected [100, 200, 300], got {values}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestCastToFloat:
    """Test casting to float types."""

    def test_cast_int_to_float(self, backend_name, backend_factory, collect_expr):
        data = {"value": [1, 2, 3, 4, 5]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("fp64")
        values = collect_expr(df, expr)
        assert values == [1.0, 2.0, 3.0, 4.0, 5.0], f"[{backend_name}] Expected [1.0, 2.0, 3.0, 4.0, 5.0], got {values}"

    def test_cast_string_to_float(self, backend_name, backend_factory, collect_expr):
        data = {"value": ["1.5", "2.5", "3.5"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("fp64")
        values = collect_expr(df, expr)
        assert values == [1.5, 2.5, 3.5], f"[{backend_name}] Expected [1.5, 2.5, 3.5], got {values}"

    def test_cast_bool_to_float(self, backend_name, backend_factory, collect_expr):
        data = {"flag": [True, False, True]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("flag").cast("fp64")
        values = collect_expr(df, expr)
        assert values == [1.0, 0.0, 1.0], f"[{backend_name}] Expected [1.0, 0.0, 1.0], got {values}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestCastToString:
    """Test casting to string type."""

    def test_cast_int_to_string(self, backend_name, backend_factory, collect_expr):
        data = {"value": [1, 2, 3, 100, 999]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("string")
        values = collect_expr(df, expr)
        assert values == ["1", "2", "3", "100", "999"], f"[{backend_name}] Expected string list, got {values}"

    def test_cast_float_to_string(self, backend_name, backend_factory, collect_expr):
        data = {"value": [1.5, 2.0, 3.75]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("string")
        values = collect_expr(df, expr)
        assert len(values) == 3, f"[{backend_name}] Expected 3 values"
        assert "1" in values[0] and "5" in values[0], f"[{backend_name}] Expected '1.5', got {values[0]}"

    def test_cast_bool_to_string(self, backend_name, backend_factory, collect_expr):
        data = {"flag": [True, False, True]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("flag").cast("string")
        values = collect_expr(df, expr)
        assert len(values) == 3, f"[{backend_name}] Expected 3 values"
        assert values[0] != values[1], f"[{backend_name}] True and False should differ: {values}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestCastToBoolean:
    """Test casting to boolean type."""

    def test_cast_int_to_bool(self, backend_name, backend_factory, collect_expr):
        data = {"value": [0, 1, 2, -1, 0]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("bool")
        values = collect_expr(df, expr)
        assert values == [False, True, True, True, False], f"[{backend_name}] Expected [F,T,T,T,F], got {values}"

    def test_cast_float_to_bool(self, backend_name, backend_factory, collect_expr):
        data = {"value": [0.0, 1.0, 0.5, -0.5, 0.0]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("bool")
        values = collect_expr(df, expr)
        assert values == [False, True, True, True, False], f"[{backend_name}] Expected [F,T,T,T,F], got {values}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestCastWithNulls:
    """Test casting with null values."""

    def test_cast_with_null_int_to_float(self, backend_name, backend_factory, collect_expr):
        data = {"value": [1, None, 3, None, 5]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("fp64")
        values = collect_expr(df, expr)
        assert values[0] == 1.0
        assert values[2] == 3.0
        assert values[4] == 5.0
        assert values[1] is None or (isinstance(values[1], float) and math.isnan(values[1])), \
            f"[{backend_name}] Second value should be null: {values[1]}"
        assert values[3] is None or (isinstance(values[3], float) and math.isnan(values[3])), \
            f"[{backend_name}] Fourth value should be null: {values[3]}"

    def test_cast_with_null_float_to_string(self, backend_name, backend_factory, collect_expr):
        if backend_name == "pandas":
            pytest.xfail(
                "Pandas converts null float to 'nan' instead of preserving None."
            )
        data = {"value": [1.5, None, 3.5]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("string")
        values = collect_expr(df, expr)
        assert isinstance(values[0], str), f"[{backend_name}] First should be string: {values[0]}"
        assert isinstance(values[2], str), f"[{backend_name}] Third should be string: {values[2]}"
        assert values[1] is None, f"[{backend_name}] Second value should be null: {values[1]}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestCastInExpressions:
    """Test using cast within larger expressions."""

    def test_cast_then_arithmetic(self, backend_name, backend_factory, collect_expr):
        data = {"value": ["10", "20", "30"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("i64") * 2
        values = collect_expr(df, expr)
        assert values == [20, 40, 60], f"[{backend_name}] Expected [20, 40, 60], got {values}"

    def test_cast_then_comparison(self, backend_name, backend_factory, collect_expr):
        data = {"value": ["5", "15", "25"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("i64").gt(10)
        values = collect_expr(df, expr)
        assert values == [False, True, True], f"[{backend_name}] Expected [F,T,T], got {values}"

    def test_arithmetic_then_cast(self, backend_name, backend_factory, collect_expr):
        data = {"a": [10, 20, 30], "b": [3, 3, 3]}
        df = backend_factory.create(data, backend_name)
        expr = (ma.col("a") + ma.col("b")).cast("string")
        values = collect_expr(df, expr)
        assert values == ["13", "23", "33"], f"[{backend_name}] Expected ['13','23','33'], got {values}"

    def test_cast_with_alias(self, backend_name, backend_factory):
        data = {"price": [100, 200, 300]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("price").cast("fp64").name.alias("price_float")
        backend_expr = expr.compile(df)
        if backend_name.startswith("ibis-"):
            result = df.select(backend_expr)
            values = result.to_pyarrow()["price_float"].to_pylist()
        else:
            result = df.select(backend_expr)
            values = result["price_float"].to_list()
        assert values == [100.0, 200.0, 300.0], f"[{backend_name}] Expected [100.0, 200.0, 300.0], got {values}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestCastEdgeCases:
    """Test edge cases for cast operations."""

    def test_cast_same_type(self, backend_name, backend_factory, collect_expr):
        data = {"value": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("i64")
        values = collect_expr(df, expr)
        assert values == [1, 2, 3], f"[{backend_name}] Expected [1, 2, 3], got {values}"

    def test_cast_negative_float_to_int(self, backend_name, backend_factory, collect_expr):
        if backend_name == "ibis-duckdb":
            pytest.xfail(
                "DuckDB uses banker's rounding for float-to-int cast, not truncation."
            )
        data = {"value": [-1.9, -2.1, -3.5]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("i64")
        values = collect_expr(df, expr)
        assert values == [-1, -2, -3], f"[{backend_name}] Expected [-1, -2, -3], got {values}"

    def test_cast_zero_values(self, backend_name, backend_factory, collect_expr):
        data = {"value": [0, 0, 0]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("string")
        values = collect_expr(df, expr)
        assert len(values) == 3
        for v in values:
            assert "0" in v, f"[{backend_name}] Expected '0' in {v}"

    def test_cast_large_int_to_float(self, backend_name, backend_factory, collect_expr):
        data = {"value": [1000000, 2000000, 3000000]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("fp64")
        values = collect_expr(df, expr)
        assert values == [1000000.0, 2000000.0, 3000000.0], f"[{backend_name}] Expected floats, got {values}"
