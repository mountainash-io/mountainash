"""Argument channel tests for arithmetic operations."""
from __future__ import annotations

import math

import pytest
import polars as pl
import _duckdb

import mountainash as ma
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.errors import InvalidOptionValueError

from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_ARITHMETIC as FK_ARITH,
    FKEY_MOUNTAINASH_SCALAR_ARITHMETIC as FK_MA_ARITH,
)
from expressions.argument_types.conftest import ALL_BACKENDS, make_df
from expressions.argument_types._option_helpers import (
    OptionProbeDidNotDiscriminateError,
    OptionSpec,
    option_result,
    xfail_option_unsupported,
)
from expressions.argument_types.option_disposition import (
    INVALID_OPTION_VALUE,
    OPTION_DISPOSITIONS,
    OPTION_FAMILY_DEFAULT_FACT_KEYS,
    REGISTERED_INVALID_OPTION_REJECTIONS,
    REGISTERED_OPTION_PROBES,
    InvalidOptionRejection,
    OptionCell,
    OptionProbeRegistration,
    param_taxonomy,
)
from expressions.argument_types._test_template import (
    INPUT_TYPES,
    OpSpec,
    run_argument_matrix,
    xfail_if_limited,
)

TESTED_PARAMS: list[tuple] = [
    (FK_ARITH.ABS, "x"),
    (FK_ARITH.ACOS, "x"),
    (FK_ARITH.ACOSH, "x"),
    (FK_ARITH.ADD, "x"),
    (FK_ARITH.ADD, "y"),
    (FK_ARITH.ASIN, "x"),
    (FK_ARITH.ASINH, "x"),
    (FK_ARITH.ATAN, "x"),
    (FK_ARITH.ATAN2, "x"),
    (FK_ARITH.ATAN2, "y"),
    (FK_ARITH.ATANH, "x"),
    (FK_ARITH.BITWISE_AND, "x"),
    (FK_ARITH.BITWISE_AND, "y"),
    (FK_ARITH.BITWISE_NOT, "x"),
    (FK_ARITH.BITWISE_OR, "x"),
    (FK_ARITH.BITWISE_OR, "y"),
    (FK_ARITH.BITWISE_XOR, "x"),
    (FK_ARITH.BITWISE_XOR, "y"),
    (FK_ARITH.COS, "x"),
    (FK_ARITH.COSH, "x"),
    (FK_ARITH.DEGREES, "x"),
    (FK_ARITH.DIVIDE, "x"),
    (FK_ARITH.DIVIDE, "y"),
    (FK_ARITH.EXP, "x"),
    ("factorial", "n"),
    (FK_MA_ARITH.FLOOR_DIVIDE, "x"),
    (FK_MA_ARITH.FLOOR_DIVIDE, "y"),
    (FK_ARITH.MODULO, "x"),
    (FK_ARITH.MODULO, "y"),
    (FK_ARITH.MULTIPLY, "x"),
    (FK_ARITH.MULTIPLY, "y"),
    (FK_ARITH.NEGATE, "x"),
    (FK_ARITH.POWER, "x"),
    (FK_ARITH.POWER, "y"),
    (FK_ARITH.RADIANS, "x"),
    (FK_ARITH.SHIFT_LEFT, "base"),
    (FK_ARITH.SHIFT_LEFT, "shift"),
    (FK_ARITH.SHIFT_RIGHT, "base"),
    (FK_ARITH.SHIFT_RIGHT, "shift"),
    (FK_ARITH.SHIFT_RIGHT_UNSIGNED, "base"),
    (FK_ARITH.SHIFT_RIGHT_UNSIGNED, "shift"),
    (FK_ARITH.SIGN, "x"),
    (FK_ARITH.SIN, "x"),
    (FK_ARITH.SINH, "x"),
    (FK_ARITH.SQRT, "x"),
    (FK_ARITH.SUBTRACT, "x"),
    (FK_ARITH.SUBTRACT, "y"),
    (FK_ARITH.TAN, "x"),
    (FK_ARITH.TANH, "x"),
]


@pytest.mark.parametrize(
    ("build", "fkey"),
    [
        pytest.param(
            lambda: ma.col("v").add(ma.col("w"), rounding="CEILING"),
            FK_ARITH.ADD,
            id="add",
        ),
        pytest.param(
            lambda: ma.col("v").subtract(ma.col("w"), rounding="CEILING"),
            FK_ARITH.SUBTRACT,
            id="subtract",
        ),
        pytest.param(
            lambda: ma.col("v").multiply(ma.col("w"), rounding="CEILING"),
            FK_ARITH.MULTIPLY,
            id="multiply",
        ),
        pytest.param(
            lambda: ma.col("v").divide(ma.col("w"), rounding="CEILING"),
            FK_ARITH.DIVIDE,
            id="divide",
        ),
        pytest.param(
            lambda: ma.col("v").sin(rounding="CEILING"),
            FK_ARITH.SIN,
            id="sin",
        ),
    ],
)
def test_arithmetic_rounding_option_is_emitted(build, fkey):
    node = build()._node

    assert node.function_key is fkey
    assert node.options == {"rounding": "CEILING"}


