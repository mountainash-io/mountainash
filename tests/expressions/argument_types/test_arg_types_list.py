"""Argument channel tests for list operations."""
from __future__ import annotations

import pytest
import mountainash as ma
from mountainash.core.dtypes import MountainashDtype as D
from mountainash.typespec import FieldSpec
from mountainash.expressions import BaseExpressionAPI

from mountainash.core.types import BackendCapabilityError
from tests.fixtures.call_expectations import expect_call_failure
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_LIST as FK_LIST,
)
from expressions.argument_types.conftest import ALL_BACKENDS
from expressions.argument_types._test_template import (INPUT_TYPES,
OpSpec,
run_argument_matrix, )

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
    (FK_LIST.T_CONTAINS, "item"),
    (FK_LIST.CAST_ITEMS, "converted_fields"),
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
        expected_by_input={
            "raw": [True, False, False], "lit": [True, False, False],
            "col": [True, True, False], "complex": [True, True, False],
        },
    ),
    OpSpec(
        function_key=FK_LIST.T_CONTAINS,
        op_name="list_t_contains_item",
        build=lambda col, arg: col.list.t_contains(arg),
        raw_arg=2,
        arg_col_name="item",
        param_name="item",
        input_col="a",
        data={"a": [[1, 2, 3], [4, 5, 6], [7, 8, 9]], "item": [2, 5, 1]},
    ),
    OpSpec(
        function_key=FK_LIST.CAST_ITEMS,
        op_name="cast_list_item_children",
        build=lambda col, arg: col.list.cast_items(
            element=FieldSpec(fields={"v": FieldSpec(dtype=D.I16)}), field_name="a",
            converted_fields=(("v", arg if isinstance(arg, BaseExpressionAPI) else ma.lit(arg)),),
        ),
        raw_arg=7, arg_col_name="replacement", param_name="converted_fields",
        input_col="a",
        data={"a": [[{"v": 1}, None], [{"v": 2}], []], "replacement": [3, 5, 7]},
        expected_by_input={
            "raw": [[{"v": 7}, None], [{"v": 7}], []],
            "lit": [[{"v": 7}, None], [{"v": 7}], []],
            "col": [[{"v": 3}, None], [{"v": 5}], []],
            "complex": [[{"v": 3}, None], [{"v": 5}], []],
        },
    ),
]

def _params():
    cases = []
    for op in OP_SPECS:
        for bk in ALL_BACKENDS:
            for it in INPUT_TYPES:
                
                marks = []
                cases.append(
                    pytest.param(op, bk, it, marks=marks, id=f"{op.op_name}-{bk}-{it}")
                )
    return cases


if OP_SPECS:

    @pytest.mark.parametrize("op,backend,input_type", _params())
    def test_argument_channel(op: OpSpec, backend: str, input_type: str):
        if op.function_key is FK_LIST.CAST_ITEMS:
            if backend.startswith("narwhals") or (
                backend == "ibis" and input_type in {"col", "complex"}
            ):
                with pytest.raises(BackendCapabilityError) as error:
                    run_argument_matrix(op, backend, input_type)
                assert error.value.function_key is FK_LIST.CAST_ITEMS
                return
            import polars as pl
            with expect_call_failure(
                when=backend in {"polars", "ibis-polars"} and input_type in {"col", "complex"},
                reason="312: native Polars list evaluation cannot capture a named outer column",
                errors=(pl.exceptions.ComputeError,),
            ):
                run_argument_matrix(op, backend, input_type)
            return
        if backend.startswith("narwhals") and input_type in ("col", "complex"):
            with pytest.raises(BackendCapabilityError) as error:
                run_argument_matrix(op, backend, input_type)
            assert error.value.function_key is op.function_key
            return
        with expect_call_failure(
            when=backend == "narwhals-pandas",
            reason="NW-LIST-01: pandas object-list storage has no Arrow list namespace",
            errors=(TypeError,),
        ):
            run_argument_matrix(op, backend, input_type)
