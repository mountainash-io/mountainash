"""Argument channel tests for arithmetic operations."""
from __future__ import annotations

import pytest
import polars as pl
import _duckdb

import mountainash as ma
from mountainash.core.errors import InvalidOptionValueError

from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_ARITHMETIC as FK_ARITH,
    FKEY_MOUNTAINASH_SCALAR_ARITHMETIC as FK_MA_ARITH,
)
from expressions.argument_types.conftest import ALL_BACKENDS, make_df
from expressions.argument_types._option_helpers import (
    OptionProbeDidNotDiscriminateError,
    OptionSpec,
    option_result,
    xfail_option_unsupported,
)
from expressions.argument_types.option_disposition import (
    OPTION_DISPOSITIONS,
    REGISTERED_OPTION_PROBES,
    OptionCell,
    OptionProbeRegistration,
    param_taxonomy,
)
from expressions.argument_types._test_template import (
    INPUT_TYPES,
    OpSpec,
    run_argument_matrix,
    xfail_if_limited,
)

TESTED_PARAMS: list[tuple] = [
    (FK_ARITH.ABS, "x"),
    (FK_ARITH.ACOS, "x"),
    (FK_ARITH.ACOSH, "x"),
    (FK_ARITH.ADD, "x"),
    (FK_ARITH.ADD, "y"),
    (FK_ARITH.ASIN, "x"),
    (FK_ARITH.ASINH, "x"),
    (FK_ARITH.ATAN, "x"),
    (FK_ARITH.ATAN2, "x"),
    (FK_ARITH.ATAN2, "y"),
    (FK_ARITH.ATANH, "x"),
    (FK_ARITH.BITWISE_AND, "x"),
    (FK_ARITH.BITWISE_AND, "y"),
    (FK_ARITH.BITWISE_NOT, "x"),
    (FK_ARITH.BITWISE_OR, "x"),
    (FK_ARITH.BITWISE_OR, "y"),
    (FK_ARITH.BITWISE_XOR, "x"),
    (FK_ARITH.BITWISE_XOR, "y"),
    (FK_ARITH.COS, "x"),
    (FK_ARITH.COSH, "x"),
    (FK_ARITH.DEGREES, "x"),
    (FK_ARITH.DIVIDE, "x"),
    (FK_ARITH.DIVIDE, "y"),
    (FK_ARITH.EXP, "x"),
    ("factorial", "n"),
    (FK_MA_ARITH.FLOOR_DIVIDE, "x"),
    (FK_MA_ARITH.FLOOR_DIVIDE, "y"),
    (FK_ARITH.MODULO, "x"),
    (FK_ARITH.MODULO, "y"),
    (FK_ARITH.MULTIPLY, "x"),
    (FK_ARITH.MULTIPLY, "y"),
    (FK_ARITH.NEGATE, "x"),
    (FK_ARITH.POWER, "x"),
    (FK_ARITH.POWER, "y"),
    (FK_ARITH.RADIANS, "x"),
    (FK_ARITH.SHIFT_LEFT, "base"),
    (FK_ARITH.SHIFT_LEFT, "shift"),
    (FK_ARITH.SHIFT_RIGHT, "base"),
    (FK_ARITH.SHIFT_RIGHT, "shift"),
    (FK_ARITH.SHIFT_RIGHT_UNSIGNED, "base"),
    (FK_ARITH.SHIFT_RIGHT_UNSIGNED, "shift"),
    (FK_ARITH.SIGN, "x"),
    (FK_ARITH.SIN, "x"),
    (FK_ARITH.SINH, "x"),
    (FK_ARITH.SQRT, "x"),
    (FK_ARITH.SUBTRACT, "x"),
    (FK_ARITH.SUBTRACT, "y"),
    (FK_ARITH.TAN, "x"),
    (FK_ARITH.TANH, "x"),
]


_ARITH_PROTOCOL = "SubstraitScalarArithmeticExpressionSystemProtocol"
_ABS_VALUES = ("ERROR", "SATURATE", "SILENT")
_ABS_PROBE_EXEMPT = {
    (backend, "SILENT")
    for backend in ("polars", "narwhals-polars", "narwhals-pandas")
}
_ABS_DECLARED = {
    (backend, value)
    for backend in ALL_BACKENDS
    for value in _ABS_VALUES
    if (backend, value) not in _ABS_PROBE_EXEMPT
}