_ARITH_PROTOCOL = "SubstraitScalarArithmeticExpressionSystemProtocol"
_ABS_VALUES = ("ERROR", "SATURATE", "SILENT")
_ABS_PROBE_EXEMPT = {
    (backend, "SILENT")
    for backend in ("polars", "narwhals-polars", "narwhals-pandas")
}
_ABS_PROBE_EXEMPT.add(("ibis", "ERROR"))
_ABS_DECLARED = {
    (backend, value)
    for backend in ALL_BACKENDS
    for value in _ABS_VALUES
    if (backend, value) not in _ABS_PROBE_EXEMPT
}


OPTION_DISPOSITIONS.extend(
    OptionCell(
        FK_ARITH.ABS,
        _ARITH_PROTOCOL,
        "abs",
        "overflow",
        backend,
        value,
        "int8",
        "probe_exempt" if (backend, value) in _ABS_PROBE_EXEMPT else "declared_unsupported",
        (
            "intended-error-path"
            if backend == "ibis" and value == "ERROR"
            else "explicit SILENT selects the native wrapping behavior and is "
            "indistinguishable from omission"
            if (backend, value) in _ABS_PROBE_EXEMPT
            else "native behavior does not implement the requested overflow mode"
        ),
    )
    for backend in ALL_BACKENDS
    for value in _ABS_VALUES
)


def _abs_probe(value: str) -> OptionSpec:
    return OptionSpec(
        FK_ARITH.ABS,
        "overflow",
        value,
        "int8",
        lambda value=value: ma.col("v").abs(overflow=value),
        lambda: ma.col("v").abs(),
        {"v": [-128]},
        schema={"v": pl.Int8},
    )


REGISTERED_OPTION_PROBES.extend(
    OptionProbeRegistration(
        _abs_probe(value),
        backend,
        "declared_unsupported",
        (
            _duckdb.OutOfRangeException
            if backend == "ibis"
            else OptionProbeDidNotDiscriminateError
        ),
    )
    for backend, value in sorted(_ABS_DECLARED)
)
REGISTERED_OPTION_PROBES.extend(
    OptionProbeRegistration(
        _abs_probe(value)._replace(
            expected_discriminates=False,
            expected_native_exception=(
                _duckdb.OutOfRangeException
                if backend == "ibis" and value == "ERROR"
                else None
            ),
        ),
        backend,
        "probe_exempt",
    )
    for backend, value in sorted(_ABS_PROBE_EXEMPT)
)


_SEMANTIC_VALUES = {
    ("acos", "on_domain_error"): ("NAN", "ERROR"),
    ("acosh", "on_domain_error"): ("NAN", "ERROR"),
    ("asin", "on_domain_error"): ("NAN", "ERROR"),
    ("atan2", "on_domain_error"): ("NAN", "ERROR"),
    ("atanh", "on_domain_error"): ("NAN", "ERROR"),
    ("sqrt", "on_domain_error"): ("NAN", "ERROR"),
    ("divide", "on_domain_error"): ("NAN", "NULL", "ERROR"),
    ("divide", "on_division_by_zero"): ("IEEE", "LIMIT", "NULL", "ERROR"),
    ("modulus", "division_type"): ("TRUNCATE", "FLOOR"),
    ("modulus", "on_domain_error"): ("NULL", "ERROR"),
}
_SEMANTIC_FKEYS = {
    "acos": FK_ARITH.ACOS,
    "acosh": FK_ARITH.ACOSH,
    "asin": FK_ARITH.ASIN,
    "atan2": FK_ARITH.ATAN2,
    "atanh": FK_ARITH.ATANH,
    "sqrt": FK_ARITH.SQRT,
    "divide": FK_ARITH.DIVIDE,
    "modulus": FK_ARITH.MODULO,
}
_SEMANTIC_INPUTS = {
    ("acos", "on_domain_error"): ({"v": [2.0]}, {"v": pl.Float64}),
    ("acosh", "on_domain_error"): ({"v": [0.0]}, {"v": pl.Float64}),
    ("asin", "on_domain_error"): ({"v": [2.0]}, {"v": pl.Float64}),
    ("atan2", "on_domain_error"): (
        {"v": [math.nan], "w": [1.0]},
        {"v": pl.Float64, "w": pl.Float64},
    ),
    ("atanh", "on_domain_error"): ({"v": [2.0]}, {"v": pl.Float64}),
    ("sqrt", "on_domain_error"): ({"v": [-1.0]}, {"v": pl.Float64}),
    ("divide", "on_domain_error"): (
        {"v": [math.nan], "w": [1.0]},
        {"v": pl.Float64, "w": pl.Float64},
    ),
    ("divide", "on_division_by_zero"): (
        {"v": [0.0], "w": [0.0]},
        {"v": pl.Float64, "w": pl.Float64},
    ),
    ("modulus", "division_type"): (
        {"v": [-5], "w": [3]},
        {"v": pl.Int64, "w": pl.Int64},
    ),
    ("modulus", "on_domain_error"): (
        {"v": [5], "w": [0]},
        {"v": pl.Int64, "w": pl.Int64},
    ),
}
_SEMANTIC_EXEMPT = {
    ("acos", "on_domain_error", "polars", "NAN"),
    ("acosh", "on_domain_error", "polars", "NAN"),
    ("asin", "on_domain_error", "polars", "NAN"),
    ("atan2", "on_domain_error", "polars", "NAN"),
    ("atanh", "on_domain_error", "polars", "NAN"),
    ("sqrt", "on_domain_error", "polars", "NAN"),
    ("sqrt", "on_domain_error", "narwhals-polars", "NAN"),
    ("divide", "on_domain_error", "polars", "NAN"),
    ("divide", "on_domain_error", "narwhals-polars", "NAN"),
    ("divide", "on_domain_error", "narwhals-pandas", "NULL"),
    ("divide", "on_division_by_zero", "polars", "IEEE"),
    ("divide", "on_division_by_zero", "narwhals-polars", "IEEE"),
    ("divide", "on_division_by_zero", "narwhals-pandas", "NULL"),
    ("modulus", "division_type", "polars", "FLOOR"),
    ("modulus", "division_type", "narwhals-polars", "FLOOR"),
    ("modulus", "division_type", "narwhals-pandas", "FLOOR"),
    ("modulus", "on_domain_error", "polars", "NULL"),
    ("modulus", "on_domain_error", "narwhals-polars", "NULL"),
    ("modulus", "on_domain_error", "narwhals-pandas", "NULL"),
    ("acos", "on_domain_error", "ibis", "ERROR"),
    ("asin", "on_domain_error", "ibis", "ERROR"),
    ("sqrt", "on_domain_error", "ibis", "ERROR"),
}
_SEMANTIC_INTENDED_ERROR = {
    ("acos", "on_domain_error", "ibis", "ERROR"): _duckdb.InvalidInputException,
    ("asin", "on_domain_error", "ibis", "ERROR"): _duckdb.InvalidInputException,
    ("sqrt", "on_domain_error", "ibis", "ERROR"): _duckdb.OutOfRangeException,
}
_SEMANTIC_DECLARED = {
    (op, param, backend, value)
    for (op, param), values in _SEMANTIC_VALUES.items()
    for backend in ALL_BACKENDS
    for value in values
    if (op, param, backend, value) not in _SEMANTIC_EXEMPT
}


