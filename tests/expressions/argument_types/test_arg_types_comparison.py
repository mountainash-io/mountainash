"""Argument channel coverage for comparison operations.

The covered comparison forms require a relation-level fixture rather than this
eager scalar matrix.
"""
from __future__ import annotations

import pytest

from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_COMPARISON as FK_MA_CMP,
    FKEY_SUBSTRAIT_SCALAR_COMPARISON as FK_CMP,
)
from expressions.argument_types.conftest import ALL_BACKENDS
from expressions.argument_types._test_template import (INPUT_TYPES,
OpSpec,
run_argument_matrix, )

TESTED_PARAMS: list[tuple] = [
    (FK_CMP.BETWEEN, "high"),
    (FK_CMP.BETWEEN, "low"),
    (FK_CMP.BETWEEN, "x"),
    (FK_CMP.COALESCE, "args"),
    (FK_CMP.EQUAL, "x"),
    (FK_CMP.EQUAL, "y"),
    (FK_CMP.GREATEST, "args"),
    (FK_CMP.GREATEST_SKIP_NULL, "args"),
    (FK_CMP.GT, "x"),
    (FK_CMP.GT, "y"),
    (FK_CMP.GTE, "x"),
    (FK_CMP.GTE, "y"),
    (FK_MA_CMP.IS_DUPLICATED, "x"),
    ("is_distinct_from", "x"),
    ("is_distinct_from", "y"),
    (FK_CMP.IS_FALSE, "x"),
    (FK_CMP.IS_FINITE, "x"),
    (FK_CMP.IS_INFINITE, "x"),
    (FK_CMP.IS_NAN, "x"),
    ("is_not_distinct_from", "x"),
    ("is_not_distinct_from", "y"),
    (FK_CMP.IS_NOT_FALSE, "x"),
    (FK_CMP.IS_NOT_NULL, "x"),
    (FK_CMP.IS_NOT_TRUE, "x"),
    (FK_CMP.IS_NULL, "x"),
    (FK_CMP.IS_TRUE, "x"),
    (FK_CMP.LEAST, "args"),
    (FK_CMP.LEAST_SKIP_NULL, "args"),
    (FK_CMP.LT, "x"),
    (FK_CMP.LT, "y"),
    (FK_CMP.LTE, "x"),
    (FK_CMP.LTE, "y"),
    (FK_CMP.NOT_EQUAL, "x"),
    (FK_CMP.NOT_EQUAL, "y"),
    ("nullif", "x"),
    ("nullif", "y"),
]

OP_SPECS: list[OpSpec] = []


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
        run_argument_matrix(op, backend, input_type)
