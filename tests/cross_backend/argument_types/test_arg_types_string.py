"""Argument channel tests for string operations."""
from __future__ import annotations

import pytest

from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)
from cross_backend.argument_types.conftest import ALL_BACKENDS
from cross_backend.argument_types._test_template import (
    INPUT_TYPES,
    OpSpec,
    run_argument_matrix,
    xfail_if_limited,
)

# Full set of (function_key_or_op_name, param_name) pairs covered by this category.
# String fallbacks are used for ops that lack a matching FKEY enum member yet.
TESTED_PARAMS: list[tuple] = [
    # Substrait string ops — all have OP_SPECS in this file
    (FK_STR.CENTER, "character"),
    (FK_STR.CENTER, "length"),
    (FK_STR.CONCAT_WS, "separator"),
    (FK_STR.CONTAINS, "substring"),
    # Mountainash string extensions — 8 ops (json_decode has no OP_SPEC; others have one)
    ("strip_suffix", "x"),
    ("to_integer", "x"),
    ("to_time", "x"),
    ("encode", "x"),
    ("decode", "x"),
    ("json_decode", "x"),
    ("json_path_match", "x"),
    ("extract_groups", "x"),
    (FK_STR.COUNT_SUBSTRING, "substring"),
    (FK_STR.ENDS_WITH, "substring"),
    (FK_STR.LEFT, "count"),
    (FK_STR.LIKE, "match"),
    (FK_STR.LPAD, "characters"),
    (FK_STR.LPAD, "length"),
    (FK_STR.LTRIM, "characters"),
    (FK_STR.REGEXP_REPLACE, "occurrence"),
    (FK_STR.REGEXP_REPLACE, "pattern"),
    (FK_STR.REGEXP_REPLACE, "position"),
    (FK_STR.REGEXP_REPLACE, "replacement"),
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
    (FK_STR.STRPOS, "substring"),
    (FK_STR.SUBSTRING, "length"),
    (FK_STR.SUBSTRING, "start"),
    (FK_STR.TRIM, "characters"),
    # Not listed here (broken upstream APIs, tracked in _KNOWN_UNTESTED in coverage guard):
    #     concat_ws.string_arguments — backend only accepts 2 positional args
    #     string_split.separator — STRING_SPLIT enum key missing
    #     regexp_count_substring.pattern/.position — backends return None (NoneType.compile)
    #     regexp_match_substring.* — missing FKEY enum members
    #     regexp_match_substring_all.* — missing FKEY enum members
    #     regexp_strpos.* — backends return None
    #     regexp_string_split.pattern — missing FKEY enum member
]