def _semantic_expr(op: str, param: str, value: str | None = None):
    kwargs = {} if value is None else {param: value}
    method = getattr(ma.col("v"), op)
    if op in {"atan2", "divide", "modulus"}:
        return method(ma.col("w"), **kwargs)
    return method(**kwargs)


def _semantic_probe(op: str, param: str, value: str) -> OptionSpec:
    data, schema = _SEMANTIC_INPUTS[(op, param)]
    return OptionSpec(
        _SEMANTIC_FKEYS[op],
        param,
        value,
        "int64" if op == "modulus" else "float64",
        lambda: _semantic_expr(op, param, value),
        lambda: _semantic_expr(op, param),
        data,
        schema,
    )


def _semantic_native_failure(
    op: str, param: str, backend: str, value: str
) -> type[BaseException]:
    if backend.startswith("narwhals") and op in {
        "acos",
        "acosh",
        "asin",
        "atan2",
        "atanh",
    }:
        return NotImplementedError
    if backend == "ibis":
        if op in {"acos", "asin"}:
            return _duckdb.InvalidInputException
        if op in {"acosh", "atanh"}:
            return NotImplementedError
        if op == "sqrt":
            return _duckdb.OutOfRangeException
    return OptionProbeDidNotDiscriminateError


OPTION_DISPOSITIONS.extend(
    OptionCell(
        _SEMANTIC_FKEYS[op],
        _ARITH_PROTOCOL,
        op,
        param,
        backend,
        value,
        "int64" if op == "modulus" else "float64",
        (
            "probe_exempt"
            if (op, param, backend, value) in _SEMANTIC_EXEMPT
            else "declared_unsupported"
        ),
        (
            "intended-error-path"
            if (op, param, backend, value) in _SEMANTIC_INTENDED_ERROR
            else "native omission already has the requested semantics and is "
            "indistinguishable from the explicit option"
            if (op, param, backend, value) in _SEMANTIC_EXEMPT
            else "native behavior does not implement the requested option semantics"
        ),
    )
    for (op, param), values in _SEMANTIC_VALUES.items()
    for backend in ALL_BACKENDS
    for value in values
)

REGISTERED_OPTION_PROBES.extend(
    OptionProbeRegistration(
        _semantic_probe(op, param, value),
        backend,
        "declared_unsupported",
        _semantic_native_failure(op, param, backend, value),
    )
    for op, param, backend, value in sorted(_SEMANTIC_DECLARED)
)
REGISTERED_OPTION_PROBES.extend(
    OptionProbeRegistration(
        _semantic_probe(op, param, value)._replace(
            expected_discriminates=False,
            expected_native_exception=_SEMANTIC_INTENDED_ERROR.get(
                (op, param, backend, value)
            ),
        ),
        backend,
        "probe_exempt",
    )
    for op, param, backend, value in sorted(_SEMANTIC_EXEMPT)
)


