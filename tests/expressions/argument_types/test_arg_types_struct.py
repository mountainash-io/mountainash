"""Argument channel tests for struct operations."""
from __future__ import annotations

import pytest
import mountainash as ma
from mountainash.core.dtypes import MountainashDtype as D
from mountainash.core.types import BackendCapabilityError
from mountainash.typespec.spec import FieldDefinition
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_STRUCT as FK_STRUCT
from mountainash.expressions import BaseExpressionAPI

from expressions.argument_types.conftest import ALL_BACKENDS
from expressions.argument_types._test_template import (INPUT_TYPES,
OpSpec,
run_argument_matrix, )

TESTED_PARAMS: list[tuple] = [
    ("struct_field", "x"),
    (FK_STRUCT.CAST, "converted_fields"),
]

OP_SPECS: list[OpSpec] = [
    OpSpec(
        function_key=FK_STRUCT.CAST,
        op_name="cast_struct_children",
        build=lambda col, arg: col.struct.cast(
            fields={"v": FieldDefinition(dtype=D.I16)}, field_name="a",
            converted_fields=(("v", arg if isinstance(arg, BaseExpressionAPI) else ma.lit(arg)),),
        ),
        raw_arg=7, arg_col_name="replacement", param_name="converted_fields",
        input_col="a",
        data={"a": [{"v": 1}, {"v": 2}, {"v": 3}, None], "replacement": [3, 5, 7, 9]},
        expected_by_input={
            "raw": [{"v": 7}] * 3 + [None], "lit": [{"v": 7}] * 3 + [None],
            "col": [{"v": 3}, {"v": 5}, {"v": 7}, None],
            "complex": [{"v": 3}, {"v": 5}, {"v": 7}, None],
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
        if backend == "narwhals-pandas":
            with pytest.raises(BackendCapabilityError) as error:
                run_argument_matrix(op, backend, input_type)
            assert error.value.function_key is FK_STRUCT.CAST
            return
        run_argument_matrix(op, backend, input_type)