OP_SPECS: list[OpSpec] = [
    OpSpec(
        function_key=FK_STR.CONTAINS,
        op_name="contains",
        build=lambda col, arg: col.str.contains(arg),
        raw_arg="world",
        arg_col_name="pattern",
        param_name="substring",
        data={
            "text": ["hello world", "foo bar", "world cup"],
            "pattern": ["world", "baz", "cup"],
        },
    ),
    OpSpec(
        function_key=FK_STR.STARTS_WITH,
        op_name="starts_with",
        build=lambda col, arg: col.str.starts_with(arg),
        raw_arg="hel",
        arg_col_name="pattern",
        param_name="substring",
        data={
            "text": ["hello", "foo", "help"],
            "pattern": ["hel", "baz", "hel"],
        },
    ),
    OpSpec(
        function_key=FK_STR.ENDS_WITH,
        op_name="ends_with",
        build=lambda col, arg: col.str.ends_with(arg),
        raw_arg="world",
        arg_col_name="pattern",
        param_name="substring",
        data={
            "text": ["hello world", "foo bar", "my world"],
            "pattern": ["world", "baz", "world"],
        },
    ),
    OpSpec(
        function_key=FK_STR.REPLACE,
        op_name="replace",
        build=lambda col, arg: col.str.replace(arg, "X"),
        raw_arg="o",
        arg_col_name="pattern",
        param_name="substring",
        data={
            "text": ["hello", "foo", "world"],
            "pattern": ["o", "o", "o"],
        },
    ),
    OpSpec(
        function_key=FK_STR.LPAD,
        op_name="lpad",
        build=lambda col, arg: col.str.lpad(arg, "*"),
        raw_arg=5,
        arg_col_name="length",
        param_name="length",
        data={
            "text": ["a", "bb", "ccc"],
            "length": [5, 5, 5],
        },
    ),
    OpSpec(
        function_key=FK_STR.RPAD,
        op_name="rpad",
        build=lambda col, arg: col.str.rpad(arg, "*"),
        raw_arg=5,
        arg_col_name="length",
        param_name="length",
        data={
            "text": ["a", "bb", "ccc"],
            "length": [5, 5, 5],
        },
    ),
    OpSpec(
        function_key=FK_STR.SUBSTRING,
        op_name="substring_start",
        build=lambda col, arg: col.str.substring(arg),
        raw_arg=1,
        arg_col_name="start",
        param_name="start",
        data={
            "text": ["hello", "world", "test"],
            "start": [1, 2, 0],
        },
    ),
    OpSpec(
        function_key=FK_STR.SUBSTRING,
        op_name="substring_length",
        build=lambda col, arg: col.str.substring(0, arg),
        raw_arg=3,
        arg_col_name="length",
        param_name="length",
        data={
            "text": ["hello", "world", "test"],
            "length": [3, 4, 2],
        },
    ),
    OpSpec(
        function_key=FK_STR.LEFT,
        op_name="left",
        build=lambda col, arg: col.str.left(arg),
        raw_arg=3,
        arg_col_name="count",
        param_name="count",
        data={
            "text": ["hello", "world", "test"],
            "count": [3, 2, 4],
        },
    ),
    OpSpec(
        function_key=FK_STR.RIGHT,
        op_name="right",
        build=lambda col, arg: col.str.right(arg),
        raw_arg=3,
        arg_col_name="count",
        param_name="count",
        data={
            "text": ["hello", "world", "test"],
            "count": [3, 2, 4],
        },
    ),
    OpSpec(
        function_key=FK_STR.TRIM,
        op_name="trim",
        build=lambda col, arg: col.str.trim(arg),
        raw_arg="x",
        arg_col_name="chars",
        param_name="characters",
        data={
            "text": ["xhellox", "xworldx", "xtestx"],
            "chars": ["x", "x", "x"],
        },
    ),
    OpSpec(
        function_key=FK_STR.LTRIM,
        op_name="ltrim",
        build=lambda col, arg: col.str.ltrim(arg),
        raw_arg="x",
        arg_col_name="chars",
        param_name="characters",
        data={
            "text": ["xhello", "xworld", "xtest"],
            "chars": ["x", "x", "x"],
        },
    ),
    OpSpec(
        function_key=FK_STR.RTRIM,
        op_name="rtrim",
        build=lambda col, arg: col.str.rtrim(arg),
        raw_arg="x",
        arg_col_name="chars",
        param_name="characters",
        data={
            "text": ["hellox", "worldx", "testx"],
            "chars": ["x", "x", "x"],
        },
    ),
    OpSpec(
        function_key=FK_STR.LIKE,
        op_name="like",
        build=lambda col, arg: col.str.like(arg),
        raw_arg="%ello%",
        arg_col_name="pattern",
        param_name="match",
        data={
            "text": ["hello", "world", "jello"],
            "pattern": ["%ello%", "%orl%", "%ell%"],
        },
    ),
    OpSpec(
        function_key=FK_STR.REPLACE,
        op_name="replace_replacement",
        build=lambda col, arg: col.str.replace("o", arg),
        raw_arg="X",
        arg_col_name="replacement",
        param_name="replacement",
        data={
            "text": ["hello", "foo", "world"],
            "replacement": ["X", "Y", "Z"],
        },
    ),
    OpSpec(
        function_key=FK_STR.REGEXP_REPLACE,
        op_name="regexp_replace_pattern",
        build=lambda col, arg: col.str.regexp_replace(arg, "X"),
        raw_arg="o+",
        arg_col_name="pattern",
        param_name="pattern",
        data={
            "text": ["hello", "foooo", "world"],
            "pattern": ["o+", "o+", "o+"],
        },
    ),
    OpSpec(
        function_key=FK_STR.REGEXP_REPLACE,
        op_name="regexp_replace_replacement",
        build=lambda col, arg: col.str.regexp_replace("o+", arg),
        raw_arg="X",
        arg_col_name="replacement",
        param_name="replacement",
        data={
            "text": ["hello", "foooo", "world"],
            "replacement": ["X", "Y", "Z"],
        },
    ),
    # -- secondary args added in Part 2 --
    OpSpec(
        function_key=FK_STR.COUNT_SUBSTRING,
        op_name="count_substring",
        build=lambda col, arg: col.str.count_substring(arg),
        raw_arg="o",
        arg_col_name="pattern",
        param_name="substring",
        data={
            "text": ["hello world", "foo bar", "boo"],
            "pattern": ["o", "o", "o"],
        },
    ),
    OpSpec(
        function_key=FK_STR.STRPOS,
        op_name="strpos",
        build=lambda col, arg: col.str.strpos(arg),
        raw_arg="lo",
        arg_col_name="pattern",
        param_name="substring",
        data={
            "text": ["hello", "world", "helo"],
            "pattern": ["lo", "lo", "lo"],
        },
    ),
    OpSpec(
        function_key=FK_STR.REPEAT,
        op_name="repeat",
        build=lambda col, arg: col.str.repeat(arg),
        raw_arg=3,
        arg_col_name="count_col",
        param_name="count",
        data={
            "text": ["a", "b", "c"],
            "count_col": [3, 3, 3],
        },
    ),
    OpSpec(
        function_key=FK_STR.CENTER,
        op_name="center_length",
        build=lambda col, arg: col.str.center(arg, "*"),
        raw_arg=10,
        arg_col_name="length",
        param_name="length",
        data={
            "text": ["a", "bb", "ccc"],
            "length": [10, 10, 10],
        },
    ),
    OpSpec(
        function_key=FK_STR.CENTER,
        op_name="center_character",
        build=lambda col, arg: col.str.center(10, arg),
        raw_arg="*",
        arg_col_name="fill",
        param_name="character",
        data={
            "text": ["a", "bb", "ccc"],
            "fill": ["*", "*", "*"],
        },
    ),
    OpSpec(
        function_key=FK_STR.LPAD,
        op_name="lpad_characters",
        build=lambda col, arg: col.str.lpad(10, arg),
        raw_arg="*",
        arg_col_name="fill",
        param_name="characters",
        data={
            "text": ["a", "bb", "ccc"],
            "fill": ["*", "*", "*"],
        },
    ),
    OpSpec(
        function_key=FK_STR.RPAD,
        op_name="rpad_characters",
        build=lambda col, arg: col.str.rpad(10, arg),
        raw_arg="*",
        arg_col_name="fill",
        param_name="characters",
        data={
            "text": ["a", "bb", "ccc"],
            "fill": ["*", "*", "*"],
        },
    ),
    OpSpec(
        function_key=FK_STR.REPLACE_SLICE,
        op_name="replace_slice_start",
        build=lambda col, arg: col.str.replace_slice(arg, 2, "XX"),
        raw_arg=0,
        arg_col_name="start_col",
        param_name="start",
        data={
            "text": ["hello", "world", "test"],
            "start_col": [0, 0, 0],
        },
    ),
    OpSpec(
        function_key=FK_STR.REPLACE_SLICE,
        op_name="replace_slice_length",
        build=lambda col, arg: col.str.replace_slice(0, arg, "XX"),
        raw_arg=2,
        arg_col_name="length_col",
        param_name="length",
        data={
            "text": ["hello", "world", "test"],
            "length_col": [2, 2, 2],
        },
    ),
    OpSpec(
        function_key=FK_STR.REPLACE_SLICE,
        op_name="replace_slice_replacement",
        build=lambda col, arg: col.str.replace_slice(0, 2, arg),
        raw_arg="XX",
        arg_col_name="repl",
        param_name="replacement",
        data={
            "text": ["hello", "world", "test"],
            "repl": ["XX", "YY", "ZZ"],
        },
    ),
    # -- Mountainash string extensions --
    OpSpec(
        function_key="strip_suffix",
        op_name="strip_suffix",
        build=lambda col, _arg: col.str.strip_suffix("_old"),
        raw_arg=0,
        arg_col_name="a",
        param_name="x",
        input_col="a",
        data={"a": ["hello_old", "world_old", "test"]},
    ),
    OpSpec(
        function_key="to_integer",
        op_name="to_integer",
        build=lambda col, _arg: col.str.to_integer(),
        raw_arg=0,
        arg_col_name="a",
        param_name="x",
        input_col="a",
        data={"a": ["123", "456", "789"]},
    ),
    OpSpec(
        function_key="to_time",
        op_name="to_time",
        build=lambda col, _arg: col.str.to_time("%H:%M"),
        raw_arg=0,
        arg_col_name="a",
        param_name="x",
        input_col="a",
        data={"a": ["12:30", "08:00", "23:59"]},
    ),
    OpSpec(
        function_key="encode",
        op_name="encode",
        build=lambda col, _arg: col.str.encode("hex"),
        raw_arg=0,
        arg_col_name="a",
        param_name="x",
        input_col="a",
        data={"a": ["hello", "world", "test"]},
    ),
    OpSpec(
        function_key="decode",
        op_name="decode",
        build=lambda col, _arg: col.str.decode("hex"),
        raw_arg=0,
        arg_col_name="a",
        param_name="x",
        input_col="a",
        data={"a": ["68656c6c6f", "776f726c64", "74657374"]},
    ),
    OpSpec(
        function_key="json_path_match",
        op_name="json_path_match",
        build=lambda col, _arg: col.str.json_path_match("$.x"),
        raw_arg=0,
        arg_col_name="a",
        param_name="x",
        input_col="a",
        data={"a": ['{"x":1}', '{"x":2}', '{"x":3}']},
    ),
    OpSpec(
        function_key="extract_groups",
        op_name="extract_groups",
        build=lambda col, _arg: col.str.extract_groups(r"(\w+)@(\w+)"),
        raw_arg=0,
        arg_col_name="a",
        param_name="x",
        input_col="a",
        data={"a": ["user@host", "foo@bar", "a@b"]},
    ),
    OpSpec(
        function_key=FK_STR.CONCAT_WS,
        op_name="concat_ws_separator",
        build=lambda col, arg: col.str.concat_ws(arg),
        raw_arg=",",
        arg_col_name="sep",
        param_name="separator",
        data={
            "text": ["hello", "world", "test"],
            "sep": [",", ",", ","],
        },
    ),
    OpSpec(
        function_key=FK_STR.REGEXP_REPLACE,
        op_name="regexp_replace_position",
        build=lambda col, arg: col.str.regexp_replace("o+", "X", position=arg),
        raw_arg=0,
        arg_col_name="pos",
        param_name="position",
        data={
            "text": ["hello", "foooo", "world"],
            "pos": [0, 0, 0],
        },
    ),
    OpSpec(
        function_key=FK_STR.REGEXP_REPLACE,
        op_name="regexp_replace_occurrence",
        build=lambda col, arg: col.str.regexp_replace("o+", "X", occurrence=arg),
        raw_arg=1,
        arg_col_name="occ",
        param_name="occurrence",
        data={
            "text": ["hello", "foooo", "world"],
            "occ": [1, 1, 1],
        },
    ),
]