_OVERFLOW_SPECS = {
    "add": OptionSpec(
        FK_ARITH.ADD,
        "overflow",
        "",
        "int8",
        lambda: ma.col("v").add(ma.col("w"), overflow=""),
        lambda: ma.col("v").add(ma.col("w")),
        {"v": [127], "w": [1]},
        schema={"v": pl.Int8, "w": pl.Int8},
    ),
    "subtract": OptionSpec(
        FK_ARITH.SUBTRACT,
        "overflow",
        "",
        "int8",
        lambda: ma.col("v").subtract(ma.col("w"), overflow=""),
        lambda: ma.col("v").subtract(ma.col("w")),
        {"v": [-128], "w": [1]},
        schema={"v": pl.Int8, "w": pl.Int8},
    ),
    "multiply": OptionSpec(
        FK_ARITH.MULTIPLY,
        "overflow",
        "",
        "int8",
        lambda: ma.col("v").multiply(ma.col("w"), overflow=""),
        lambda: ma.col("v").multiply(ma.col("w")),
        {"v": [64], "w": [2]},
        schema={"v": pl.Int8, "w": pl.Int8},
    ),
    "divide": OptionSpec(
        FK_ARITH.DIVIDE,
        "overflow",
        "",
        "int8",
        lambda: ma.col("v").divide(ma.col("w"), overflow=""),
        lambda: ma.col("v").divide(ma.col("w")),
        {"v": [-128], "w": [-1]},
        schema={"v": pl.Int8, "w": pl.Int8},
    ),
    "modulus": OptionSpec(
        FK_ARITH.MODULO,
        "overflow",
        "",
        "int8",
        lambda: ma.col("v").modulus(ma.col("w"), overflow=""),
        lambda: ma.col("v").modulus(ma.col("w")),
        {"v": [-128], "w": [-1]},
        schema={"v": pl.Int8, "w": pl.Int8},
    ),
    "negate": OptionSpec(
        FK_ARITH.NEGATE,
        "overflow",
        "",
        "int8",
        lambda: ma.col("v").negate(overflow=""),
        lambda: ma.col("v").negate(),
        {"v": [-128]},
        schema={"v": pl.Int8},
    ),
    "power": OptionSpec(
        FK_ARITH.POWER,
        "overflow",
        "",
        "int64",
        lambda: ma.col("v").power(ma.col("w"), overflow=""),
        lambda: ma.col("v").power(ma.col("w")),
        # 2**63 is exactly one above signed Int64 max (2**63 - 1).
        {"v": [2], "w": [63]},
        schema={"v": pl.Int64, "w": pl.Int64},
    ),
}
_WRAPPING_OVERFLOW_OPS = frozenset(_OVERFLOW_SPECS) - {"divide"}
_OVERFLOW_PROBE_EXEMPT = {
    (op, backend, "SILENT")
    for op in _WRAPPING_OVERFLOW_OPS
    for backend in ("polars", "narwhals-polars", "narwhals-pandas")
}
_IBIS_INTENDED_ERROR_OVERFLOW_OPS = {
    "add",
    "subtract",
    "multiply",
    "modulus",
    "negate",
}
_OVERFLOW_PROBE_EXEMPT.update(
    (op, "ibis", "ERROR") for op in _IBIS_INTENDED_ERROR_OVERFLOW_OPS
)
_OVERFLOW_DECLARED = {
    (op, backend, value)
    for op in _OVERFLOW_SPECS
    for backend in ALL_BACKENDS
    for value in _ABS_VALUES
    if (op, backend, value) not in _OVERFLOW_PROBE_EXEMPT
}


def _overflow_probe(op: str, value: str) -> OptionSpec:
    template = _OVERFLOW_SPECS[op]
    builders = {
        "add": lambda: ma.col("v").add(ma.col("w"), overflow=value),
        "subtract": lambda: ma.col("v").subtract(ma.col("w"), overflow=value),
        "multiply": lambda: ma.col("v").multiply(ma.col("w"), overflow=value),
        "divide": lambda: ma.col("v").divide(ma.col("w"), overflow=value),
        "modulus": lambda: ma.col("v").modulus(ma.col("w"), overflow=value),
        "negate": lambda: ma.col("v").negate(overflow=value),
        "power": lambda: ma.col("v").power(ma.col("w"), overflow=value),
    }
    return OptionSpec(
        template.fkey,
        template.option_param,
        value,
        template.dtype,
        builders[op],
        template.reference_expr,
        template.data,
        template.schema,
    )


OPTION_DISPOSITIONS.extend(
    OptionCell(
        _OVERFLOW_SPECS[op].fkey,
        _ARITH_PROTOCOL,
        op,
        "overflow",
        backend,
        value,
        _OVERFLOW_SPECS[op].dtype,
        (
            "probe_exempt"
            if (op, backend, value) in _OVERFLOW_PROBE_EXEMPT
            else "declared_unsupported"
        ),
        (
            "intended-error-path"
            if op in _IBIS_INTENDED_ERROR_OVERFLOW_OPS
            and backend == "ibis"
            and value == "ERROR"
            else "explicit SILENT selects native i64 power wrapping and is "
            "indistinguishable from omission"
            if op == "power"
            and (op, backend, value) in _OVERFLOW_PROBE_EXEMPT
            else "explicit SILENT selects native integer wrapping and is "
            "indistinguishable from omission"
            if (op, backend, value) in _OVERFLOW_PROBE_EXEMPT
            else "native behavior does not implement the pinned i64 power "
            "overflow mode"
            if op == "power"
            else "native behavior does not implement the requested overflow mode"
        ),
    )
    for op in _OVERFLOW_SPECS
    for backend in ALL_BACKENDS
    for value in _ABS_VALUES
)


