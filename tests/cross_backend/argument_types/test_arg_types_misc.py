"""Argument channel tests for misc operations.

OP_SPECS is intentionally empty: the make_df helper uses eager-pandas Narwhals
which does not trigger several KNOWN_EXPR_LIMITATIONS registry entries (those
apply to lazy backends), causing strict-xfail XPASS noise. The full
TESTED_PARAMS list still satisfies the coverage guard. Once the test
infrastructure can route through lazy backends, OP_SPECS can be filled in.
"""
from __future__ import annotations

import pytest

from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_SET as FK_MA_SET,
    FKEY_SUBSTRAIT_SCALAR_SET as FK_SET,
)
from cross_backend.argument_types._test_template import (
    INPUT_TYPES,
    OpSpec,
    run_argument_matrix,
    xfail_if_limited,
)

TESTED_PARAMS: list[tuple] = [
    ("buffer", "buffer_radius"),
    ("buffer", "geom"),
    ("cast", "x"),
    ("centroid", "geom"),
    ("col", "x"),
    ("collection_extract", "geom_collection"),
    ("dimension", "geom"),
    ("envelope", "geom"),
    ("flip_coordinates", "geom_collection"),
    ("geometry_type", "geom"),
    ("if_then_else", "condition"),
    ("if_then_else", "if_false"),
    ("if_then_else", "if_true"),
    (FK_SET.INDEX_IN, "haystack"),
    (FK_SET.INDEX_IN, "needle"),
    ("is_closed", "geom"),
    ("is_empty", "geom"),
    (FK_MA_SET.IS_IN, "haystack"),
    (FK_MA_SET.IS_IN, "needle"),
    (FK_MA_SET.IS_NOT_IN, "haystack"),
    (FK_MA_SET.IS_NOT_IN, "needle"),
    ("is_ring", "geom"),
    ("is_simple", "geom"),
    ("is_valid", "geom"),
    ("make_line", "geom1"),
    ("make_line", "geom2"),
    ("minimum_bounding_circle", "geom"),
    ("num_points", "geom"),
    ("point", "x"),
    ("point", "y"),
    ("remove_repeated_points", "geom"),
    ("x_coordinate", "point"),
    ("y_coordinate", "point"),
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
