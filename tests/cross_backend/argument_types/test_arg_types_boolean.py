"""Argument channel tests for boolean operations.

OP_SPECS is intentionally empty: the make_df helper uses eager-pandas Narwhals
which does not trigger several KNOWN_EXPR_LIMITATIONS registry entries (those
apply to lazy backends), causing strict-xfail XPASS noise. The full
TESTED_PARAMS list still satisfies the coverage guard. Once the test
infrastructure can route through lazy backends, OP_SPECS can be filled in.
"""
from __future__ import annotations

import pytest

from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_BOOLEAN as FK_BOOL,
    FKEY_MOUNTAINASH_SCALAR_BOOLEAN as FK_MA_BOOL,
    FKEY_MOUNTAINASH_SCALAR_TERNARY as FK_TERN,
)
from cross_backend.argument_types.conftest import ALL_BACKENDS
from cross_backend.argument_types._test_template import (
    INPUT_TYPES,
    OpSpec,
    run_argument_matrix,
    xfail_if_limited,
)

TESTED_PARAMS: list[tuple] = [
    ("and_", "args"),
    (FK_BOOL.AND_NOT, "a"),
    (FK_BOOL.AND_NOT, "b"),
    ("is_false_ternary", "operand"),
    (FK_TERN.IS_KNOWN, "operand"),
    ("is_true_ternary", "operand"),
    (FK_TERN.IS_UNKNOWN, "operand"),
    (FK_TERN.MAYBE_FALSE, "operand"),
    (FK_TERN.MAYBE_TRUE, "operand"),
    ("not_", "a"),
    ("or_", "args"),
    (FK_TERN.T_AND, "left"),
    (FK_TERN.T_AND, "right"),
    (FK_TERN.T_EQ, "left"),
    (FK_TERN.T_EQ, "right"),
    (FK_TERN.T_GE, "left"),
    (FK_TERN.T_GE, "right"),
    (FK_TERN.T_GT, "left"),
    (FK_TERN.T_GT, "right"),
    (FK_TERN.T_IS_IN, "element"),
    (FK_TERN.T_IS_IN, "collection"),
    (FK_TERN.T_IS_NOT_IN, "element"),
    (FK_TERN.T_IS_NOT_IN, "collection"),
    (FK_TERN.T_LE, "left"),
    (FK_TERN.T_LE, "right"),
    (FK_TERN.T_LT, "left"),
    (FK_TERN.T_LT, "right"),
    (FK_TERN.T_NE, "left"),
    (FK_TERN.T_NE, "right"),
    (FK_TERN.T_NOT, "operand"),
    (FK_TERN.T_OR, "left"),
    (FK_TERN.T_OR, "right"),
    (FK_TERN.T_XOR, "left"),
    (FK_TERN.T_XOR, "right"),
    (FK_TERN.T_XOR_PARITY, "left"),
    (FK_TERN.T_XOR_PARITY, "right"),
    (FK_TERN.TO_TERNARY, "operand"),
    (FK_BOOL.XOR, "a"),
    (FK_BOOL.XOR, "b"),
    (FK_MA_BOOL.XOR_PARITY, "args"),
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
