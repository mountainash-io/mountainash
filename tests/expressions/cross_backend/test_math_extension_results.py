"""Cross-backend result verification for comparison and arithmetic extensions."""

from __future__ import annotations

import math

import pytest

import mountainash as ma
from fixtures.backend_registry import ALL_BACKENDS
from fixtures.call_expectations import expect_call_failure


NARWHALS_BACKENDS = {"pandas", "narwhals-polars", "narwhals-pandas"}
IBIS_BACKENDS = {"ibis-duckdb", "ibis-sqlite"}


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestIsBetween:
    def test_is_between_basic(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1, 5, 10, 15, 20]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").is_between(5, 15))
        assert actual == [False, True, True, True, False]

    def test_is_between_boundary(self, backend_name, backend_factory, collect_expr):
        data = {"a": [5, 15]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").is_between(5, 15))
        assert actual == [True, True]

    def test_is_between_with_null(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1, None, 10]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").is_between(0, 20))
        assert actual[0] is True
        assert actual[1] in [None, False]
        assert actual[2] is True


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestIsIn:
    def test_is_in_basic(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1, 2, 3, 4, 5]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").is_in([2, 4]))
        assert actual == [False, True, False, True, False]

    def test_is_in_with_null(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1, None, 3]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").is_in([1, 3]))
        assert actual[0] is True
        assert actual[1] in [None, False]
        assert actual[2] is True

    def test_is_in_no_match(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").is_in([99, 100]))
        assert actual == [False, False, False]

    def test_is_in_strings(self, backend_name, backend_factory, collect_expr):
        data = {"a": ["apple", "banana", "cherry"]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").is_in(["banana", "cherry"]))
        assert actual == [False, True, True]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestAbs:
    def test_abs_positive(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").abs())
        assert actual == [1, 2, 3]

    def test_abs_negative(self, backend_name, backend_factory, collect_expr):
        data = {"a": [-5, -10, 0]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").abs())
        assert actual == [5, 10, 0]

    def test_abs_floats(self, backend_name, backend_factory, collect_expr):
        data = {"a": [-1.5, 2.5, -3.0]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").abs())
        assert actual == pytest.approx([1.5, 2.5, 3.0])


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestSign:
    def test_sign_mixed(self, backend_name, backend_factory, collect_expr):
        data = {"a": [-5.0, 0.0, 3.0]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").sign())
        assert actual == pytest.approx([-1.0, 0.0, 1.0])


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestSqrt:
    def test_sqrt_perfect_squares(self, backend_name, backend_factory, collect_expr):
        data = {"a": [4.0, 9.0, 16.0, 25.0]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").sqrt())
        assert actual == pytest.approx([2.0, 3.0, 4.0, 5.0])

    def test_sqrt_zero(self, backend_name, backend_factory, collect_expr):
        data = {"a": [0.0, 1.0]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").sqrt())
        assert actual == pytest.approx([0.0, 1.0])


@pytest.mark.cross_backend
class TestCbrt:
    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_cbrt_basic(self, backend_name, backend_factory, collect_expr):
        data = {"a": [8.0, 27.0, 64.0]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").cbrt())
        assert actual == pytest.approx([2.0, 3.0, 4.0], rel=1e-6)

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_cbrt_negative(self, backend_name, backend_factory, collect_expr):
        data = {"a": [-8.0, -27.0]}
        df = backend_factory.create(data, backend_name)
        with expect_call_failure(
            when=backend_name in ('polars', 'polars-lazy', 'pandas', 'narwhals-polars', 'narwhals-pandas', 'narwhals-lazy', 'ibis-duckdb', 'ibis-sqlite'),
            reason='ma.col(x).cbrt() on negative inputs yields NaN across all backends',
            errors=(AssertionError,),
        ):
            actual = collect_expr(df, ma.col("a").cbrt())
            assert actual == pytest.approx([-2.0, -3.0], rel=1e-6)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestExp:
    def test_exp_basic(self, backend_name, backend_factory, collect_expr):
        data = {"a": [0.0, 1.0, 2.0]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").exp())
        assert actual == pytest.approx([1.0, math.e, math.e**2], rel=1e-9)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestLog:
    def test_log_base10(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1.0, 10.0, 100.0, 1000.0]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").log(10))
        assert actual == pytest.approx([0.0, 1.0, 2.0, 3.0], rel=1e-9)

    def test_log_base_e(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1.0, math.e, math.e**2]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").log(math.e))
        assert actual == pytest.approx([0.0, 1.0, 2.0], rel=1e-6)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestClip:
    def test_clip_basic(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1, 5, 10, 15, 20]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").clip(5, 15))
        assert actual == [5, 5, 10, 15, 15]

    def test_clip_floats(self, backend_name, backend_factory, collect_expr):
        data = {"a": [0.5, 1.5, 2.5]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").clip(1.0, 2.0))
        assert actual == pytest.approx([1.0, 1.5, 2.0])

    def test_clip_with_null(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1, None, 20]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").clip(5, 15))
        assert actual[0] == 5
        assert actual[1] is None
        assert actual[2] == 15


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestCot:
    def test_cot_basic(self, backend_name, backend_factory, collect_expr):
        data = {"a": [math.pi / 4, math.pi / 2]}
        df = backend_factory.create(data, backend_name)
        with expect_call_failure(
            when=backend_name in ('pandas', 'narwhals-polars', 'narwhals-pandas', 'narwhals-lazy'),
            reason='ma.col(x).cot() raises on pandas and all narwhals backends',
            errors=(NotImplementedError,),
        ):
            actual = collect_expr(df, ma.col("a").cot())
            assert actual[0] == pytest.approx(1.0, rel=1e-6)
            assert actual[1] == pytest.approx(0.0, abs=1e-10)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestDeclaredDecimalMath:
    """Mathematical methods are exercised from typed Decimal inputs."""


    def test_direct_decimal_roots(
        self, backend_name, declared_decimal_frame, backend_factory
    ):
        from decimal import Decimal as D
        from polars.exceptions import InvalidOperationError
        import polars as pl

        import mountainash as ma

        if backend_name == "ibis-sqlite":
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import (
                FKEY_MOUNTAINASH_SCALAR_VALUE,
            )

            source = backend_factory.create({"a": [0]}, backend_name)
            with pytest.raises(BackendCapabilityError) as error:
                ma.relation(source).select(
                    ma.col("a").cast(ma.DecimalDtype(10, 2), rounding="half_to_even").sqrt().alias("sqrt")
                ).to_polars()
            assert error.value.function_key is FKEY_MOUNTAINASH_SCALAR_VALUE.DECIMAL_CAST
            return

        frame = declared_decimal_frame(
            {"a": [D("0.00"), D("2.25"), D("9.00"), None]},
            {"a": (10, 2)},
        )
        values = ma.relation(frame).select(
            ma.col("a").sqrt().alias("sqrt"),
        ).to_polars()
        if backend_name in {"ibis-duckdb", }:
            assert values.schema["sqrt"] == pl.Decimal(10, 2)
        else:
            assert values.schema["sqrt"] == pl.Float64
        assert values["sqrt"].to_list()[0] == 0
        assert math.isclose(float(values["sqrt"][1]), 1.5)
        assert math.isclose(float(values["sqrt"][2]), 3.0)
        assert values["sqrt"][3] is None


    @pytest.mark.parametrize(
        "operation",
        [
            "exp", "ln", "log10", "log2", "log1p", "log_base_2",
            "cot", "cbrt", "sin", "cos", "tan", "asin", "acos", "atan",
            "sinh", "cosh", "tanh", "asinh", "acosh", "atanh",
            "radians", "degrees", "atan2",
        ],
    )
    def test_direct_decimal_math_method(
        self, backend_name, declared_decimal_frame, backend_factory, operation
    ):
        from decimal import Decimal as D
        from polars.exceptions import InvalidOperationError
        import polars as pl

        import mountainash as ma

        if backend_name == "ibis-sqlite":
            from mountainash.core.types import BackendCapabilityError
            frame = backend_factory.create({"a": [0.25]}, backend_name)
            with pytest.raises(BackendCapabilityError, match="fixed-precision decimal"):
                ma.relation(frame).select(
                    ma.col("a").cast(ma.DecimalDtype(10, 2), rounding="half_to_even")
                ).to_polars()
            return
        frame = declared_decimal_frame(
            {"a": [D("1.25"), D("1.50"), D("1.75"), None] if operation == "acosh"
             else [D("0.25"), D("0.50"), D("0.75"), None]},
            {"a": (10, 2)},
        )
        a = ma.col("a")
        if operation == "log_base_2":
            expression = a.log(2.0)
        elif operation == "atan2":
            expression = a.atan2(a)
        else:
            expression = getattr(a, operation)()

        trig = {
            "cot", "sin", "cos", "tan", "asin", "acos", "atan",
            "sinh", "cosh", "tanh", "asinh", "acosh", "atanh", "radians", "degrees",
        }
        inverse_hyperbolic = {"sinh", "cosh", "tanh", "asinh", "acosh", "atanh"}
        pandas_family = {"pandas", "narwhals-polars", "narwhals-lazy", "narwhals-pandas"}
        if backend_name in {"polars", "polars-lazy", } and operation == "cbrt":
            unsupported_error = InvalidOperationError
        elif backend_name in {"narwhals-polars", "narwhals-lazy"} and operation == "cbrt":
            from narwhals.exceptions import InvalidOperationError as NarwhalsInvalidOperationError
            unsupported_error = NarwhalsInvalidOperationError
        elif backend_name in pandas_family and operation in trig | {"acosh", "atan2"}:
            unsupported_error = NotImplementedError
        elif backend_name in {"polars", "polars-lazy"} and operation in trig:
            unsupported_error = InvalidOperationError
        elif backend_name == "ibis-duckdb" and operation in inverse_hyperbolic:
            unsupported_error = NotImplementedError
        else:
            unsupported_error = None

        with expect_call_failure(
            when=unsupported_error is not None,
            reason=f"direct Decimal {operation} has no native lowering on {backend_name}",
            errors=(unsupported_error,) if unsupported_error else (AssertionError,),
        ):
            result = ma.relation(frame).select(expression.alias("result")).to_polars()
            dtype = result.schema["result"]
            if backend_name.startswith("ibis") and operation not in {"cot", "atan2", "acosh", "log_base_2"}:
                assert dtype == pl.Decimal(10, 2)
            else:
                assert dtype == pl.Float64
            reference_fn = {
                "ln": math.log, "log_base_2": lambda x: math.log(x, 2),
                "acosh": lambda x: math.acosh(x + 1),
                "atan2": lambda x: math.atan2(x, x),
                "cot": lambda x: 1 / math.tan(x),
                "cbrt": lambda x: x ** (1 / 3),
            }.get(operation, getattr(math, operation, None))
            references = [reference_fn(x) for x in (0.25, 0.50, 0.75)]
            with expect_call_failure(
                when=dtype == pl.Decimal(10, 2),
                reason="307: Ibis native mathematical result extraction rounds to operand Decimal scale",
                errors=(AssertionError,),
            ):
                assert [float(x) for x in result["result"].to_list()[:3]] == pytest.approx(references)
            assert result["result"][3] is None

    @pytest.mark.parametrize(
        ("operation", "expected"),
        [
            ("sqrt", "0.500"),
            ("cbrt", "0.630"),
            ("negate", "-0.250"), ("abs", "0.250"), ("sign", "1.000"),
            ("ceil", "1.000"), ("floor", "0.000"), ("round", "0.000"),
            ("exp", "1.284"), ("ln", "-1.386"), ("log10", "-0.602"),
            ("log2", "-2.000"), ("log1p", "0.223"), ("log_base_2", "-2.000"),
            ("cot", "3.916"), ("sin", "0.247"), ("cos", "0.969"),
            ("tan", "0.255"), ("asin", "0.253"), ("acos", "1.318"),
            ("atan", "0.245"), ("sinh", "0.253"), ("cosh", "1.031"),
            ("tanh", "0.245"), ("asinh", "0.247"), ("acosh", "0.693"),
            ("atanh", "0.255"), ("radians", "0.004"), ("degrees", "14.324"),
            ("atan2", "0.785"),
        ],
    )
    def test_authored_float_math_then_decimal_cast(
        self, backend_name, declared_decimal_frame, backend_factory, operation, expected
    ):
        from decimal import Decimal as D
        import polars as pl

        import mountainash as ma
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import (
            FKEY_MOUNTAINASH_SCALAR_VALUE,
        )

        if backend_name == "ibis-sqlite":
            source = backend_factory.create(
                {"a": [0.25]}, backend_name
            )
            float_column = ma.col("a").cast("fp64")
        else:
            source = declared_decimal_frame(
                {"a": [D("0.25"), None]}, {"a": (10, 2)}
            )
            float_column = ma.col("a").cast("fp64")
        if operation == "negate":
            expression = -float_column
        elif operation == "log_base_2":
            expression = float_column.log(2.0)
        elif operation == "acosh":
            expression = (float_column + 1.0).acosh()
        elif operation == "atan2":
            expression = float_column.atan2(float_column)
        else:
            expression = getattr(float_column, operation)()

        unsupported_hyperbolic = operation in {
            "sinh", "cosh", "tanh", "asinh", "acosh", "atanh"
        } and backend_name in {"ibis-duckdb"}
        if backend_name == "ibis-sqlite":
            with pytest.raises(BackendCapabilityError) as error:
                ma.relation(source).select(
                    expression.cast(
                        ma.DecimalDtype(12, 3), rounding="half_to_even"
                    ).alias("result")
                ).to_polars()
            assert error.value.function_key is FKEY_MOUNTAINASH_SCALAR_VALUE.DECIMAL_CAST
            return
        if unsupported_hyperbolic:
            with expect_call_failure(
                when=True,
                reason=f"authored Float64 {operation} is unsupported on {backend_name}",
                errors=(NotImplementedError,),
            ):
                ma.relation(source).select(
                    expression.cast(
                        ma.DecimalDtype(12, 3), rounding="half_to_even"
                    ).alias("result")
                ).to_polars()
            return
        authored = ma.relation(source).select(
            expression.cast(
                ma.DecimalDtype(12, 3), rounding="half_to_even"
            ).alias("result")
        )
        if backend_name in {"pandas", "narwhals-polars", "narwhals-lazy", "narwhals-pandas"}:
            with expect_call_failure(
                when=True,
                reason="Narwhals final Decimal cast is refused (NW-MATH-11)",
                errors=(BackendCapabilityError,),
            ):
                authored.to_polars()
            return
        result = authored.to_polars()
        assert result.schema["result"] == pl.Decimal(12, 3)
        assert result["result"][0] == D(expected)
        assert result["result"][1] is None

    @pytest.mark.parametrize("working", [False, True], ids=["native-decimal", "authored-fp64"])
    @pytest.mark.parametrize(
        "operation",
        [
            "bitwise_not", "bitwise_and", "bitwise_or", "bitwise_xor",
            "shift_left", "shift_right", "shift_right_unsigned",
        ],
    )
    def test_integer_only_operations_do_not_coerce_decimal(
        self, backend_name, declared_decimal_frame, backend_factory, operation, working
    ):
        from decimal import Decimal as D
        from polars.exceptions import InvalidOperationError
        import pyarrow as pa

        import mountainash as ma
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import (
            FKEY_MOUNTAINASH_SCALAR_VALUE,
        )

        if backend_name == "ibis-sqlite":
            source = backend_factory.create({"a": [3]}, backend_name)
            with pytest.raises(BackendCapabilityError) as error:
                ma.relation(source).select(
                    ma.col("a").cast(ma.DecimalDtype(8, 0), rounding="half_to_even").alias("a")
                ).to_polars()
            assert error.value.function_key is FKEY_MOUNTAINASH_SCALAR_VALUE.DECIMAL_CAST
            return

        source = declared_decimal_frame({"a": [D("3.00")]}, {"a": (8, 2)})
        a = ma.col("a")
        if working:
            a = a.cast("fp64")
        if operation == "bitwise_not":
            expression = a.bitwise_not()
        elif operation == "bitwise_and":
            expression = a.bitwise_and(1)
        elif operation == "bitwise_or":
            expression = a.bitwise_or(1)
        elif operation == "bitwise_xor":
            expression = a.bitwise_xor(1)
        elif operation == "shift_left":
            expression = a.shift_left(1)
        elif operation == "shift_right":
            expression = a.shift_right(1)
        else:
            expression = a.shift_right_unsigned(1)

        if operation == "bitwise_not":
            if backend_name in {"polars", "polars-lazy", "narwhals-polars", "narwhals-lazy"}:
                error_type = InvalidOperationError
            elif backend_name in {"pandas", "narwhals-pandas"}:
                error_type = pa.ArrowNotImplementedError
            else:
                error_type = TypeError
        elif operation in {"bitwise_and", "bitwise_or"}:
            if backend_name in {"polars", "polars-lazy", "narwhals-polars", "narwhals-lazy"}:
                error_type = InvalidOperationError
            else:
                error_type = TypeError
        elif operation == "bitwise_xor":
            if backend_name in {"polars", "polars-lazy"}:
                error_type = InvalidOperationError
            elif backend_name.startswith("narwhals") or backend_name == "pandas":
                error_type = BackendCapabilityError
            else:
                error_type = TypeError
        elif operation in {"shift_left", "shift_right"}:
            error_type = (
                BackendCapabilityError
                if backend_name in {
                    "polars", "polars-lazy", "narwhals-polars",
                    "narwhals-lazy", "narwhals-pandas", "pandas",
                }
                else TypeError
            )
        else:
            error_type = BackendCapabilityError

        if error_type is InvalidOperationError and backend_name in {"narwhals-polars", "narwhals-lazy"}:
            from narwhals.exceptions import InvalidOperationError as NarwhalsInvalidOperationError
            error_type = NarwhalsInvalidOperationError
        with expect_call_failure(
            when=True,
            reason=f"{operation} is integer-only and rejects native Decimal on {backend_name}",
            errors=(error_type,),
        ):
            ma.relation(source).select(expression.alias("result")).to_polars()

    @pytest.mark.parametrize(
        ("n", "expected"),
        [
            (1, [None, 2.0, 1.0, None, None, None]),
            (2, [None, None, 5.0, None, None, 1.0]),
        ],
    )
    def test_decimal_pct_change_keeps_partition_and_order_semantics(
        self, backend_name, declared_decimal_frame, backend_factory, n, expected
    ):
        from decimal import Decimal as D

        import mountainash as ma
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import (
            FKEY_MOUNTAINASH_SCALAR_VALUE,
        )
        from ibis.common.exceptions import OperationNotDefinedError
        import polars as pl

        if backend_name == "ibis-sqlite":
            source = backend_factory.create({"a": [2]}, backend_name)
            with pytest.raises(BackendCapabilityError) as error:
                ma.relation(source).select(
                    ma.col("a").cast(ma.DecimalDtype(10, 2), rounding="half_to_even")
                ).to_polars()
            assert error.value.function_key is FKEY_MOUNTAINASH_SCALAR_VALUE.DECIMAL_CAST
            return

        frame = declared_decimal_frame(
            {
                "a": [D("12.00"), D("2.00"), D("6.00"),
                      D("6.00"), D("3.00"), None],
                "group": ["A", "A", "A", "B", "B", "B"],
                "idx": [2, 0, 1, 2, 0, 1],
            },
            {"a": (10, 2)},
        )
        error_type = (
            NotImplementedError
            if n > 1 and backend_name in {
                "pandas", "narwhals-polars", "narwhals-lazy", "narwhals-pandas"
            }
            else None
        )
        with expect_call_failure(
            when=error_type is not None,
            reason=(
                "Narwhals diff(n>1) is unsupported"
            ),
            errors=(error_type,) if error_type else (AssertionError,),
        ):
            result = ma.relation(frame).select(
                ma.col("group"), ma.col("idx"),
                ma.col("a").pct_change(n=n).over("group", order_by="idx").alias("change")
            ).sort("group", "idx").to_polars()
            if backend_name in {
                "polars", "polars-lazy", "narwhals-polars", "narwhals-lazy"
            }:
                assert result.schema["change"] == pl.Decimal(38, 2)
            elif backend_name in {"pandas", "narwhals-pandas"}:
                assert result.schema["change"] == pl.Decimal(22, 11)
            else:
                assert result.schema["change"] == pl.Float64
            assert result["change"].to_list() == expected


    def test_authored_pct_change_then_decimal_cast(
        self, backend_name, declared_decimal_frame, backend_factory
    ):
        from decimal import Decimal as D
        import polars as pl

        import mountainash as ma
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import (
            FKEY_MOUNTAINASH_SCALAR_VALUE,
        )

        if backend_name == "ibis-sqlite":
            source = backend_factory.create(
                {"a": [2.0, 3.0], "group": ["A", "A"], "idx": [0, 1]},
                backend_name,
            )
            with pytest.raises(BackendCapabilityError) as error:
                ma.relation(source).select(
                    ma.col("a")
                    .cast("fp64")
                    .pct_change()
                    .over("group", order_by="idx")
                    .cast(ma.DecimalDtype(12, 3), rounding="half_to_even")
                    .alias("change")
                ).to_polars()
            assert error.value.function_key is FKEY_MOUNTAINASH_SCALAR_VALUE.DECIMAL_CAST
            return

        source = declared_decimal_frame(
            {
                "a": [D("12.00"), D("2.00"), D("6.00"),
                      D("6.00"), D("3.00"), None],
                "group": ["A", "A", "A", "B", "B", "B"],
                "idx": [2, 0, 1, 2, 0, 1],
            },
            {"a": (10, 2)},
        )
        authored = ma.relation(source).select(
            ma.col("group"), ma.col("idx"),
            ma.col("a")
            .cast("fp64")
            .pct_change()
            .over("group", order_by="idx")
            .cast(ma.DecimalDtype(12, 3), rounding="half_to_even")
            .alias("change")
        ).sort("group", "idx")
        if backend_name in {"pandas", "narwhals-polars", "narwhals-lazy", "narwhals-pandas"}:
            with expect_call_failure(
                when=True,
                reason="Narwhals final Decimal cast is refused (NW-MATH-11)",
                errors=(BackendCapabilityError,),
            ):
                authored.to_polars()
            return
        result = authored.to_polars()
        assert result.schema["change"] == pl.Decimal(12, 3)
        assert result["change"].to_list() == [
            None, D("2.000"), D("1.000"), None, None, None
        ]
    def test_pct_change_window_does_not_bind_unrelated_lag_sibling(
        self, backend_name, backend_factory
    ):
        import mountainash as ma

        source = backend_factory.create(
            {
                "a": [2.0, 3.0, 6.0],
                "group": ["A", "A", "A"],
                "idx": [0, 1, 2],
            },
            backend_name,
        )
        relation = ma.relation(source).select(
            ma.col("a").pct_change().over("group", order_by="idx").alias("change"),
            ma.col("a").lag().alias("unbound_lag"),
        )
        with pytest.raises(ValueError, match="requires .over"):
            relation.to_polars()

    def test_direct_decimal_invalid_sqrt_domain(
        self, backend_name, declared_decimal_frame, backend_factory
    ):
        import duckdb
        from decimal import Decimal as D

        import mountainash as ma

        if backend_name == "ibis-sqlite":
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import (
                FKEY_MOUNTAINASH_SCALAR_VALUE,
            )

            source = backend_factory.create({"a": [-1]}, backend_name)
            query = ma.relation(source).select(
                ma.col("a").cast(ma.DecimalDtype(8, 2), rounding="half_to_even").sqrt().alias("root")
            )
            with pytest.raises(BackendCapabilityError) as error:
                query.to_polars()
            assert error.value.function_key is FKEY_MOUNTAINASH_SCALAR_VALUE.DECIMAL_CAST
            return

        frame = declared_decimal_frame({"a": [D("-1.00")]}, {"a": (8, 2)})
        query = ma.relation(frame).select(ma.col("a").sqrt().alias("root"))
        if backend_name == "ibis-duckdb":
            with pytest.raises(duckdb.OutOfRangeException):
                query.to_polars()
        else:
            value = query.to_polars()["root"][0]
            if backend_name in {"pandas", "narwhals-pandas"}:
                assert value is None
            else:
                assert math.isnan(value)

    @pytest.mark.parametrize("operation", ["asin", "acos"])
    def test_authored_float_inverse_trig_domain(
        self, backend_name, declared_decimal_frame, backend_factory, operation
    ):
        import duckdb
        from decimal import Decimal as D
        from mountainash.core.types import BackendCapabilityError
        import polars as pl

        import mountainash as ma

        if backend_name == "ibis-sqlite":
            source = backend_factory.create({"a": [-2.0]}, backend_name)
            with pytest.raises(BackendCapabilityError):
                ma.relation(source).select(
                    ma.col("a").cast(ma.DecimalDtype(10, 2), rounding="half_to_even").cast("fp64")
                ).to_polars()
            return
        if backend_name in {"pandas", "narwhals-polars", "narwhals-lazy", "narwhals-pandas"}:
            source = declared_decimal_frame(
                {"a": [D("-2.00"), D("2.00")]}, {"a": (8, 2)}
            )
            with expect_call_failure(
                when=True,
                reason=f"authored Float64 {operation} is unsupported on Narwhals",
                errors=(NotImplementedError,),
            ):
                ma.relation(source).select(
                    getattr(ma.col("a").cast("fp64"), operation)().alias("value")
                ).to_polars()
            return
        source = declared_decimal_frame(
            {"a": [D("-2.00"), D("2.00")]}, {"a": (8, 2)}
        )
        query = ma.relation(source).select(
            getattr(ma.col("a").cast("fp64"), operation)().alias("value")
        )
        if backend_name == "ibis-duckdb":
            with pytest.raises(duckdb.InvalidInputException):
                query.to_polars()
        else:
            values = query.to_polars()
            assert values.schema["value"] == pl.Float64
            assert math.isnan(values["value"][0])
            assert math.isnan(values["value"][1])

    @pytest.mark.parametrize("value", ["-1.00", "0.00"])
    def test_direct_decimal_invalid_log_domains(
        self, backend_name, declared_decimal_frame, backend_factory, value
    ):
        import duckdb
        from decimal import Decimal as D

        import mountainash as ma

        if backend_name == "ibis-sqlite":
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import (
                FKEY_MOUNTAINASH_SCALAR_VALUE,
            )

            source = backend_factory.create({"a": [-1]}, backend_name)
            query = ma.relation(source).select(
                ma.col("a").cast(ma.DecimalDtype(8, 2), rounding="half_to_even").ln().alias("log")
            )
            with pytest.raises(BackendCapabilityError) as error:
                query.to_polars()
            assert error.value.function_key is FKEY_MOUNTAINASH_SCALAR_VALUE.DECIMAL_CAST
            return

        frame = declared_decimal_frame(
            {"a": [D(value)]}, {"a": (8, 2)}
        )
        query = ma.relation(frame).select(ma.col("a").ln().alias("log"))
        if backend_name == "ibis-duckdb":
            with pytest.raises(duckdb.OutOfRangeException):
                query.to_polars()
        else:
            result = query.to_polars()["log"][0]
            if D(value) < 0:
                assert math.isnan(result)
            else:
                assert result == -math.inf

    def test_invalid_sqrt_separates_float_domain_from_final_decimal_cast(
        self, backend_name, declared_decimal_frame, backend_factory
    ):
        import duckdb
        from decimal import Decimal as D
        from polars.exceptions import InvalidOperationError

        import mountainash as ma
        from mountainash.core.types import BackendCapabilityError

        if backend_name == "ibis-sqlite":
            source = backend_factory.create({"a": [-1.0]}, backend_name)
        else:
            source = declared_decimal_frame(
                {"a": [D("-1.00"), D("0.00")]}, {"a": (8, 2)}
            )
        query = ma.relation(source).select(
            ma.col("a")
            .cast("fp64")
            .sqrt()
            .cast(ma.DecimalDtype(12, 3), rounding="half_to_even")
            .alias("root")
        )
        if backend_name in {
            "ibis-sqlite", "pandas", "narwhals-polars", "narwhals-lazy",
            "narwhals-pandas",
        }:
            with pytest.raises(BackendCapabilityError):
                query.to_polars()
        elif backend_name == "ibis-duckdb":
            with pytest.raises(duckdb.OutOfRangeException):
                query.to_polars()
        else:
            with pytest.raises(InvalidOperationError):
                query.to_polars()

    def test_factorial_is_an_explicit_unsupported_operation(
        self, backend_name, declared_decimal_frame, backend_factory
    ):
        import mountainash as ma

        if backend_name == "ibis-sqlite":
            source = backend_factory.create({"a": [3]}, backend_name)
            expression = ma.col("a")
        else:
            from decimal import Decimal as D

            source = declared_decimal_frame(
                {"a": [D("3")]}, {"a": (8, 0)}
            )
            expression = ma.col("a")

        # Every backend lowering has an existing explicit NotImplementedError;
        # the generic API builder must not silently return None instead.
        with pytest.raises(NotImplementedError, match="factorial"):
            ma.relation(source).select(
                expression.factorial().alias("factorial")
            ).to_polars()

        with pytest.raises(NotImplementedError, match="factorial"):
            ma.relation(source).select(
                expression.cast("fp64").factorial().alias("factorial")
            ).to_polars()
