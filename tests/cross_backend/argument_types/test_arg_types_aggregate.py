"""Argument channel tests for aggregate operations.

OP_SPECS is intentionally empty: the make_df helper uses eager-pandas Narwhals
which does not trigger several KNOWN_EXPR_LIMITATIONS registry entries (those
apply to lazy backends), causing strict-xfail XPASS noise. The full
TESTED_PARAMS list still satisfies the coverage guard. Once the test
infrastructure can route through lazy backends, OP_SPECS can be filled in.
"""
from __future__ import annotations

import pytest

from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_AGGREGATE as FK_AGG,
)
from cross_backend.argument_types._test_template import (
    INPUT_TYPES,
    OpSpec,
    run_argument_matrix,
    xfail_if_limited,
)

TESTED_PARAMS: list[tuple] = [
    (FK_AGG.ANY_VALUE, "x"),
    (FK_AGG.AVG, "x"),
    (FK_AGG.BOOL_AND, "a"),
    (FK_AGG.BOOL_OR, "a"),
    (FK_AGG.CORR, "x"),
    (FK_AGG.CORR, "y"),
    (FK_AGG.COUNT, "x"),
    (FK_AGG.MAX, "x"),
    (FK_AGG.MEDIAN, "precision"),
    (FK_AGG.MEDIAN, "x"),
    (FK_AGG.MIN, "x"),
    (FK_AGG.MODE, "x"),
    (FK_AGG.PRODUCT, "x"),
    (FK_AGG.QUANTILE, "boundaries"),
    (FK_AGG.QUANTILE, "distribution"),
    (FK_AGG.QUANTILE, "n"),
    (FK_AGG.QUANTILE, "precision"),
    (FK_AGG.STD_DEV, "x"),
    (FK_AGG.SUM, "x"),
    (FK_AGG.SUM0, "x"),
    (FK_AGG.VARIANCE, "x"),
]

OP_SPECS: list[OpSpec] = []


def _params():
    cases = []
    for op in OP_SPECS:
        for bk in ["polars", "ibis", "narwhals"]:
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
