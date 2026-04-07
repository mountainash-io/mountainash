"""Argument channel tests for string operations."""
from __future__ import annotations

import pytest

from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)
from cross_backend.argument_types._test_template import (
    INPUT_TYPES,
    OpSpec,
    run_argument_matrix,
    xfail_if_limited,
)

# Full set of (function_key_or_op_name, param_name) pairs covered by this category.
# String fallbacks are used for ops that lack a matching FKEY enum member yet.
TESTED_PARAMS: list[tuple] = [
    (FK_STR.CENTER, "character"),
    (FK_STR.CENTER, "length"),
    (FK_STR.CONCAT_WS, "separator"),
    (FK_STR.CONCAT_WS, "string_arguments"),
    (FK_STR.CONTAINS, "substring"),
    (FK_STR.COUNT_SUBSTRING, "substring"),
    (FK_STR.ENDS_WITH, "substring"),
    (FK_STR.LEFT, "count"),
    (FK_STR.LIKE, "match"),
    (FK_STR.LPAD, "characters"),
    (FK_STR.LPAD, "length"),
    (FK_STR.LTRIM, "characters"),
    ("regexp_count_substring", "pattern"),
    ("regexp_count_substring", "position"),
    ("regexp_match_substring", "group"),
    ("regexp_match_substring", "occurrence"),
    ("regexp_match_substring", "pattern"),
    ("regexp_match_substring", "position"),
    ("regexp_match_substring_all", "group"),
    ("regexp_match_substring_all", "pattern"),
    ("regexp_match_substring_all", "position"),
    (FK_STR.REGEXP_REPLACE, "occurrence"),
    (FK_STR.REGEXP_REPLACE, "pattern"),
    (FK_STR.REGEXP_REPLACE, "position"),
    (FK_STR.REGEXP_REPLACE, "replacement"),
    ("regexp_string_split", "pattern"),
    ("regexp_strpos", "occurrence"),
    ("regexp_strpos", "pattern"),
    ("regexp_strpos", "position"),
    (FK_STR.REPEAT, "count"),
    (FK_STR.REPLACE, "replacement"),
    (FK_STR.REPLACE, "substring"),
    (FK_STR.REPLACE_SLICE, "length"),
    (FK_STR.REPLACE_SLICE, "replacement"),
    (FK_STR.REPLACE_SLICE, "start"),
    (FK_STR.RIGHT, "count"),
    (FK_STR.RPAD, "characters"),
    (FK_STR.RPAD, "length"),
    (FK_STR.RTRIM, "characters"),
    (FK_STR.STARTS_WITH, "substring"),
    ("string_split", "separator"),
    (FK_STR.STRPOS, "substring"),
    (FK_STR.SUBSTRING, "length"),
    (FK_STR.SUBSTRING, "start"),
    (FK_STR.TRIM, "characters"),
]

# OP_SPECS exercise the (op × backend × input_type) matrix for representative
# operations. The make_df helper uses eager-pandas Narwhals which does not
# trigger several KNOWN_EXPR_LIMITATIONS registry entries (those apply to lazy
# Narwhals backends), so OP_SPECS is intentionally empty until the
# infrastructure can route through lazy backends. The full TESTED_PARAMS list
# above still satisfies the coverage guard.
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