_IBIS_OVERFLOW_ERRORS = frozenset(
    {"add", "subtract", "multiply", "modulus", "negate"}
)
REGISTERED_OPTION_PROBES.extend(
    OptionProbeRegistration(
        _overflow_probe(op, value),
        backend,
        "declared_unsupported",
        (
            _duckdb.OutOfRangeException
            if backend == "ibis" and op in _IBIS_OVERFLOW_ERRORS
            else OptionProbeDidNotDiscriminateError
        ),
    )
    for op, backend, value in sorted(_OVERFLOW_DECLARED)
)
REGISTERED_OPTION_PROBES.extend(
    OptionProbeRegistration(
        _overflow_probe(op, value)._replace(
            expected_discriminates=False,
            expected_native_exception=(
                _duckdb.OutOfRangeException
                if backend == "ibis" and value == "ERROR"
                else None
            ),
        ),
        backend,
        "probe_exempt",
    )
    for op, backend, value in sorted(_OVERFLOW_PROBE_EXEMPT)
)


_ROUNDING_VALUES = (
    "CEILING",
    "FLOOR",
    "TIE_AWAY_FROM_ZERO",
    "TIE_TO_EVEN",
    "TRUNCATE",
)
_ROUNDING_FKEYS = {
    "acos": FK_ARITH.ACOS,
    "acosh": FK_ARITH.ACOSH,
    "add": FK_ARITH.ADD,
    "asin": FK_ARITH.ASIN,
    "asinh": FK_ARITH.ASINH,
    "atan": FK_ARITH.ATAN,
    "atan2": FK_ARITH.ATAN2,
    "atanh": FK_ARITH.ATANH,
    "cos": FK_ARITH.COS,
    "cosh": FK_ARITH.COSH,
    "degrees": FK_ARITH.DEGREES,
    "divide": FK_ARITH.DIVIDE,
    "exp": FK_ARITH.EXP,
    "multiply": FK_ARITH.MULTIPLY,
    "radians": FK_ARITH.RADIANS,
    "sin": FK_ARITH.SIN,
    "sinh": FK_ARITH.SINH,
    "sqrt": FK_ARITH.SQRT,
    "subtract": FK_ARITH.SUBTRACT,
    "tan": FK_ARITH.TAN,
    "tanh": FK_ARITH.TANH,
}
_ROUNDING_BINARY_OPS = {"add", "subtract", "multiply", "divide", "atan2"}
_ROUNDING_INPUTS = {
    "add": ({"v": [1.0], "w": [2.0**-53]}, {"v": pl.Float64, "w": pl.Float64}),
    "subtract": ({"v": [1.0], "w": [0.1]}, {"v": pl.Float64, "w": pl.Float64}),
    "multiply": ({"v": [0.1], "w": [0.2]}, {"v": pl.Float64, "w": pl.Float64}),
    "divide": ({"v": [1.0], "w": [10.0]}, {"v": pl.Float64, "w": pl.Float64}),
    "atan2": ({"v": [0.1], "w": [0.2]}, {"v": pl.Float64, "w": pl.Float64}),
    "acosh": ({"v": [2.0]}, {"v": pl.Float64}),
    "sqrt": ({"v": [2.0]}, {"v": pl.Float64}),
    **{
        op: ({"v": [0.1]}, {"v": pl.Float64})
        for op in _ROUNDING_FKEYS
        if op not in {"add", "subtract", "multiply", "divide", "atan2", "acosh", "sqrt"}
    },
}


def _rounding_expr(op: str, value: str | None = None):
    kwargs = {} if value is None else {"rounding": value}
    method = getattr(ma.col("v"), op)
    if op in _ROUNDING_BINARY_OPS:
        return method(ma.col("w"), **kwargs)
    return method(**kwargs)


def _rounding_probe(op: str, value: str) -> OptionSpec:
    data, schema = _ROUNDING_INPUTS[op]
    return OptionSpec(
        _ROUNDING_FKEYS[op],
        "rounding",
        value,
        "float64",
        lambda: _rounding_expr(op, value),
        lambda: _rounding_expr(op),
        data,
        schema,
    )


_IBIS_UNIMPLEMENTED_ROUNDING_OPS = {
    "acosh",
    "asinh",
    "atanh",
    "cosh",
    "sinh",
    "tanh",
}
_NARWHALS_IMPLEMENTED_ROUNDING_OPS = {
    "add",
    "divide",
    "exp",
    "multiply",
    "sqrt",
    "subtract",
}


def _rounding_native_failure(op: str, backend: str) -> type[BaseException]:
    if backend == "ibis" and op in _IBIS_UNIMPLEMENTED_ROUNDING_OPS:
        return NotImplementedError
    if backend.startswith("narwhals") and op not in _NARWHALS_IMPLEMENTED_ROUNDING_OPS:
        return NotImplementedError
    return OptionProbeDidNotDiscriminateError


