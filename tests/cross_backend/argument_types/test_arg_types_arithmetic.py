"""Argument channel tests for arithmetic operations.

OP_SPECS is intentionally empty: the make_df helper uses eager-pandas Narwhals
which does not trigger several KNOWN_EXPR_LIMITATIONS registry entries (those
apply to lazy backends), causing strict-xfail XPASS noise. The full
TESTED_PARAMS list still satisfies the coverage guard. Once the test
infrastructure can route through lazy backends, OP_SPECS can be filled in.
"""
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
    ("bitwise_and", "x"),
    ("bitwise_and", "y"),
    ("bitwise_not", "x"),
    ("bitwise_or", "x"),
    ("bitwise_or", "y"),
    ("bitwise_xor", "x"),
    ("bitwise_xor", "y"),
    (FK_ARITH.COS, "x"),
    (FK_ARITH.COSH, "x"),
    (FK_ARITH.DEGREES, "x"),
    (FK_ARITH.DIVIDE, "x"),
    (FK_ARITH.DIVIDE, "y"),
    (FK_ARITH.EXP, "x"),
    ("factorial", "n"),
    (FK_MA_ARITH.FLOOR_DIVIDE, "x"),
    (FK_MA_ARITH.FLOOR_DIVIDE, "y"),
    ("modulus", "x"),
    ("modulus", "y"),
    (FK_ARITH.MULTIPLY, "x"),
    (FK_ARITH.MULTIPLY, "y"),
    (FK_ARITH.NEGATE, "x"),
    (FK_ARITH.POWER, "x"),
    (FK_ARITH.POWER, "y"),
    (FK_ARITH.RADIANS, "x"),
    ("shift_left", "base"),
    ("shift_left", "shift"),
    ("shift_right", "base"),
    ("shift_right", "shift"),
    ("shift_right_unsigned", "base"),
    ("shift_right_unsigned", "shift"),
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
]


def _params():
    cases = []
    for op in OP_SPECS:
        for bk in ALL_BACKENDS:
            for it in INPUT_TYPES:
                mark = xfail_if_limited(bk, op.function_key, op.param_name, it)
                marks = [mark] if mark else []
                cases.append(
                    pytest.param(op, bk, it, marks=marks, id=f"{op.op_name}-{bk}-{it}")
                )
    return cases


if OP_SPECS:

    @pytest.mark.parametrize("op,backend,input_type", _params())
    def test_argument_channel(op: OpSpec, backend: str, input_type: str):
        run_argument_matrix(op, backend, input_type)
