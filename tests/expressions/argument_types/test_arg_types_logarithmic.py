"""Argument channel coverage for logarithmic operations.

The covered logarithmic forms require a relation-level fixture rather than
this eager scalar matrix.
"""
from __future__ import annotations

import pytest

from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_LOGARITHMIC as FK_LOG,
)
from expressions.argument_types.conftest import ALL_BACKENDS
from expressions.argument_types._test_template import (INPUT_TYPES,
OpSpec,
run_argument_matrix, )

TESTED_PARAMS: list[tuple] = [
    ("ln", "x"),
    (FK_LOG.LOG10, "x"),
    ("log1p", "x"),
    (FK_LOG.LOG2, "x"),
    (FK_LOG.LOGB, "base"),
    (FK_LOG.LOGB, "x"),
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