OPTION_DISPOSITIONS.extend(
    OptionCell(
        fkey,
        _ARITH_PROTOCOL,
        op,
        "rounding",
        backend,
        value,
        "float64",
        "declared_unsupported",
        "native behavior does not implement the requested IEEE rounding mode",
    )
    for op, fkey in _ROUNDING_FKEYS.items()
    for backend in ALL_BACKENDS
    for value in _ROUNDING_VALUES
)

OPTION_FAMILY_DEFAULT_FACT_KEYS.update(
    (
        cell.fkey,
        cell.param,
        cell.value,
        CONST_BACKEND.IBIS,
        None,
    )
    for cell in OPTION_DISPOSITIONS
    if cell.protocol == _ARITH_PROTOCOL
    and cell.fixture == "ibis"
    and cell.disposition != "invalid"
)


# Invalid strings are unbounded, so the matrix uses one canonical sentinel per
# activated owner/dtype.  Rejection happens while building the AST, before a
# backend is selected, but OptionCell retains all fixture identities because
# fixture remains part of the matrix schema.
_INVALID_OPTION_REJECTIONS = [
    InvalidOptionRejection(
        FK_ARITH.ABS,
        _ARITH_PROTOCOL,
        "abs",
        "overflow",
        INVALID_OPTION_VALUE,
        "int8",
        lambda: ma.col("v").abs(overflow=INVALID_OPTION_VALUE),
    ),
    *(
        InvalidOptionRejection(
            _SEMANTIC_FKEYS[op],
            _ARITH_PROTOCOL,
            op,
            param,
            INVALID_OPTION_VALUE,
            "int64" if op == "modulus" else "float64",
            lambda op=op, param=param: _semantic_expr(
                op, param, INVALID_OPTION_VALUE
            ),
        )
        for op, param in _SEMANTIC_VALUES
    ),
    *(
        InvalidOptionRejection(
            spec.fkey,
            _ARITH_PROTOCOL,
            op,
            "overflow",
            INVALID_OPTION_VALUE,
            spec.dtype,
            lambda op=op: _overflow_probe(op, INVALID_OPTION_VALUE).build_expr(),
        )
        for op, spec in _OVERFLOW_SPECS.items()
    ),
    *(
        InvalidOptionRejection(
            fkey,
            _ARITH_PROTOCOL,
            op,
            "rounding",
            INVALID_OPTION_VALUE,
            "float64",
            lambda op=op: _rounding_expr(op, INVALID_OPTION_VALUE),
        )
        for op, fkey in _ROUNDING_FKEYS.items()
    ),
]
REGISTERED_INVALID_OPTION_REJECTIONS.extend(_INVALID_OPTION_REJECTIONS)
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
    for rejection in _INVALID_OPTION_REJECTIONS
    for backend in ALL_BACKENDS
)


@pytest.mark.parametrize(
    "rejection",
    _INVALID_OPTION_REJECTIONS,
    ids=lambda rejection: f"{rejection.op}-{rejection.param}-{rejection.dtype}",
)
def test_arithmetic_canonical_invalid_option_rejected_at_build_time(
    rejection: InvalidOptionRejection,
) -> None:
    with pytest.raises(InvalidOptionValueError):
        rejection.build_expr()


REGISTERED_OPTION_PROBES.extend(
    OptionProbeRegistration(
        _rounding_probe(op, value),
        backend,
        "declared_unsupported",
        _rounding_native_failure(op, backend),
    )
    for op in _ROUNDING_FKEYS
    for backend in ALL_BACKENDS
    for value in _ROUNDING_VALUES
)


def test_power_overflow_probe_uses_pinned_int64_boundary() -> None:
    spec = _OVERFLOW_SPECS["power"]

    assert spec.dtype == "int64"
    assert spec.data == {"v": [2], "w": [63]}
    assert spec.schema == {"v": pl.Int64, "w": pl.Int64}


TESTED_OPTION_PARAMS = [
    (
        _ARITH_PROTOCOL,
        "abs",
        "overflow",
        param_taxonomy(_ARITH_PROTOCOL, "abs", "overflow"),
    ),
    *(
        (
            _ARITH_PROTOCOL,
            op,
            "overflow",
            param_taxonomy(_ARITH_PROTOCOL, op, "overflow"),
        )
        for op in _OVERFLOW_SPECS
    ),
    *(
        (
            _ARITH_PROTOCOL,
            op,
            param,
            param_taxonomy(_ARITH_PROTOCOL, op, param),
        )
        for op, param in _SEMANTIC_VALUES
    ),
    *(
        (
            _ARITH_PROTOCOL,
            op,
            "rounding",
            param_taxonomy(_ARITH_PROTOCOL, op, "rounding"),
        )
        for op in _ROUNDING_FKEYS
    ),
]


def _assert_requested_semantics(value: str, got: list[object]) -> None:
    if value == "FLOOR":
        assert got == [1]
    elif value == "TRUNCATE":
        assert got == [-2]
    elif value in {"NAN", "IEEE"}:
        assert len(got) == 1
        assert isinstance(got[0], float) and math.isnan(got[0])
    elif value == "NULL":
        assert got == [None]
    elif value == "LIMIT":
        assert got == [math.inf]
    else:
        raise AssertionError(f"no result assertion for {value}")