OPTION_DISPOSITIONS.extend(
    OptionCell(
        FK_ARITH.ABS,
        _ARITH_PROTOCOL,
        "abs",
        "overflow",
        backend,
        value,
        "int8",
        "probe_exempt" if (backend, value) in _ABS_PROBE_EXEMPT else "declared_unsupported",
        (
            "explicit SILENT selects the native wrapping behavior and is "
            "indistinguishable from omission"
            if (backend, value) in _ABS_PROBE_EXEMPT
            else "native behavior does not implement the requested overflow mode"
        ),
    )
    for backend in ALL_BACKENDS
    for value in _ABS_VALUES
)


def _abs_probe(value: str) -> OptionSpec:
    return OptionSpec(
        FK_ARITH.ABS,
        "overflow",
        value,
        "int8",
        lambda value=value: ma.col("v").abs(overflow=value),
        lambda: ma.col("v").abs(),
        {"v": [-128]},
        schema={"v": pl.Int8},
    )


REGISTERED_OPTION_PROBES.extend(
    OptionProbeRegistration(
        _abs_probe(value),
        backend,
        "declared_unsupported",
        (
            _duckdb.OutOfRangeException
            if backend == "ibis"
            else OptionProbeDidNotDiscriminateError
        ),
    )
    for backend, value in sorted(_ABS_DECLARED)
)


_OVERFLOW_SPECS = {
    "add": OptionSpec(
        FK_ARITH.ADD,
        "overflow",
        "",
        "int8",
        lambda: ma.col("v").add(ma.col("w"), overflow=""),
        lambda: ma.col("v").add(ma.col("w")),
        {"v": [127], "w": [1]},
        schema={"v": pl.Int8, "w": pl.Int8},
    ),
    "subtract": OptionSpec(
        FK_ARITH.SUBTRACT,
        "overflow",
        "",
        "int8",
        lambda: ma.col("v").subtract(ma.col("w"), overflow=""),
        lambda: ma.col("v").subtract(ma.col("w")),
        {"v": [-128], "w": [1]},
        schema={"v": pl.Int8, "w": pl.Int8},
    ),
    "multiply": OptionSpec(
        FK_ARITH.MULTIPLY,
        "overflow",
        "",
        "int8",
        lambda: ma.col("v").multiply(ma.col("w"), overflow=""),
        lambda: ma.col("v").multiply(ma.col("w")),
        {"v": [64], "w": [2]},
        schema={"v": pl.Int8, "w": pl.Int8},
    ),
    "divide": OptionSpec(
        FK_ARITH.DIVIDE,
        "overflow",
        "",
        "int8",
        lambda: ma.col("v").divide(ma.col("w"), overflow=""),
        lambda: ma.col("v").divide(ma.col("w")),
        {"v": [-128], "w": [-1]},
        schema={"v": pl.Int8, "w": pl.Int8},
    ),
    "modulus": OptionSpec(
        FK_ARITH.MODULO,
        "overflow",
        "",
        "int8",
        lambda: ma.col("v").modulus(ma.col("w"), overflow=""),
        lambda: ma.col("v").modulus(ma.col("w")),
        {"v": [-128], "w": [-1]},
        schema={"v": pl.Int8, "w": pl.Int8},
    ),
    "negate": OptionSpec(
        FK_ARITH.NEGATE,
        "overflow",
        "",
        "int8",
        lambda: ma.col("v").negate(overflow=""),
        lambda: ma.col("v").negate(),
        {"v": [-128]},
        schema={"v": pl.Int8},
    ),
    "power": OptionSpec(
        FK_ARITH.POWER,
        "overflow",
        "",
        "int64",
        lambda: ma.col("v").power(ma.col("w"), overflow=""),
        lambda: ma.col("v").power(ma.col("w")),
        # 2**63 is exactly one above signed Int64 max (2**63 - 1).
        {"v": [2], "w": [63]},
        schema={"v": pl.Int64, "w": pl.Int64},
    ),
}
_WRAPPING_OVERFLOW_OPS = frozenset(_OVERFLOW_SPECS) - {"divide"}
_OVERFLOW_PROBE_EXEMPT = {
    (op, backend, "SILENT")
    for op in _WRAPPING_OVERFLOW_OPS
    for backend in ("polars", "narwhals-polars", "narwhals-pandas")
}
_OVERFLOW_DECLARED = {
    (op, backend, value)
    for op in _OVERFLOW_SPECS
    for backend in ALL_BACKENDS
    for value in _ABS_VALUES
    if (op, backend, value) not in _OVERFLOW_PROBE_EXEMPT
}


