"""
Cross-backend tests for arithmetic operations.

Tests basic arithmetic operations:
- Addition, subtraction, multiplication, division
- Modulo, power, floor division
- Python magic operators (+, -, *, /, //, %, **)
- Chaining arithmetic operations
- Edge cases (division by zero, negative numbers)

These tests validate that arithmetic works consistently across
all backends: Polars, Pandas, Narwhals, and Ibis (DuckDB, Polars, SQLite).
"""

from decimal import Decimal as D

import polars as pl
import narwhals as nw
import mountainash as ma_top
from mountainash.core.types import BackendCapabilityError
import pytest
import mountainash.expressions as ma

from fixtures.backend_registry import ALL_BACKENDS
from fixtures.call_expectations import expect_call_failure

# =============================================================================
# Cross-Backend Tests - Basic Arithmetic
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.arithmetic
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestBasicArithmetic:
    """Test basic arithmetic operations across all backends."""

    def test_addition(self, backend_name, backend_factory, collect_expr):
        """Test addition operation."""
        data = {"a": [10, 20, 30, 40, 50], "b": [2, 3, 4, 5, 6]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a").add(ma.col("b"))

        # Use helper - replaces 9 lines with 1!
        actual = collect_expr(df, expr)

        expected = [12, 23, 34, 45, 56]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    @pytest.mark.parametrize(
        ("values", "other", "options", "expected"),
        [
            pytest.param([0.25, 0.75], 0.5, {"rounding": "CEILING"}, [0.75, 1.25], id="rounding"),
            pytest.param([2, 3], 1, {"overflow": "SATURATE"}, [3, 4], id="overflow"),
        ],
    )
    def test_unsupported_arithmetic_option_requires_backend_support_without_catalogue(
        self, backend_name, backend_factory, collect_expr, values, other, options, expected,
    ):
        from mountainash.core.capabilities import CapabilityRegistry
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import (
            FKEY_SUBSTRAIT_SCALAR_ARITHMETIC,
        )

        df = backend_factory.create({"v": values}, backend_name)
        snapshot = CapabilityRegistry.snapshot()
        try:
            CapabilityRegistry.reset()
            assert collect_expr(df, ma.col("v").add(other)) == expected
            with pytest.raises(BackendCapabilityError) as caught:
                collect_expr(df, ma.col("v").add(other, **options))
            assert caught.value.function_key is FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ADD
            assert caught.value.limitation is None
        finally:
            CapabilityRegistry.restore(snapshot)

    def test_subtraction(self, backend_name, backend_factory, collect_expr):
        """Test subtraction operation."""
        data = {"a": [10, 20, 30, 40, 50], "b": [2, 3, 4, 5, 6]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a").subtract(ma.col("b"))

        actual = collect_expr(df, expr)

        expected = [8, 17, 26, 35, 44]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_multiplication(self, backend_name, backend_factory, collect_expr):
        """Test multiplication operation."""
        data = {"a": [10, 20, 30, 40, 50], "c": [1, 2, 3, 4, 5]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a").multiply(ma.col("c"))

        actual = collect_expr(df, expr)

        expected = [10, 40, 90, 160, 250]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_division(self, backend_name, backend_factory, collect_expr):
        """Test division operation."""
        data = {"a": [10, 20, 30, 40, 50], "b": [2, 3, 4, 5, 6]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a").divide(ma.col("b"))

        actual = collect_expr(df, expr)

        expected = [10 / 2, 20 / 3, 30 / 4, 40 / 5, 50 / 6]

        # Check each value with tolerance for floating point
        for i, (act, exp) in enumerate(zip(actual, expected)):
            assert abs(act - exp) < 0.0001, f"[{backend_name}] At index {i}: expected {exp}, got {act}"

    def test_modulo(self, backend_name, backend_factory, collect_expr):
        """Test modulo operation."""
        data = {"a": [10, 20, 30, 40, 50], "b": [2, 3, 4, 5, 6]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a").modulo(ma.col("b"))

        actual = collect_expr(df, expr)

        expected = [0, 2, 2, 0, 2]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_power(self, backend_name, backend_factory, collect_expr):
        """Test power operation."""
        data = {"c": [1, 2, 3, 4, 5]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("c").power(2)

        actual = collect_expr(df, expr)

        expected = [1, 4, 9, 16, 25]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_floor_division(self, backend_name, backend_factory, collect_expr):
        """Test floor division operation."""
        data = {"a": [10, 20, 30, 40, 50], "b": [2, 3, 4, 5, 6]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a").floor_divide(ma.col("b"))

        actual = collect_expr(df, expr)

        expected = [5, 6, 7, 8, 8]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"


# =============================================================================
# Cross-Backend Tests - Python Magic Operators
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.arithmetic
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestPythonMagicOperators:
    """Test Python magic operators (+, -, *, /, etc.)."""

    def test_plus_operator(self, backend_name, backend_factory, collect_expr):
        """Test + operator."""
        data = {"x": [10, 20, 30], "y": [2, 4, 5]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("x") + ma.col("y")

        actual = collect_expr(df, expr)

        expected = [12, 24, 35]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_minus_operator(self, backend_name, backend_factory, collect_expr):
        """Test - operator."""
        data = {"x": [10, 20, 30], "y": [2, 4, 5]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("x") - ma.col("y")

        actual = collect_expr(df, expr)

        expected = [8, 16, 25]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_multiply_operator(self, backend_name, backend_factory, collect_expr):
        """Test * operator."""
        data = {"x": [10, 20, 30], "y": [2, 4, 5]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("x") * ma.col("y")

        actual = collect_expr(df, expr)

        expected = [20, 80, 150]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_divide_operator(self, backend_name, backend_factory, collect_expr):
        """Test / operator."""
        data = {"x": [10, 20, 30], "y": [2, 4, 5]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("x") / ma.col("y")

        actual = collect_expr(df, expr)

        expected = [5.0, 5.0, 6.0]

        for i, (act, exp) in enumerate(zip(actual, expected)):
            assert abs(act - exp) < 0.0001, f"[{backend_name}] At index {i}: expected {exp}, got {act}"


# =============================================================================
# Integration Tests - Complex Arithmetic
# =============================================================================


@pytest.mark.integration
@pytest.mark.arithmetic
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestComplexArithmetic:
    """Test chaining and complex arithmetic operations."""

    def test_chained_operations(self, backend_name, backend_factory, collect_expr):
        """Test chaining multiple arithmetic operations."""
        data = {"a": [10, 20, 30], "b": [2, 3, 4], "c": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)

        # (a + b) * c
        expr = (ma.col("a") + ma.col("b")) * ma.col("c")

        actual = collect_expr(df, expr)

        expected = [12, 46, 102]  # (10+2)*1=12, (20+3)*2=46, (30+4)*3=102
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_mixed_literals_and_columns(self, backend_name, backend_factory, collect_expr):
        """Test mixing literal values with column references."""
        data = {"a": [10, 20, 30]}
        df = backend_factory.create(data, backend_name)

        # a * 2 + 5
        expr = ma.col("a") * 2 + 5

        actual = collect_expr(df, expr)

        expected = [25, 45, 65]  # 10*2+5=25, 20*2+5=45, 30*2+5=65
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_complex_chained_operations(self, backend_name, backend_factory, collect_expr):
        """Test complex chained arithmetic operations (float division)."""
        data = {"a": [10, 20, 30], "b": [2, 3, 4], "c": [5, 10, 15]}
        df = backend_factory.create(data, backend_name)

        # (a + b) * c - a / b
        expr = (ma.col("a") + ma.col("b")) * ma.col("c") - ma.col("a") / ma.col("b")

        actual = collect_expr(df, expr)

        import math

        expected = [55.0, 230.0 - (20.0 / 3.0), 502.5]

        for i, (a, e) in enumerate(zip(actual, expected)):
            assert math.isclose(a, e, rel_tol=1e-9), f"[{backend_name}] At index {i}: expected {e}, got {a}"


# =============================================================================
# Edge Case Tests
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.arithmetic
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestArithmeticEdgeCases:
    """Test edge cases for arithmetic operations."""

    def test_negative_numbers(self, backend_name, backend_factory, collect_expr):
        """Test arithmetic with negative numbers."""
        data = {"a": [-10, -20, 30], "b": [2, -3, 4]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a") + ma.col("b")

        actual = collect_expr(df, expr)

        expected = [-8, -23, 34]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_zero_operations(self, backend_name, backend_factory, collect_expr):
        """Test arithmetic with zero."""
        data = {"a": [10, 0, 30], "zero": [0, 0, 0]}
        df = backend_factory.create(data, backend_name)

        # Add zero (should return same values)
        expr = ma.col("a") + ma.col("zero")

        actual = collect_expr(df, expr)

        expected = [10, 0, 30]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_large_numbers(self, backend_name, backend_factory, collect_expr):
        """Test arithmetic with large numbers."""
        data = {"a": [1000000, 2000000, 3000000], "b": [500000, 1000000, 1500000]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a") + ma.col("b")

        actual = collect_expr(df, expr)

        expected = [1500000, 3000000, 4500000]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_floating_point_operations(self, backend_name, backend_factory, collect_expr):
        """Test arithmetic with floating point numbers."""
        data = {"a": [1.5, 2.5, 3.5], "b": [0.5, 1.5, 2.5]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a") + ma.col("b")

        actual = collect_expr(df, expr)

        expected = [2.0, 4.0, 6.0]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_power_with_zero(self, backend_name, backend_factory, collect_expr):
        """Test power operation with zero exponent."""
        data = {"a": [5, 10, 100]}
        df = backend_factory.create(data, backend_name)

        # Any number to the power of 0 should be 1
        expr = ma.col("a") ** 0

        actual = collect_expr(df, expr)

        expected = [1, 1, 1]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_power_with_one(self, backend_name, backend_factory, collect_expr):
        """Test power operation with one as exponent."""
        data = {"a": [5, 10, 100]}
        df = backend_factory.create(data, backend_name)

        # Any number to the power of 1 should be itself
        expr = ma.col("a") ** 1

        actual = collect_expr(df, expr)

        expected = [5, 10, 100]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_floor_division_with_negatives(self, backend_name, backend_factory, collect_expr):
        """Test floor division with negative numbers."""
        data = {"a": [-10, 10, -10], "b": [3, -3, -3]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a") // ma.col("b")

        actual = collect_expr(df, expr)

        # Floor division rounds toward negative infinity
        expected = [-4, -4, 3]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_multiply_by_zero(self, backend_name, backend_factory, collect_expr):
        """Test multiplication by zero."""
        data = {"a": [10, 20, 30, -5]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a") * 0

        actual = collect_expr(df, expr)

        expected = [0, 0, 0, 0]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_multiply_by_one(self, backend_name, backend_factory, collect_expr):
        """Test multiplication by one (identity)."""
        data = {"a": [10, 20, 30, -5]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a") * 1

        actual = collect_expr(df, expr)

        expected = [10, 20, 30, -5]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_subtract_from_zero(self, backend_name, backend_factory, collect_expr):
        """Test subtracting from zero (negation)."""
        data = {"a": [10, -20, 30, 0]}
        df = backend_factory.create(data, backend_name)

        expr = 0 - ma.col("a")

        actual = collect_expr(df, expr)
        expected = [-10, 20, -30, 0]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"

    def test_mixed_integer_float(self, backend_name, backend_factory, collect_expr):
        """Test operations with mixed integer and float types."""
        data = {"int_col": [10, 20, 30], "float_col": [2.5, 3.5, 4.5]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("int_col") * ma.col("float_col")

        actual = collect_expr(df, expr)

        expected = [25.0, 70.0, 135.0]
        assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"


_MODULO_NEG_BACKENDS = [b for b in ALL_BACKENDS]


@pytest.mark.arithmetic
@pytest.mark.parametrize("backend_name", _MODULO_NEG_BACKENDS)
class TestModuloWithNegatives:
    """Negative-operand modulo. ibis-sqlite/ibis-duckdb route through IB-MATH-05
    (SQL modulo takes the sign of the dividend rather than the divisor)."""

    def test_modulo_with_negatives(self, backend_name, backend_factory, collect_expr):
        data = {"a": [-10, 10, -10], "b": [3, -3, -3]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a") % ma.col("b")

        with expect_call_failure(
            when=backend_name in ('ibis-sqlite', 'ibis-duckdb'),
            reason='Cyclic calculations and hash bucketing with negative dividends diverge',
            errors=(AssertionError,),
        ):
            actual = collect_expr(df, expr)

            # Python modulo: result has same sign as the divisor
            expected = [2, -2, -1]

            assert actual == expected, f"[{backend_name}] Expected {expected}, got {actual}"


def _sqlite_decimal_refusal(backend_factory):
    frame = backend_factory.create({"a": ["1.25"]}, "ibis-sqlite")
    with pytest.raises(BackendCapabilityError, match="fixed-precision decimal"):
        ma_top.relation(frame).select(
            ma.col("a").cast(ma_top.DecimalDtype(12, 3), rounding="half_to_even")
        ).to_polars()


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("working", [False, True], ids=["native-decimal", "authored-fp64"])
@pytest.mark.parametrize(
    "operation, expected",
    [
        ("add", ["8.25", "-4.25", "2", None]),
        ("subtract", ["4.25", "-8.25", "-2", None]),
        ("multiply", ["12.5", "-12.5", "0", None]),
        ("divide", ["3.125", "-3.125", "0", None]),
        ("floor_divide", ["3", "-4", "0", None]),
        ("modulus", ["0.25", "1.75", "0", None]),
        ("power", ["39.0625", "39.0625", "0", None]),
    ],
)
def test_declared_decimal_binary(
    backend_name, declared_decimal_frame, backend_factory, working, operation, expected
):
    """Catch wrong lowering/order/null handling without hiding native arithmetic behind casts."""
    if backend_name == "ibis-sqlite":
        _sqlite_decimal_refusal(backend_factory)
        return
    frame = declared_decimal_frame(
        {"a": [D("6.250"), D("-6.250"), D("0"), None],
         "b": [D("2.00")] * 4},
        {"a": (12, 3), "b": (10, 2)},
    )
    a, b = ma.col("a"), ma.col("b")
    if working:
        a, b = a.cast("fp64"), b.cast("fp64")
    expr = getattr(a, operation)(b)
    if working:
        expr = expr.cast(ma_top.DecimalDtype(16, 5), rounding="half_to_even")
    query = ma_top.relation(frame).select(expr.alias("r"))
    if working and backend_name in {"pandas", "narwhals-pandas", "narwhals-polars", "narwhals-lazy"}:
        with pytest.raises(BackendCapabilityError, match="NW-MATH-11"):
            query.to_polars()
        return
    unsupported = (
        not working
        and operation == "power"
        and backend_name in {"polars", "polars-lazy", "narwhals-polars", "narwhals-lazy", "ibis-polars"}
    )
    with expect_call_failure(
        when=unsupported,
        reason="Polars Decimal power kernel remains unsupported (288)",
        errors=(nw.exceptions.InvalidOperationError,) if backend_name.startswith("narwhals") else (pl.exceptions.InvalidOperationError,),
    ):
        with expect_call_failure(
            when=(operation == "modulus" and backend_name == "ibis-duckdb")
            or (not working and operation == "power" and backend_name == "ibis-duckdb"),
            reason="IB-MATH-05 remainder sign; Ibis 12 Decimal power extraction rounds native DOUBLE to input scale (288)",
            errors=(AssertionError,),
        ):
            with expect_call_failure(
                when=not working and operation == "modulus" and backend_name in {"pandas", "narwhals-pandas"},
                reason="pandas 3 Arrow Decimal remainder is not implemented (288)",
                errors=(NotImplementedError,),
            ):
                out = query.to_polars()
            if working:
                assert out.schema["r"] == pl.Decimal(16, 5)
            elif backend_name in {"pandas", "narwhals-pandas"}:
                # Arrow's decimal promotion rules; power returns floating point.
                dtype = {
                    "add": pl.Decimal(13, 3), "subtract": pl.Decimal(13, 3),
                    "multiply": pl.Decimal(23, 5), "divide": pl.Decimal(23, 12),
                    "floor_divide": pl.Decimal(23, 12), "power": pl.Float64,
                }[operation]
                assert out.schema["r"] == dtype
            elif backend_name.startswith("ibis"):
                dtype = {"divide": pl.Float64, "floor_divide": pl.Int64}.get(operation, pl.Decimal(12, 3))
                assert out.schema["r"] == dtype
            else:
                assert out.schema["r"] == pl.Decimal(38, 3)
            from mountainash.relations.schema_inference import SchemaTypeStatus
            assert query.schema["r"] in (SchemaTypeStatus.UNKNOWN, ma_top.relation(out).schema["r"])
            assert out["r"].to_list() == [D(v) if v is not None else None for v in expected]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_authored_decimal_chain(backend_name, declared_decimal_frame, backend_factory):
    """Premature conversion of either multiplicand loses the fourth fractional digit."""
    if backend_name == "ibis-sqlite":
        _sqlite_decimal_refusal(backend_factory)
        return
    frame = declared_decimal_frame(
        {"a": [D("1.235"), D("-2.345"), D("0"), None],
         "b": [D("2.50"), D("3.00"), D("4.00"), D("5.00")]},
        {"a": (12, 3), "b": (10, 2)},
    )
    a, b = ma.col("a").cast("fp64"), ma.col("b").cast("fp64")
    query = ma_top.relation(frame).select(
        (a * b + a).cast(ma_top.DecimalDtype(16, 5), rounding="half_to_even").alias("r")
    )
    if backend_name in {"pandas", "narwhals-pandas", "narwhals-polars", "narwhals-lazy"}:
        with pytest.raises(BackendCapabilityError, match="NW-MATH-11"):
            query.to_polars()
        return
    out = query.to_polars()
    assert out.schema["r"] == pl.Decimal(16, 5)
    assert out["r"].to_list() == [D("4.32250"), D("-9.38000"), D("0.00000"), None]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize(
    "left,right,declaration,expected",
    [
        ("0.105", "0.105", (10, 3), "0.011025"),
        ("12.34", "5.67", (10, 2), "69.967800"),
        ("9999.99", "9999.99", (6, 2), "99999800.000100"),
    ],
)
@pytest.mark.parametrize("working", [False, True], ids=["native-decimal", "authored-fp64"])
def test_decimal_multiplication_fractional_witnesses(
    backend_name, declared_decimal_frame, backend_factory, left, right, declaration, expected, working
):
    """Keep the original 288 witnesses: operand scale must not masquerade as exact product."""
    if backend_name == "ibis-sqlite":
        _sqlite_decimal_refusal(backend_factory)
        return
    frame = declared_decimal_frame(
        {"a": [D(left)], "b": [D(right)]}, {"a": declaration, "b": declaration}
    )
    a, b = ma.col("a"), ma.col("b")
    if working:
        a, b = a.cast("fp64"), b.cast("fp64")
    expr = a * b
    if working:
        expr = expr.cast(ma_top.DecimalDtype(16, 6), rounding="half_to_even")
    query = ma_top.relation(frame).select(expr.alias("r"))
    if working and backend_name in {"pandas", "narwhals-pandas", "narwhals-polars", "narwhals-lazy"}:
        with pytest.raises(BackendCapabilityError, match="NW-MATH-11"):
            query.to_polars()
        return
    import pyarrow as pa
    with expect_call_failure(
        when=not working and (
            backend_name == "ibis-duckdb" or (backend_name == "ibis-polars" and declaration == (6, 2))
        ),
        reason="Ibis 12 Decimal product extraction narrows native scale/precision (288)",
        errors=(pa.ArrowInvalid,),
    ):
        out = query.to_polars()
    if working:
        assert out.schema["r"] == pl.Decimal(16, 6)
    with expect_call_failure(
        when=not working and backend_name in {
            "polars", "polars-lazy", "narwhals-polars", "narwhals-lazy", "ibis-polars"
        },
        reason="Polars native Decimal multiplication retains operand scale (288/284)",
        errors=(AssertionError,),
    ):
        assert out["r"].to_list() == [D(expected)]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("working", [False, True], ids=["native-decimal", "authored-fp64"])
@pytest.mark.parametrize(
    "operation,operand,expected",
    [
        ("subtract", "decimal-literal", "4.25"),
        ("rsubtract", "decimal-literal", "-4.25"),
        ("divide", "decimal-literal", "3.125"),
        ("rdivide", "decimal-literal", "0.32"),
        ("rfloor_divide", "integer-literal", "0"),
        ("rmodulus", "integer-literal", "2"),
        ("rpower", "float-literal", "76.10926"),
        ("add", "integer-column", "8.25"),
        ("multiply", "float-column", "15.625"),
        ("multiply", "integer-literal", "12.5"),
        ("subtract", "float-literal", "4.25"),
    ],
)
def test_decimal_operand_arrangements(
    backend_name, declared_decimal_frame, backend_factory, working, operation, operand, expected
):
    """Typed literals, reversed noncommutative operations and mixed columns preserve operand roles."""
    if backend_name == "ibis-sqlite":
        _sqlite_decimal_refusal(backend_factory)
        return
    frame = declared_decimal_frame(
        {"a": [D("6.250")], "i": [2], "f": [2.5]}, {"a": (12, 3)}
    )
    a = ma.col("a")
    b = {
        "decimal-literal": ma_top.lit(D("2.00"), dtype=ma_top.DecimalDtype(10, 2)),
        "integer-literal": ma.lit(2),
        "float-literal": ma.lit(2.0),
        "integer-column": ma.col("i"),
        "float-column": ma.col("f"),
    }[operand]
    if working:
        a, b = a.cast("fp64"), b.cast("fp64")
    expr = getattr(a, operation)(b)
    if working:
        expr = expr.cast(ma_top.DecimalDtype(16, 5), rounding="half_to_even")
    query = ma_top.relation(frame).select(expr.alias("r"))
    if working and backend_name in {"pandas", "narwhals-pandas", "narwhals-polars", "narwhals-lazy"}:
        with pytest.raises(BackendCapabilityError, match="NW-MATH-11"):
            query.to_polars()
        return
    with expect_call_failure(
        when=not working and operation == "rpower"
        and backend_name in {"polars", "polars-lazy", "narwhals-polars", "narwhals-lazy", "ibis-polars"},
        reason="Polars Decimal rpower kernel remains unsupported (288)",
        errors=(nw.exceptions.InvalidOperationError,) if backend_name.startswith("narwhals") else (pl.exceptions.InvalidOperationError,),
    ):
        with expect_call_failure(
            when=not working and operation == "rmodulus" and backend_name in {"pandas", "narwhals-pandas"},
            reason="pandas 3 Arrow Decimal remainder not implemented (288)",
            errors=(NotImplementedError,),
        ):
            out = query.to_polars()
    if working:
        assert out.schema["r"] == pl.Decimal(16, 5)
        assert out["r"].to_list() == [D(expected)]
    elif operation == "rpower":
        with expect_call_failure(
            when=backend_name == "ibis-duckdb",
            reason="Ibis 12 power extraction rounds native DOUBLE to Decimal operand scale (288)",
            errors=(AssertionError,),
        ):
            assert float(out["r"][0]) == pytest.approx(76.10925536017415)
    elif out.schema["r"].is_float():
        assert out["r"].to_list() == pytest.approx([float(expected)])
    else:
        assert out["r"].to_list() == [D(expected)]
    from mountainash.relations.schema_inference import SchemaTypeStatus
    assert query.schema["r"] in (SchemaTypeStatus.UNKNOWN, ma_top.relation(out).schema["r"])


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("working", [False, True], ids=["native-decimal", "authored-fp64"])
@pytest.mark.parametrize("operation", ["divide", "floor_divide", "modulus"])
def test_decimal_zero_divisor_computation_boundary(
    backend_name, declared_decimal_frame, backend_factory, working, operation
):
    """Distinguish computation errors/nonfinite values from final Decimal conversion."""
    import math
    import duckdb
    import pyarrow as pa

    if backend_name == "ibis-sqlite":
        _sqlite_decimal_refusal(backend_factory)
        return
    control_frame = declared_decimal_frame(
        {"a": [D("1.250")], "b": [D("0.50")]}, {"a": (12, 3), "b": (10, 2)}
    )
    control_a, control_b = ma.col("a"), ma.col("b")
    if working:
        control_a, control_b = control_a.cast("fp64"), control_b.cast("fp64")
    control = ma_top.relation(control_frame).select(
        getattr(control_a, operation)(control_b).alias("r")
    )
    if backend_name in {"pandas", "narwhals-pandas"} and operation == "modulus":
        # This provider refuses modulus itself, independently of the divisor.
        with pytest.raises(NotImplementedError):
            control.to_polars()
    else:
        expected_control = {"divide": "2.5", "floor_divide": "2", "modulus": "0.25"}[operation]
        expected_value = float(expected_control) if working else D(expected_control)
        assert control.to_polars()["r"].to_list() == [expected_value]
    frame = declared_decimal_frame(
        {"a": [D("1.250")], "b": [D("0.00")]}, {"a": (12, 3), "b": (10, 2)}
    )
    a, b = ma.col("a"), ma.col("b")
    if working:
        a, b = a.cast("fp64"), b.cast("fp64")
    query = ma_top.relation(frame).select(getattr(a, operation)(b).alias("r"))
    arrow_pandas = backend_name in {"pandas", "narwhals-pandas"}
    polars_kernel = backend_name in {"polars", "polars-lazy", "narwhals-polars", "narwhals-lazy", "ibis-polars"}
    errors = nw.exceptions if backend_name.startswith("narwhals") else pl.exceptions
    error = None
    if arrow_pandas and operation == "modulus":
        error = NotImplementedError
    elif not working and operation == "divide":
        if arrow_pandas:
            error = pa.ArrowInvalid
        elif polars_kernel:
            error = errors.ComputeError
    elif not working and polars_kernel:
        error = errors.ComputeError
    if operation == "floor_divide" and backend_name.startswith("ibis"):
        if backend_name == "ibis-duckdb":
            error = duckdb.ConversionException
        elif working:
            error = pa.ArrowInvalid
    if error is not None:
        with pytest.raises(error):
            query.to_polars()
        return
    out = query.to_polars()
    if (arrow_pandas and operation == "floor_divide") or (
        not working and backend_name == "ibis-duckdb" and operation == "modulus"
    ):
        assert out["r"].to_list() == [None]
    elif operation == "modulus":
        assert math.isnan(out["r"][0])
    else:
        assert out["r"].to_list() == [float("inf")]
