"""Argument channel tests for window operations."""
from __future__ import annotations

import pytest

from mountainash.expressions.core.expression_system.function_keys.enums import (
    SUBSTRAIT_ARITHMETIC_WINDOW as FK_WIN,
)
from cross_backend.argument_types.conftest import ALL_BACKENDS
from cross_backend.argument_types._test_template import (
    INPUT_TYPES,
    OpSpec,
    run_argument_matrix,
    xfail_if_limited,
)

TESTED_PARAMS: list[tuple] = [
    (FK_WIN.FIRST_VALUE, "x"),
    (FK_WIN.LAG, "x"),
    (FK_WIN.LAST_VALUE, "x"),
    (FK_WIN.LEAD, "x"),
    (FK_WIN.NTH_VALUE, "window_offset"),
    (FK_WIN.NTH_VALUE, "x"),
    (FK_WIN.NTILE, "x"),
    # order_by_col is visitor-injected from WindowSpec, not user-facing
    (FK_WIN.RANK, "order_by_col"),
    (FK_WIN.DENSE_RANK, "order_by_col"),
    (FK_WIN.ROW_NUMBER, "order_by_col"),
    # Mountainash extension window operations
    ("backward_fill", "x"),
    ("cum_count", "x"),
    ("cum_max", "x"),
    ("cum_min", "x"),
    ("cum_prod", "x"),
    ("cum_sum", "x"),
    ("diff", "x"),
    ("forward_fill", "x"),
]

OP_SPECS: list[OpSpec] = []


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