def _overflow_probe(op: str, value: str) -> OptionSpec:
    template = _OVERFLOW_SPECS[op]
    builders = {
        "add": lambda: ma.col("v").add(ma.col("w"), overflow=value),
        "subtract": lambda: ma.col("v").subtract(ma.col("w"), overflow=value),
        "multiply": lambda: ma.col("v").multiply(ma.col("w"), overflow=value),
        "divide": lambda: ma.col("v").divide(ma.col("w"), overflow=value),
        "modulus": lambda: ma.col("v").modulus(ma.col("w"), overflow=value),
        "negate": lambda: ma.col("v").negate(overflow=value),
        "power": lambda: ma.col("v").power(ma.col("w"), overflow=value),
    }
    return OptionSpec(
        template.fkey,
        template.option_param,
        value,
        template.dtype,
        builders[op],
        template.reference_expr,
        template.data,
        template.schema,
    )


OPTION_DISPOSITIONS.extend(
    OptionCell(
        _OVERFLOW_SPECS[op].fkey,
        _ARITH_PROTOCOL,
        op,
        "overflow",
        backend,
        value,
        _OVERFLOW_SPECS[op].dtype,
        (
            "probe_exempt"
            if (op, backend, value) in _OVERFLOW_PROBE_EXEMPT
            else "declared_unsupported"
        ),
        (
            "explicit SILENT selects native i64 power wrapping and is "
            "indistinguishable from omission"
            if op == "power"
            and (op, backend, value) in _OVERFLOW_PROBE_EXEMPT
            else "explicit SILENT selects native integer wrapping and is "
            "indistinguishable from omission"
            if (op, backend, value) in _OVERFLOW_PROBE_EXEMPT
            else "native behavior does not implement the pinned i64 power "
            "overflow mode"
            if op == "power"
            else "native behavior does not implement the requested overflow mode"
        ),
    )
    for op in _OVERFLOW_SPECS
    for backend in ALL_BACKENDS
    for value in _ABS_VALUES
)


_IBIS_OVERFLOW_ERRORS = frozenset(
    {"add", "subtract", "multiply", "modulus", "negate"}
)
REGISTERED_OPTION_PROBES.extend(
    OptionProbeRegistration(
        _overflow_probe(op, value),
        backend,
        "declared_unsupported",
        (
            _duckdb.OutOfRangeException
            if backend == "ibis" and op in _IBIS_OVERFLOW_ERRORS
            else OptionProbeDidNotDiscriminateError
        ),
    )
    for op, backend, value in sorted(_OVERFLOW_DECLARED)
)


def test_power_overflow_probe_uses_pinned_int64_boundary() -> None:
    spec = _OVERFLOW_SPECS["power"]

    assert spec.dtype == "int64"
    assert spec.data == {"v": [2], "w": [63]}
    assert spec.schema == {"v": pl.Int64, "w": pl.Int64}


TESTED_OPTION_PARAMS = [
    (
        _ARITH_PROTOCOL,
        "abs",
        "overflow",
        param_taxonomy(_ARITH_PROTOCOL, "abs", "overflow"),
    ),
    *(
        (
            _ARITH_PROTOCOL,
            op,
            "overflow",
            param_taxonomy(_ARITH_PROTOCOL, op, "overflow"),
        )
        for op in _OVERFLOW_SPECS
    ),
]


@pytest.mark.parametrize(
    "op,backend,value",
    sorted(_OVERFLOW_DECLARED),
    ids=lambda value: str(value),
)
def test_arithmetic_overflow_declared_unsupported(op, backend, value, request):
    spec = _overflow_probe(op, value)
    request.applymarker(
        xfail_option_unsupported(spec.fkey, "overflow", value, backend)
    )
    df = make_df(spec.data, backend, schema=spec.schema)
    got = option_result(df, spec.build_expr(), backend)
    assert got != option_result(df, spec.reference_expr(), backend)


@pytest.mark.parametrize(
    "op,backend",
    sorted({case[:2] for case in _OVERFLOW_PROBE_EXEMPT}),
)
def test_arithmetic_overflow_silent_matches_native_wrapping(op, backend):
    spec = _overflow_probe(op, "SILENT")
    df = make_df(spec.data, backend, schema=spec.schema)
    assert option_result(df, spec.build_expr(), backend) == option_result(
        df, spec.reference_expr(), backend
    )


@pytest.mark.parametrize("op", sorted(_OVERFLOW_SPECS))
@pytest.mark.parametrize("value", ["WRAP", "error", ""])
def test_arithmetic_overflow_rejects_invalid_value_at_build_time(op, value):
    with pytest.raises(InvalidOptionValueError):
        _overflow_probe(op, value).build_expr()


@pytest.mark.parametrize(
    "backend,value",
    sorted(_ABS_DECLARED),
    ids=lambda value: str(value),
)
def test_abs_overflow_declared_unsupported(backend, value, request):
    request.applymarker(
        xfail_option_unsupported(FK_ARITH.ABS, "overflow", value, backend)
    )
    df = make_df({"v": [-128]}, backend, schema={"v": pl.Int8})
    got = option_result(df, ma.col("v").abs(overflow=value), backend)
    assert got == [128]