@pytest.mark.parametrize(
    "op,param,backend,value",
    sorted(_SEMANTIC_DECLARED),
    ids=lambda value: str(value),
)
def test_arithmetic_semantic_option_declared_unsupported(
    op, param, backend, value, request
):
    spec = _semantic_probe(op, param, value)
    request.applymarker(
        xfail_option_unsupported(spec.fkey, param, value, backend)
    )
    df = make_df(spec.data, backend, schema=spec.schema)
    got = option_result(df, spec.build_expr(), backend)
    if value == "ERROR":
        pytest.fail("requested ERROR semantics returned a value")
    _assert_requested_semantics(value, got)


@pytest.mark.parametrize(
    "op,param,backend,value",
    sorted(_SEMANTIC_EXEMPT),
    ids=lambda value: str(value),
)
def test_arithmetic_semantic_option_matches_native_requested_semantics(
    op, param, backend, value
):
    spec = _semantic_probe(op, param, value)
    if (op, param, backend, value) in _SEMANTIC_INTENDED_ERROR:
        with pytest.raises(_SEMANTIC_INTENDED_ERROR[(op, param, backend, value)]):
            option_result(
                make_df(spec.data, backend, schema=spec.schema),
                spec.build_expr(),
                backend,
            )
        return
    df = make_df(spec.data, backend, schema=spec.schema)
    _assert_requested_semantics(
        value, option_result(df, spec.build_expr(), backend)
    )


@pytest.mark.parametrize("op,param", sorted(_SEMANTIC_VALUES))
@pytest.mark.parametrize("value", [INVALID_OPTION_VALUE, "nan", ""])
def test_arithmetic_semantic_option_rejects_invalid_value_at_build_time(
    op, param, value
):
    with pytest.raises(InvalidOptionValueError):
        _semantic_expr(op, param, value)


@pytest.mark.parametrize(
    "op,backend,value",
    sorted(_OVERFLOW_DECLARED),
    ids=lambda value: str(value),
)
def test_arithmetic_overflow_declared_unsupported(op, backend, value, request):
    spec = _overflow_probe(op, value)
    request.applymarker(
        xfail_option_unsupported(spec.fkey, "overflow", value, backend)
    )
    df = make_df(spec.data, backend, schema=spec.schema)
    got = option_result(df, spec.build_expr(), backend)
    assert got != option_result(df, spec.reference_expr(), backend)


@pytest.mark.parametrize(
    "op,backend",
    sorted(
        {(op, backend) for op, backend, value in _OVERFLOW_PROBE_EXEMPT if value == "SILENT"}
    ),
)
def test_arithmetic_overflow_silent_matches_native_wrapping(op, backend):
    spec = _overflow_probe(op, "SILENT")
    df = make_df(spec.data, backend, schema=spec.schema)
    assert option_result(df, spec.build_expr(), backend) == option_result(
        df, spec.reference_expr(), backend
    )


@pytest.mark.parametrize("op", sorted(_OVERFLOW_SPECS))
@pytest.mark.parametrize("value", ["WRAP", "error", ""])
def test_arithmetic_overflow_rejects_invalid_value_at_build_time(op, value):
    with pytest.raises(InvalidOptionValueError):
        _overflow_probe(op, value).build_expr()


@pytest.mark.parametrize("op", sorted(_ROUNDING_FKEYS))
@pytest.mark.parametrize("backend", ALL_BACKENDS)
@pytest.mark.parametrize("value", _ROUNDING_VALUES)
def test_arithmetic_rounding_declared_unsupported(op, backend, value, request):
    spec = _rounding_probe(op, value)
    request.applymarker(
        xfail_option_unsupported(spec.fkey, "rounding", value, backend)
    )
    df = make_df(spec.data, backend, schema=spec.schema)
    assert option_result(df, spec.build_expr(), backend) != option_result(
        df, spec.reference_expr(), backend
    )


@pytest.mark.parametrize("op", sorted(_ROUNDING_FKEYS))
@pytest.mark.parametrize("value", [INVALID_OPTION_VALUE, "ceiling", ""])
def test_arithmetic_rounding_rejects_invalid_value_at_build_time(op, value):
    with pytest.raises(InvalidOptionValueError):
        _rounding_expr(op, value)


@pytest.mark.parametrize(
    "backend,value",
    sorted(_ABS_DECLARED),
    ids=lambda value: str(value),
)
def test_abs_overflow_declared_unsupported(backend, value, request):
    request.applymarker(
        xfail_option_unsupported(FK_ARITH.ABS, "overflow", value, backend)
    )
    df = make_df({"v": [-128]}, backend, schema={"v": pl.Int8})
    got = option_result(df, ma.col("v").abs(overflow=value), backend)
    assert got == [128]


@pytest.mark.parametrize(
    "backend",
    sorted({backend for backend, value in _ABS_PROBE_EXEMPT if value == "SILENT"}),
)
def test_abs_overflow_silent_matches_native_wrapping(backend):
    df = make_df({"v": [-128]}, backend, schema={"v": pl.Int8})
    assert option_result(df, ma.col("v").abs(overflow="SILENT"), backend) == [-128]


