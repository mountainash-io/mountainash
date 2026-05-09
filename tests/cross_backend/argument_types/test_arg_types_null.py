"""Argument channel tests for null operations."""
from __future__ import annotations

import pytest

from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_NULL as FK_NULL,
)
from cross_backend.argument_types.conftest import ALL_BACKENDS
from cross_backend.argument_types._test_template import (
    INPUT_TYPES,
    OpSpec,
    run_argument_matrix,
    xfail_if_limited,
)

TESTED_PARAMS: list[tuple] = [
    (FK_NULL.FILL_NAN, "replacement"),
    (FK_NULL.FILL_NULL, "replacement"),
    (FK_NULL.NULL_IF, "condition"),
]

OP_SPECS: list[OpSpec] = [
    OpSpec(
        function_key=FK_NULL.FILL_NULL,
        op_name="fill_null",
        build=lambda col, arg: col.fill_null(arg),
        raw_arg=0,
        arg_col_name="b",
        param_name="replacement",
        input_col="a",
        data={"a": [1, 2, 3], "b": [0, 0, 0]},
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