@pytest.mark.parametrize("backend", sorted({case[0] for case in _ABS_PROBE_EXEMPT}))
def test_abs_overflow_silent_matches_native_wrapping(backend):
    df = make_df({"v": [-128]}, backend, schema={"v": pl.Int8})
    assert option_result(df, ma.col("v").abs(overflow="SILENT"), backend) == [-128]


@pytest.mark.parametrize("value", ["WRAP", "error", ""])
def test_abs_overflow_rejects_invalid_value_at_build_time(value):
    with pytest.raises(InvalidOptionValueError):
        ma.col("v").abs(overflow=value)

OP_SPECS: list[OpSpec] = [
    OpSpec(
        function_key=FK_ARITH.ADD,
        op_name="add",
        build=lambda col, arg: col.add(arg),
        raw_arg=10,
        arg_col_name="b",
        param_name="y",
        input_col="a",
        data={"a": [1, 2, 3], "b": [10, 20, 30]},
    ),
    OpSpec(
        function_key=FK_ARITH.SUBTRACT,
        op_name="subtract",
        build=lambda col, arg: col.sub(arg),
        raw_arg=1,
        arg_col_name="b",
        param_name="y",
        input_col="a",
        data={"a": [10, 20, 30], "b": [1, 2, 3]},
    ),
    OpSpec(
        function_key=FK_ARITH.MULTIPLY,
        op_name="multiply",
        build=lambda col, arg: col.mul(arg),
        raw_arg=2,
        arg_col_name="b",
        param_name="y",
        input_col="a",
        data={"a": [1, 2, 3], "b": [2, 3, 4]},
    ),
    OpSpec(
        function_key=FK_ARITH.DIVIDE,
        op_name="divide",
        build=lambda col, arg: col.truediv(arg),
        raw_arg=2,
        arg_col_name="b",
        param_name="y",
        input_col="a",
        data={"a": [10, 20, 30], "b": [2, 5, 10]},
    ),
    OpSpec(
        function_key=FK_MA_ARITH.FLOOR_DIVIDE,
        op_name="floor_divide",
        build=lambda col, arg: col.floordiv(arg),
        raw_arg=3,
        arg_col_name="b",
        param_name="y",
        input_col="a",
        data={"a": [10, 20, 30], "b": [3, 7, 4]},
    ),
    OpSpec(
        function_key=FK_ARITH.POWER,
        op_name="power",
        build=lambda col, arg: col.pow(arg),
        raw_arg=2,
        arg_col_name="b",
        param_name="y",
        input_col="a",
        data={"a": [2, 3, 4], "b": [2, 3, 2]},
    ),
    OpSpec(
        function_key=FK_ARITH.MODULO,
        op_name="modulus",
        build=lambda col, arg: col.mod(arg),
        raw_arg=3,
        arg_col_name="b",
        param_name="y",
        input_col="a",
        data={"a": [10, 21, 30], "b": [3, 4, 7]},
    ),
    OpSpec(
        function_key=FK_ARITH.ATAN2,
        op_name="atan2",
        build=lambda col, arg: col.atan2(arg),
        raw_arg=1.0,
        arg_col_name="b",
        param_name="y",
        input_col="a",
        data={"a": [1.0, 2.0, 3.0], "b": [0.5, 1.0, 1.5]},
    ),
]

# atan2 raises NotImplementedError on both narwhals backends (not a registry-tracked
# limitation); mark all input types as xfail for those backends.
_ATAN2_NW_XFAIL = pytest.mark.xfail(
    strict=True,
    raises=NotImplementedError,
    reason="atan2() is not supported by the Narwhals backend.",
)
_ATAN2_NW_BACKENDS = {"narwhals-polars", "narwhals-pandas"}


def _params():
    cases = []
    for op in OP_SPECS:
        for bk in ALL_BACKENDS:
            for it in INPUT_TYPES:
                mark = xfail_if_limited(bk, op.function_key, op.param_name, it)
                marks = [mark] if mark else []
                if op.op_name == "atan2" and bk in _ATAN2_NW_BACKENDS:
                    marks = [_ATAN2_NW_XFAIL]
                cases.append(
                    pytest.param(op, bk, it, marks=marks, id=f"{op.op_name}-{bk}-{it}")
                )
    return cases


if OP_SPECS:

    @pytest.mark.parametrize("op,backend,input_type", _params())
    def test_argument_channel(op: OpSpec, backend: str, input_type: str):
        run_argument_matrix(op, backend, input_type)