@pytest.mark.parametrize(
    ("op", "expected_exception"),
    [
        ("abs", _duckdb.OutOfRangeException),
        ("add", _duckdb.OutOfRangeException),
        ("subtract", _duckdb.OutOfRangeException),
        ("multiply", _duckdb.OutOfRangeException),
        ("modulus", _duckdb.OutOfRangeException),
        ("negate", _duckdb.OutOfRangeException),
        ("acos", _duckdb.InvalidInputException),
        ("asin", _duckdb.InvalidInputException),
        ("sqrt", _duckdb.OutOfRangeException),
    ],
)
def test_ibis_duckdb_intended_error_option_reaches_native_exception(
    op: str, expected_exception: type[BaseException]
) -> None:
    if op == "abs":
        spec = _abs_probe("ERROR")
    elif op in _OVERFLOW_SPECS:
        spec = _overflow_probe(op, "ERROR")
    else:
        spec = _semantic_probe(op, "on_domain_error", "ERROR")

    df = make_df(spec.data, "ibis", schema=spec.schema)
    with pytest.raises(expected_exception) as caught:
        option_result(df, spec.build_expr(), "ibis")
    assert type(caught.value) is expected_exception


@pytest.mark.parametrize("value", ["WRAP", "error", ""])
def test_abs_overflow_rejects_invalid_value_at_build_time(value):
    with pytest.raises(InvalidOptionValueError):
        ma.col("v").abs(overflow=value)

OP_SPECS: list[OpSpec] = [
    OpSpec(
        function_key=FK_ARITH.ADD,
        op_name="add",
        build=lambda col, arg: col.add(arg),
        raw_arg=10,
        arg_col_name="b",
        param_name="y",
        input_col="a",
        data={"a": [1, 2, 3], "b": [10, 20, 30]},
    ),
    OpSpec(
        function_key=FK_ARITH.SUBTRACT,
        op_name="subtract",
        build=lambda col, arg: col.sub(arg),
        raw_arg=1,
        arg_col_name="b",
        param_name="y",
        input_col="a",
        data={"a": [10, 20, 30], "b": [1, 2, 3]},
    ),
    OpSpec(
        function_key=FK_ARITH.MULTIPLY,
        op_name="multiply",
        build=lambda col, arg: col.mul(arg),
        raw_arg=2,
        arg_col_name="b",
        param_name="y",
        input_col="a",
        data={"a": [1, 2, 3], "b": [2, 3, 4]},
    ),
    OpSpec(
        function_key=FK_ARITH.DIVIDE,
        op_name="divide",
        build=lambda col, arg: col.truediv(arg),
        raw_arg=2,
        arg_col_name="b",
        param_name="y",
        input_col="a",
        data={"a": [10, 20, 30], "b": [2, 5, 10]},
    ),
    OpSpec(
        function_key=FK_MA_ARITH.FLOOR_DIVIDE,
        op_name="floor_divide",
        build=lambda col, arg: col.floordiv(arg),
        raw_arg=3,
        arg_col_name="b",
        param_name="y",
        input_col="a",
        data={"a": [10, 20, 30], "b": [3, 7, 4]},
    ),
    OpSpec(
        function_key=FK_ARITH.POWER,
        op_name="power",
        build=lambda col, arg: col.pow(arg),
        raw_arg=2,
        arg_col_name="b",
        param_name="y",
        input_col="a",
        data={"a": [2, 3, 4], "b": [2, 3, 2]},
    ),
    OpSpec(
        function_key=FK_ARITH.MODULO,
        op_name="modulus",
        build=lambda col, arg: col.mod(arg),
        raw_arg=3,
        arg_col_name="b",
        param_name="y",
        input_col="a",
        data={"a": [10, 21, 30], "b": [3, 4, 7]},
    ),
    OpSpec(
        function_key=FK_ARITH.ATAN2,
        op_name="atan2",
        build=lambda col, arg: col.atan2(arg),
        raw_arg=1.0,
        arg_col_name="b",
        param_name="y",
        input_col="a",
        data={"a": [1.0, 2.0, 3.0], "b": [0.5, 1.0, 1.5]},
    ),
]

# atan2 raises NotImplementedError on both narwhals backends (not a registry-tracked
# limitation); mark all input types as xfail for those backends.
_ATAN2_NW_XFAIL = pytest.mark.xfail(
    strict=True,
    raises=NotImplementedError,
    reason="atan2() is not supported by the Narwhals backend.",
)
_ATAN2_NW_BACKENDS = {"narwhals-polars", "narwhals-pandas"}


def _params():
    cases = []
    for op in OP_SPECS:
        for bk in ALL_BACKENDS:
            for it in INPUT_TYPES:
                mark = xfail_if_limited(bk, op.function_key, op.param_name, it)
                marks = [mark] if mark else []
                if op.op_name == "atan2" and bk in _ATAN2_NW_BACKENDS:
                    marks = [_ATAN2_NW_XFAIL]
                cases.append(
                    pytest.param(op, bk, it, marks=marks, id=f"{op.op_name}-{bk}-{it}")
                )
    return cases


if OP_SPECS:

    @pytest.mark.parametrize("op,backend,input_type", _params())
    def test_argument_channel(op: OpSpec, backend: str, input_type: str):
        run_argument_matrix(op, backend, input_type)
