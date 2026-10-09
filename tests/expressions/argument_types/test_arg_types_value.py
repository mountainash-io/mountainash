"""Argument and option channel tests for value operations."""
from __future__ import annotations

import pytest

import mountainash as ma
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_VALUE as FK_VALUE,
)
from expressions.argument_types._option_helpers import OptionSpec
from expressions.argument_types._test_template import (INPUT_TYPES,
OpSpec,
run_argument_matrix, )
from expressions.argument_types.conftest import ALL_BACKENDS
from expressions.argument_types.option_disposition import (
    INVALID_OPTION_VALUE,
    OPTION_DISPOSITIONS,
    REGISTERED_INVALID_OPTION_REJECTIONS,
    REGISTERED_OPTION_PROBES,
    InvalidOptionRejection,
    OptionCell,
    OptionProbeRegistration,
)


TESTED_PARAMS: list[tuple] = [
    (FK_VALUE.VALUE_KIND, "x"),
    (FK_VALUE.BOOLEAN_VALUE, "x"),
    (FK_VALUE.TEXT_VALUE, "x"),
]

TESTED_OPTION_PARAMS = [
    (
        "MountainAshScalarValueExpressionSystemProtocol",
        "boolean_value",
        "source",
        "value-sensitive",
    ),
]

_VALUE_PROTOCOL = "MountainAshScalarValueExpressionSystemProtocol"
_VALUE_SOURCES = ("boolean", "binary_number", "finite_number")


def _source_probe(source: str) -> OptionSpec:
    return OptionSpec(
        FK_VALUE.BOOLEAN_VALUE,
        "source",
        source,
        "float64",
        lambda source=source: ma.col("value").boolean_value(source=source),
        lambda source=source: ma.col("value").boolean_value(
            source="binary_number" if source == "boolean" else "boolean"
        ),
        {"value": [0.0, 1.0, 2.0]},
        expected_discriminates=True,
    )


OPTION_DISPOSITIONS.extend(
    OptionCell(
        FK_VALUE.BOOLEAN_VALUE,
        _VALUE_PROTOCOL,
        "boolean_value",
        "source",
        backend,
        source,
        "float64",
        "honored",
        "selected source changes the nullable Boolean projection",
    )
    for backend in ALL_BACKENDS
    for source in _VALUE_SOURCES
)

_INVALID_VALUE_SOURCE_REJECTIONS = [
    InvalidOptionRejection(
        FK_VALUE.BOOLEAN_VALUE,
        _VALUE_PROTOCOL,
        "boolean_value",
        "source",
        INVALID_OPTION_VALUE,
        "float64",
        lambda: ma.col("value").boolean_value(source=INVALID_OPTION_VALUE),
    )
]

OPTION_DISPOSITIONS.extend(
    OptionCell(
        rejection.fkey,
        rejection.protocol,
        rejection.op,
        rejection.param,
        backend,
        rejection.value,
        rejection.dtype,
        "invalid",
        "canonical build-time rejection sentinel; invalid strings are unbounded",
    )
    for rejection in _INVALID_VALUE_SOURCE_REJECTIONS
    for backend in ALL_BACKENDS
)

OP_SPECS: list[OpSpec] = [
    OpSpec(
        function_key=FK_VALUE.VALUE_KIND,
        op_name="value_kind",
        build=lambda receiver, _arg: receiver.value_kind(),
        raw_arg="text",
        arg_col_name="kind_input",
        param_name="x",
        data={"kind_input": ["text", "other"]},
        complex_builder=lambda name: ma.col(name).text_value().str.strip_chars(" "),
        matrix_arg_is_input=True,
        expected_by_input={
            "raw": ["text"], "lit": ["text"],
            "col": ["text", "text"], "complex": ["text", "text"],
        },
    ),
    OpSpec(
        function_key=FK_VALUE.BOOLEAN_VALUE,
        op_name="boolean_value",
        build=lambda receiver, _arg: receiver.boolean_value(source="boolean"),
        raw_arg=True,
        arg_col_name="boolean_input",
        param_name="x",
        data={"boolean_input": [True, False]},
        complex_builder=lambda name: ma.col(name).boolean_value(),
        matrix_arg_is_input=True,
        expected_by_input={
            "raw": [True], "lit": [True],
            "col": [True, False], "complex": [True, False],
        },
    ),
    OpSpec(
        function_key=FK_VALUE.TEXT_VALUE,
        op_name="text_value",
        build=lambda receiver, _arg: receiver.text_value(),
        raw_arg="text",
        arg_col_name="text_input",
        param_name="x",
        data={"text_input": ["text", "other"]},
        complex_builder=lambda name: ma.col(name).text_value().str.strip_chars(" "),
        matrix_arg_is_input=True,
        expected_by_input={
            "raw": ["text"], "lit": ["text"],
            "col": ["text", "other"], "complex": ["text", "other"],
        },
    ),
]


def _params():
    cases = []
    for op in OP_SPECS:
        for backend in ALL_BACKENDS:
            for input_type in INPUT_TYPES:
                marks = []
                cases.append(
                    pytest.param(
                        op,
                        backend,
                        input_type,
                        marks=marks,
                        id=f"{op.op_name}-{backend}-{input_type}",
                    )
                )
    return cases


@pytest.mark.parametrize("op,backend,input_type", _params())
def test_argument_channel(op: OpSpec, backend: str, input_type: str):
    run_argument_matrix(op, backend, input_type)


@pytest.mark.parametrize("source", [INVALID_OPTION_VALUE, ma.col("source")])
def test_boolean_value_rejects_invalid_source_at_ast_build(source: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        ma.col("value").boolean_value(source=source)  # type: ignore[arg-type]
