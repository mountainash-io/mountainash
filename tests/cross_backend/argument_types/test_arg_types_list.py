"""Argument channel tests for list operations."""
from __future__ import annotations

import pytest

from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_LIST as FK_LIST,
)
from cross_backend.argument_types.conftest import ALL_BACKENDS
from cross_backend.argument_types._test_template import (
    INPUT_TYPES,
    OpSpec,
    run_argument_matrix,
    xfail_if_limited,
)

TESTED_PARAMS: list[tuple] = [
    ("list_contains", "item"),
    ("list_contains", "x"),
    ("list_explode", "x"),
    ("list_get", "x"),
    ("list_join", "x"),
    ("list_len", "x"),
    ("list_max", "x"),
    ("list_mean", "x"),
    ("list_min", "x"),
    ("list_sort", "x"),
    ("list_sum", "x"),
    ("list_unique", "x"),
]

OP_SPECS: list[OpSpec] = [
    OpSpec(
        function_key=FK_LIST.CONTAINS,
        op_name="list_contains_item",
        build=lambda col, arg: col.list.contains(arg),
        raw_arg=2,
        arg_col_name="item",
        param_name="item",
        input_col="a",
        data={"a": [[1, 2, 3], [4, 5, 6], [7, 8, 9]], "item": [2, 5, 1]},
    ),
]

_NW_XFAIL = pytest.mark.xfail(
    strict=True,
    raises=TypeError,
    reason="Narwhals list namespace not supported on pandas; expression handling issues on polars",
)
_NW_BACKENDS = {"narwhals-polars", "narwhals-pandas"}


def _params():
    cases = []
    for op in OP_SPECS:
        for bk in ALL_BACKENDS:
            for it in INPUT_TYPES:
                mark = xfail_if_limited(bk, op.function_key, op.param_name, it)
                marks = [mark] if mark else []
                if bk in _NW_BACKENDS:
                    marks = [_NW_XFAIL]
                cases.append(
                    pytest.param(op, bk, it, marks=marks, id=f"{op.op_name}-{bk}-{it}")
                )
    return cases


if OP_SPECS:

    @pytest.mark.parametrize("op,backend,input_type", _params())
    def test_argument_channel(op: OpSpec, backend: str, input_type: str):
        run_argument_matrix(op, backend, input_type)
