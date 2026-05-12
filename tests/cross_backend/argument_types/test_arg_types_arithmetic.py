"""Argument channel tests for arithmetic operations."""
from __future__ import annotations

import pytest

from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_ARITHMETIC as FK_ARITH,
    FKEY_MOUNTAINASH_SCALAR_ARITHMETIC as FK_MA_ARITH,
)
from cross_backend.argument_types.conftest import ALL_BACKENDS
from cross_backend.argument_types._test_template import (
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
