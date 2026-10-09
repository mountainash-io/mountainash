"""Cross-backend tests for cast operation behavior.

Validates that type casting produces correct values consistently across
all backends: Polars, Pandas, Narwhals, and Ibis (DuckDB, Polars, SQLite).

Uses canonical mountainash type strings ("i64", "string", "fp64", etc.)
instead of backend-specific types.
"""

import pytest
import math
import mountainash.expressions as ma
from fixtures.backend_registry import ALL_BACKENDS
from _pytest.outcomes import Failed
from ibis.common.exceptions import OperationNotDefinedError
from mountainash.core.types import BackendCapabilityError
from decimal import Decimal
import mountainash
from fixtures.call_expectations import expect_call_failure


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestCastToInteger:
    """Test casting to integer types."""

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
        assert values[1] is None or (isinstance(values[1], float) and math.isnan(values[1])), (
            f"[{backend_name}] Second value should be null: {values[1]}"
        )
        assert values[3] is None or (isinstance(values[3], float) and math.isnan(values[3])), (
            f"[{backend_name}] Fourth value should be null: {values[3]}"
        )

    def test_cast_with_null_float_to_string(self, backend_name, backend_factory, collect_expr):
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
            if hasattr(result, "collect"):
                result = result.collect()
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


_FAILURE_NULL_BACKENDS = [
    b if b in ("pandas", "narwhals-polars", "narwhals-pandas", "narwhals-lazy") else b for b in ALL_BACKENDS
]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _FAILURE_NULL_BACKENDS)
class TestCastFailureBehavior:
    """Test CastNode.failure_behavior wiring: default THROW vs NULL-on-failure.

    Previously silently dropped by the visitor -- every backend compiled a
    strict cast regardless of the `failure_behavior` requested via the
    fluent `.cast(dtype, failure_behavior=...)` API. The narwhals/pandas gap is
    and ibis-sqlite gap are covered by exact scoped manifestation bindings.
    """

    def test_cast_failure_behavior_null(self, backend_name, backend_factory, collect_expr):
        from mountainash.expressions.core.expression_protocols.api_builders.extensions_mountainash.prtcl_api_bldr_ext_ma_cast import (
            CaseFailureBehaviour,
        )

        data = {"value": ["1", "1x", "3"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("i64", failure_behavior=CaseFailureBehaviour.NULL)
        with expect_call_failure(
            when=backend_name in ('pandas', 'narwhals-pandas', 'narwhals-polars', 'narwhals-lazy') or backend_name == 'ibis-sqlite',
            reason=('NULL-on-cast-failure cannot materialize on the marked provider.' if backend_name in ('pandas', 'narwhals-pandas', 'narwhals-polars', 'narwhals-lazy') else 'NULL-on-cast-failure cannot materialize on the marked provider.'),
            errors=((BackendCapabilityError,) if backend_name in ('pandas', 'narwhals-pandas', 'narwhals-polars', 'narwhals-lazy') else (OperationNotDefinedError,)),
        ):
            values = collect_expr(df, expr)
            assert values == [1, None, 3], f"[{backend_name}] Expected [1, None, 3], got {values}"


_IBIS_DUCKDB_CAST_BACKENDS = [b for b in ALL_BACKENDS]

_SQLITE_LENIENT_CAST_BACKENDS = [b for b in ALL_BACKENDS]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _IBIS_DUCKDB_CAST_BACKENDS)
class TestCastBankersRounding:
    """Float-to-int cast truncation. ibis-duckdb routes through IB-CAST-01
    (DuckDB uses IEEE-754 banker's rounding, not truncation)."""

    def test_cast_float_to_int(self, backend_name, backend_factory, collect_expr):
        data = {"value": [1.1, 2.9, 3.5, -1.7, -2.3]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("i64")
        with expect_call_failure(
            when=backend_name == 'ibis-duckdb',
            reason='Tests expecting truncation-on-cast produce different results on ibis-duckdb.',
            errors=(AssertionError,),
        ):
            values = collect_expr(df, expr)
            assert values == [1, 2, 3, -1, -2], f"[{backend_name}] Expected [1, 2, 3, -1, -2], got {values}"

    def test_cast_negative_float_to_int(self, backend_name, backend_factory, collect_expr):
        data = {"value": [-1.9, -2.1, -3.5]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("i64")
        with expect_call_failure(
            when=backend_name == 'ibis-duckdb',
            reason='Tests expecting truncation-on-cast produce different results on ibis-duckdb.',
            errors=(AssertionError,),
        ):
            values = collect_expr(df, expr)
            assert values == [-1, -2, -3], f"[{backend_name}] Expected [-1, -2, -3], got {values}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _SQLITE_LENIENT_CAST_BACKENDS)
class TestCastThrowSqliteLenient:
    """THROW-on-invalid cast. ibis-sqlite routes through IB-CAST-03 (SQLite CAST
    is inherently lenient — parses the leading numeric prefix instead of raising)."""

    def test_cast_failure_behavior_throw_default(self, backend_name, backend_factory, collect_expr):
        """Default (THROW) behaviour must remain byte-identical: raises on invalid input."""
        data = {"value": ["1", "1x", "3"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("i64")
        with expect_call_failure(
            when=backend_name == 'ibis-sqlite',
            reason='Strict casts do not raise for malformed input on ibis-sqlite.',
            errors=(Failed,),
        ):
            with pytest.raises(Exception):
                collect_expr(df, expr)

    def test_cast_failure_behavior_throw_explicit(self, backend_name, backend_factory, collect_expr):
        """Explicit failure_behavior=THROW behaves identically to the default."""
        from mountainash.expressions.core.expression_protocols.api_builders.extensions_mountainash.prtcl_api_bldr_ext_ma_cast import (
            CaseFailureBehaviour,
        )

        data = {"value": ["1", "1x", "3"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("i64", failure_behavior=CaseFailureBehaviour.THROW)
        with expect_call_failure(
            when=backend_name == 'ibis-sqlite',
            reason='Strict casts do not raise for malformed input on ibis-sqlite.',
            errors=(Failed,),
        ):
            with pytest.raises(Exception):
                collect_expr(df, expr)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestExactNumericCast:
    """Exact numeric targets must retain their value domain and cast policies."""

    def test_rounding_options_survive_composed_projection(self, backend_name, backend_factory):
        target = mountainash.DecimalDtype(precision=5, scale=2)
        df = backend_factory.create({
            "value": ["12.345", "-12.345", "12.34501", "-12.34501", "12.355", "-12.355", None]
        }, backend_name)
        even = ma.col("value").cast(target).name.alias("even")
        away = ma.col("value").cast(target, rounding="TIE_AWAY_FROM_ZERO").name.alias("away")
        relation = mountainash.relation(df).select(even, away)
        if backend_name == "ibis-sqlite":
            with pytest.raises(BackendCapabilityError):
                relation.to_dict()
            return
        assert relation.to_dict() == {
            "even": [Decimal("12.34"), Decimal("-12.34"), Decimal("12.35"), Decimal("-12.35"),
                     Decimal("12.36"), Decimal("-12.36"), None],
            "away": [Decimal("12.35"), Decimal("-12.35"), Decimal("12.35"), Decimal("-12.35"),
                     Decimal("12.36"), Decimal("-12.36"), None],
        }

    def test_precision_and_scale_control_post_round_overflow(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create({"value": ["999.995", "-999.995", "12.345", "bad", None]}, backend_name)
        narrow = ma.col("value").cast(
            mountainash.DecimalDtype(precision=5, scale=2), failure_behavior="null"
        )
        if backend_name == "ibis-sqlite":
            with pytest.raises(BackendCapabilityError):
                collect_expr(df, narrow)
            return
        assert collect_expr(df, narrow) == [None, None, Decimal("12.34"), None, None]
        wide = ma.col("value").cast(
            mountainash.DecimalDtype(precision=6, scale=2), failure_behavior="null"
        )
        assert collect_expr(df, wide) == [
            Decimal("1000.00"), Decimal("-1000.00"), Decimal("12.34"), None, None
        ]
        fine = ma.col("value").cast(
            mountainash.DecimalDtype(precision=6, scale=3), failure_behavior="null"
        )
        assert collect_expr(df, fine) == [
            Decimal("999.995"), Decimal("-999.995"), Decimal("12.345"), None, None
        ]

    @pytest.mark.parametrize(
        "kind,values,expected",
        [
            ("LEXICAL_INTEGER", ["+00020", "1e80", "-0", "1.25", "12x", None],
             ["20", "1" + "0" * 80, "0", None, None, None]),
            ("LEXICAL_DECIMAL", ["+00020.5000", "1.23e-8", "-0.0", "NaN", "12x", None],
             ["20.5", "0.0000000123", "0", None, None, None]),
        ],
    )
    def test_lexical_values_are_canonical_and_checked(
        self, backend_name, backend_factory, collect_expr, kind, values, expected
    ):
        target = getattr(mountainash.MountainashDtype, kind)
        df = backend_factory.create({"value": values}, backend_name)
        assert collect_expr(df, ma.col("value").cast(target, failure_behavior="null")) == expected

    @pytest.mark.parametrize("named", [False, True])
    def test_exact_literals_are_prepared_before_native_inference(
        self, backend_name, backend_factory, named
    ):
        integer = 2**200 + 19
        decimal = Decimal("123456789012345678901234567890123456789012345678901234567890.12345678901234567890")
        df = backend_factory.create({"row": [1, 2]}, backend_name)
        integer_expr, decimal_expr = ma.lit(integer), ma.lit(decimal)
        if named:
            integer_expr = integer_expr.name.alias("raw_integer")
            decimal_expr = decimal_expr.name.alias("raw_decimal")
        result = mountainash.relation(df).with_columns(
            integer_expr.cast(mountainash.MountainashDtype.LEXICAL_INTEGER).name.alias("integer"),
            decimal_expr.cast(mountainash.MountainashDtype.LEXICAL_DECIMAL).name.alias("decimal"),
        ).to_dict()
        assert result == {
            "row": [1, 2],
            "integer": ["1606938044258990275541962092341162602522202993782792835301395"] * 2,
            "decimal": ["123456789012345678901234567890123456789012345678901234567890.1234567890123456789"] * 2,
        }

    def test_null_literal_retains_target_type(self, backend_name, backend_factory):
        import polars as pl

        df = backend_factory.create({"row": [1, 2]}, backend_name)
        expr = ma.lit(None).cast(mountainash.DecimalDtype(precision=20, scale=3))
        result = mountainash.relation(df).with_columns(expr.name.alias("value"))
        if backend_name == "ibis-sqlite":
            with pytest.raises(BackendCapabilityError):
                result.to_polars()
            return
        frame = result.to_polars()
        assert frame.to_dict(as_series=False) == {"row": [1, 2], "value": [None, None]}
        assert frame.schema["value"] == pl.Decimal(20, 3)

    def test_explicit_float_conversion_uses_binary_value(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create({"value": [2.675, -2.675, None]}, backend_name)
        expr = ma.col("value").cast(mountainash.DecimalDtype(precision=5, scale=2))
        if backend_name == "ibis-sqlite":
            with pytest.raises(BackendCapabilityError):
                collect_expr(df, expr)
            return
        assert collect_expr(df, expr) == [Decimal("2.67"), Decimal("-2.67"), None]

    @pytest.mark.parametrize("values", [[], [None, None]])
    @pytest.mark.parametrize("failure_behavior", ["throw", "null"])
    def test_empty_and_null_inputs_do_not_bypass_capabilities(
        self, backend_name, backend_factory, values, failure_behavior
    ):
        import polars as pl

        # Retain a declared text carrier even on engines that cannot create NULL-typed tables.
        df = backend_factory.create({
            "value": ["0", *values], "keep": [False, *([True] * len(values))]
        }, backend_name)
        expr = ma.col("value").cast(
            mountainash.DecimalDtype(precision=20, scale=3),
            failure_behavior=failure_behavior,
        ).name.alias("value")
        source = mountainash.relation(df).filter(ma.col("keep")).select("value")
        result = source.with_columns(expr)
        if backend_name == "ibis-sqlite":
            with pytest.raises(BackendCapabilityError):
                result.to_polars()
            return
        frame = result.to_polars()
        assert frame.to_dict(as_series=False) == {"value": values}
        assert frame.schema["value"] == pl.Decimal(20, 3)

    @pytest.mark.parametrize("value", ["999.995", "-999.995", "12x", "NaN"])
    def test_throw_policy_rejects_bad_rows(self, backend_name, backend_factory, collect_expr, value):
        from mountainash.exceptions import NumericConversionError

        df = backend_factory.create({"value": [value]}, backend_name)
        expr = ma.col("value").cast(
            mountainash.DecimalDtype(precision=5, scale=2), failure_behavior="throw"
        )
        error = NumericConversionError
        if backend_name == "ibis-sqlite":
            error = BackendCapabilityError
        elif backend_name == "ibis-duckdb":
            import duckdb

            error = duckdb.InvalidInputException
        with pytest.raises(error):
            collect_expr(df, expr)

    @pytest.mark.parametrize("values,expected", [
        ([9007199254740993, -9007199254740993],
         [Decimal("9007199254740993.000"), Decimal("-9007199254740993.000")]),
        ([Decimal("12.3455"), Decimal("-12.3555")],
         [Decimal("12.346"), Decimal("-12.356")]),
    ])
    def test_native_numeric_columns_do_not_pass_through_float(
        self, backend_name, backend_factory, collect_expr, values, expected
    ):
        if backend_name == "ibis-sqlite" and isinstance(values[0], Decimal):
            # SQLite cannot bind a native Decimal source, independently of casts.
            import sqlite3

            with pytest.raises(sqlite3.ProgrammingError):
                backend_factory.create({"value": values}, backend_name)
            return
        df = backend_factory.create({"value": values}, backend_name)
        expr = ma.col("value").cast(mountainash.DecimalDtype(precision=20, scale=3))
        if backend_name == "ibis-sqlite":
            with pytest.raises(BackendCapabilityError):
                collect_expr(df, expr)
            return
        assert collect_expr(df, expr) == expected

    def test_unbounded_integer_literal_avoids_python_string_limit(self, backend_name, backend_factory):
        df = backend_factory.create({"row": [1]}, backend_name)
        expr = ma.lit(10**4999 + 1).cast(
            mountainash.MountainashDtype.LEXICAL_INTEGER
        ).name.alias("value")
        result = mountainash.relation(df).with_columns(expr).to_dict()
        assert result == {"row": [1], "value": ["1" + "0" * 4998 + "1"]}

    @pytest.mark.parametrize("precision,scale,value", [
        (20, 3, Decimal("9007199254740993.125")),
        (38, 38, Decimal("0.12345678901234567890123456789012345678")),
    ])
    def test_fixed_decimal_literal_broadcasts_without_native_inference_loss(
        self, backend_name, backend_factory, precision, scale, value
    ):
        df = backend_factory.create({"row": [1, 2]}, backend_name)
        expr = ma.lit(value).cast(
            mountainash.DecimalDtype(precision=precision, scale=scale)
        ).name.alias("amount")
        result = mountainash.relation(df).with_columns(expr)
        if backend_name == "ibis-sqlite":
            with pytest.raises(BackendCapabilityError):
                result.to_dict()
            return
        assert result.to_dict() == {
            "row": [1, 2],
            "amount": [value, value],
        }