# Ops fully unsupported on narwhals (raise BackendCapabilityError for all input types,
# not just col/complex). xfail_if_limited only marks col/complex, so we handle these
# manually to avoid unexplained failures on raw/lit inputs.
_NARWHALS_FULLY_UNSUPPORTED: set[tuple] = {
    # repeat: narwhals has no str.repeat(); raises BackendCapabilityError unconditionally
    (FK_STR.REPEAT, "count"),
    # string extension ops with no narwhals support
    ("to_time", "x"),
    ("encode", "x"),
    ("decode", "x"),
    ("json_path_match", "x"),
    ("extract_groups", "x"),
}

# Ops fully unsupported on ibis (raise BackendCapabilityError for all input types).
_IBIS_FULLY_UNSUPPORTED: set[tuple] = {
    ("to_time", "x"),
    ("encode", "x"),
    ("decode", "x"),
    ("json_path_match", "x"),
    ("extract_groups", "x"),
}


def _params():
    cases = []
    for op in OP_SPECS:
        for bk in ALL_BACKENDS:
            for it in INPUT_TYPES:
                mark = xfail_if_limited(bk, op.function_key, op.param_name, it)
                if mark is None and bk in ("narwhals-polars", "narwhals-pandas"):
                    if (op.function_key, op.param_name) in _NARWHALS_FULLY_UNSUPPORTED:
                        mark = pytest.mark.xfail(
                            strict=True,
                            raises=Exception,
                            reason="Narwhals backend does not support this operation at all",
                        )
                if mark is None and bk == "ibis":
                    if (op.function_key, op.param_name) in _IBIS_FULLY_UNSUPPORTED:
                        mark = pytest.mark.xfail(
                            strict=True,
                            raises=Exception,
                            reason="Ibis backend does not support this operation at all",
                        )
                marks = [mark] if mark else []
                cases.append(
                    pytest.param(op, bk, it, marks=marks, id=f"{op.op_name}-{bk}-{it}")
                )
    return cases


if OP_SPECS:

    @pytest.mark.parametrize("op,backend,input_type", _params())
    def test_argument_channel(op: OpSpec, backend: str, input_type: str):
        run_argument_matrix(op, backend, input_type)
