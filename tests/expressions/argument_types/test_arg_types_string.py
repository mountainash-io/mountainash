"""Argument channel tests for string operations."""
from __future__ import annotations

import pytest

import mountainash as ma
from expressions.argument_types._option_helpers import (
    OptionProbeDidNotDiscriminateError,
    OptionSpec,
    option_result,
    xfail_option_unsupported,
)
from expressions.argument_types.conftest import ALL_BACKENDS, make_df
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
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.errors import InvalidOptionValueError
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_api.api_builders.substrait.api_bldr_scalar_string import (
    _validated_options,
)
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_STRING as FK_MA_STR,
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)
from expressions.argument_types._test_template import (
    INPUT_TYPES,
    OpSpec,
    run_argument_matrix,
    xfail_if_limited,
)


_STRING_PROTOCOL = "SubstraitScalarStringExpressionSystemProtocol"
_CASE_SENSITIVITY_FKEYS = {
    "contains": FK_STR.CONTAINS,
    "count_substring": FK_STR.COUNT_SUBSTRING,
    "ends_with": FK_STR.ENDS_WITH,
    "like": FK_STR.LIKE,
    "replace": FK_STR.REPLACE,
    "starts_with": FK_STR.STARTS_WITH,
    "strpos": FK_STR.STRPOS,
}
_CASE_SENSITIVITY_DATA = {
    "contains": {"text": ["Hello", "other"]},
    "count_substring": {"text": ["Hello hello", "other"]},
    "ends_with": {"text": ["say Hello", "other"]},
    "like": {"text": ["say Hello", "other"]},
    "replace": {"text": ["Hello hello", "other"]},
    "starts_with": {"text": ["Hello there", "other"]},
    "strpos": {"text": ["say Hello", "other"]},
}
_CASE_INSENSITIVE_HONORED_OPS = frozenset(
    {"contains", "ends_with", "starts_with"}
)
_CASE_INSENSITIVE_DECLARED_OPS = (
    frozenset(_CASE_SENSITIVITY_FKEYS) - _CASE_INSENSITIVE_HONORED_OPS
)


def _case_sensitivity_expr(op: str, case_sensitive: bool | None = None):
    kwargs = {} if case_sensitive is None else {"case_sensitive": case_sensitive}
    string = ma.col("text").str
    if op == "contains":
        return string.contains("hello", **kwargs)
    if op == "count_substring":
        return string.count_substring("hello", **kwargs)
    if op == "ends_with":
        return string.ends_with("hello", **kwargs)
    if op == "like":
        return string.like("%hello%", **kwargs)
    if op == "replace":
        return string.replace("hello", "X", **kwargs)
    if op == "starts_with":
        return string.starts_with("hello", **kwargs)
    if op == "strpos":
        return string.strpos("hello", **kwargs)
    raise AssertionError(f"no case-sensitivity expression for {op}")


def _case_sensitivity_probe(op: str, value: str) -> OptionSpec:
    return OptionSpec(
        _CASE_SENSITIVITY_FKEYS[op],
        "case_sensitivity",
        value,
        "str",
        lambda: _case_sensitivity_expr(op, value == "CASE_SENSITIVE"),
        lambda: _case_sensitivity_expr(op),
        _CASE_SENSITIVITY_DATA[op],
        expected_discriminates=value == "CASE_INSENSITIVE",
    )


def _registered_case_sensitivity_probe(
    op: str, value: str, backend: str
) -> OptionSpec:
    spec = _case_sensitivity_probe(op, value)
    if (
        value == "CASE_SENSITIVE"
        and backend.startswith("narwhals")
        and op in {"like", "replace"}
    ):
        # These two narwhals ops require their pattern/substring as a literal
        # (gated LITERAL_ONLY on every narwhals dialect — the SQL-LIKE→regex
        # conversion and literal replace happen Python-side). The native probe
        # runs enforce_capabilities=False, which BYPASSES that gate, so the
        # literal is visited into a narwhals Expr and the raw path raises
        # ('Expr' has no attribute 'replace' for like; an Expr-literal TypeError
        # for replace) — identically for BOTH the explicit-CASE_SENSITIVE and
        # omission builds, independent of case_sensitivity. That identical raise
        # is the probe-exempt equivalence in the raw path; the value-equivalence
        # of CASE_SENSITIVE to omission is separately verified on the GATED path
        # by test_case_sensitive_string_option_matches_omission. Controller-
        # authorised refinement of the locked disposition (gate-requiring ops
        # cannot be natively probed). Self-heals: if narwhals ever compiles these
        # raw, the "did not raise" assertion fires.
        return spec._replace(
            expected_native_exception=(
                AttributeError if op == "like" else TypeError
            )
        )
    return spec


@pytest.mark.parametrize("op", sorted(_CASE_INSENSITIVE_HONORED_OPS))
@pytest.mark.parametrize("backend", ALL_BACKENDS)
def test_case_insensitive_string_option_discriminates(op, backend):
    spec = _case_sensitivity_probe(op, "CASE_INSENSITIVE")
    df = make_df(spec.data, backend)

    assert option_result(df, spec.build_expr(), backend) != option_result(
        df, spec.reference_expr(), backend
    )


@pytest.mark.parametrize("op", sorted(_CASE_INSENSITIVE_DECLARED_OPS))
@pytest.mark.parametrize("backend", ALL_BACKENDS)
def test_case_insensitive_string_option_declared_unsupported(
    op, backend, request
):
    spec = _case_sensitivity_probe(op, "CASE_INSENSITIVE")
    request.applymarker(
        xfail_option_unsupported(
            spec.fkey, spec.option_param, spec.option_value, backend
        )
    )
    df = make_df(spec.data, backend)

    assert option_result(df, spec.build_expr(), backend) != option_result(
        df, spec.reference_expr(), backend
    )


@pytest.mark.parametrize("op", sorted(_CASE_SENSITIVITY_FKEYS))
@pytest.mark.parametrize("backend", ALL_BACKENDS)
def test_case_sensitive_string_option_matches_omission(op, backend):
    spec = _case_sensitivity_probe(op, "CASE_SENSITIVE")
    df = make_df(spec.data, backend)

    assert option_result(df, spec.build_expr(), backend) == option_result(
        df, spec.reference_expr(), backend
    )


_CASE_SENSITIVITY_VALUES = ("CASE_SENSITIVE", "CASE_INSENSITIVE")
_CASE_INSENSITIVE_NATIVE_FAILURES = {
    (op, backend): (
        AttributeError
        if op == "like" and backend.startswith("narwhals")
        else TypeError
        if op == "replace" and backend.startswith("narwhals")
        else OptionProbeDidNotDiscriminateError
    )
    for op in _CASE_INSENSITIVE_DECLARED_OPS
    for backend in ALL_BACKENDS
}


OPTION_DISPOSITIONS.extend(
    OptionCell(
        fkey,
        _STRING_PROTOCOL,
        op,
        "case_sensitivity",
        backend,
        value,
        "str",
        (
            "probe_exempt"
            if value == "CASE_SENSITIVE"
            else "honored"
            if op in _CASE_INSENSITIVE_HONORED_OPS
            else "declared_unsupported"
        ),
        (
            "builder-default CASE_SENSITIVE is indistinguishable from omission"
            if value == "CASE_SENSITIVE"
            else "native backend implements CASE_INSENSITIVE semantics"
            if op in _CASE_INSENSITIVE_HONORED_OPS
            else "native backend does not implement CASE_INSENSITIVE semantics"
        ),
    )
    for op, fkey in _CASE_SENSITIVITY_FKEYS.items()
    for backend in ALL_BACKENDS
    for value in _CASE_SENSITIVITY_VALUES
)

REGISTERED_OPTION_PROBES.extend(
    OptionProbeRegistration(
        _registered_case_sensitivity_probe(op, value, backend),
        backend,
        (
            "probe_exempt"
            if value == "CASE_SENSITIVE"
            else "honored"
            if op in _CASE_INSENSITIVE_HONORED_OPS
            else "declared_unsupported"
        ),
        (
            _CASE_INSENSITIVE_NATIVE_FAILURES[(op, backend)]
            if value == "CASE_INSENSITIVE"
            and op in _CASE_INSENSITIVE_DECLARED_OPS
            else None
        ),
    )
    for op in _CASE_SENSITIVITY_FKEYS
    for backend in ALL_BACKENDS
    for value in _CASE_SENSITIVITY_VALUES
)

OPTION_FAMILY_DEFAULT_FACT_KEYS.update(
    (
        _CASE_SENSITIVITY_FKEYS[op],
        "case_sensitivity",
        "CASE_INSENSITIVE",
        CONST_BACKEND.IBIS,
        None,
    )
    for op in _CASE_INSENSITIVE_DECLARED_OPS
)

_INVALID_CASE_SENSITIVITY_REJECTIONS = [
    InvalidOptionRejection(
        fkey,
        _STRING_PROTOCOL,
        op,
        "case_sensitivity",
        INVALID_OPTION_VALUE,
        "str",
        lambda op=op: _validated_options(
            op, case_sensitivity=INVALID_OPTION_VALUE
        ),
    )
    for op, fkey in _CASE_SENSITIVITY_FKEYS.items()
]
REGISTERED_INVALID_OPTION_REJECTIONS.extend(
    _INVALID_CASE_SENSITIVITY_REJECTIONS
)
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
    for rejection in _INVALID_CASE_SENSITIVITY_REJECTIONS
    for backend in ALL_BACKENDS
)


@pytest.mark.parametrize(
    "rejection",
    _INVALID_CASE_SENSITIVITY_REJECTIONS,
    ids=lambda rejection: f"{rejection.op}-{rejection.param}-{rejection.dtype}",
)
def test_string_canonical_invalid_option_rejected_at_build_time(
    rejection: InvalidOptionRejection,
) -> None:
    with pytest.raises(InvalidOptionValueError):
        rejection.build_expr()


TESTED_OPTION_PARAMS = [
    (
        _STRING_PROTOCOL,
        op,
        "case_sensitivity",
        param_taxonomy(_STRING_PROTOCOL, op, "case_sensitivity"),
    )
    for op in _CASE_SENSITIVITY_FKEYS
]


_REGEXP_FLAG_FKEYS = {
    "case_sensitivity": {
        "regexp_match_substring": FK_STR.REGEXP_MATCH,
        "regexp_match_substring_all": FK_STR.REGEXP_MATCH_ALL,
        "regexp_strpos": FK_STR.REGEXP_STRPOS,
        "regexp_count_substring": FK_STR.REGEXP_COUNT,
        "regexp_replace": FK_STR.REGEXP_REPLACE,
        "regexp_string_split": FK_STR.REGEXP_SPLIT,
    },
    "multiline": {
        "regexp_match_substring": FK_STR.REGEXP_MATCH,
        "regexp_match_substring_all": FK_STR.REGEXP_MATCH_ALL,
        "regexp_strpos": FK_STR.REGEXP_STRPOS,
        "regexp_count_substring": FK_STR.REGEXP_COUNT,
    },
    "dotall": {
        "regexp_match_substring": FK_STR.REGEXP_MATCH,
        "regexp_match_substring_all": FK_STR.REGEXP_MATCH_ALL,
        "regexp_strpos": FK_STR.REGEXP_STRPOS,
        "regexp_count_substring": FK_STR.REGEXP_COUNT,
    },
}
_REGEXP_FLAG_VALUES = {
    "case_sensitivity": ("CASE_SENSITIVE", "CASE_INSENSITIVE"),
    "multiline": ("MULTILINE_DISABLED", "MULTILINE_ENABLED"),
    "dotall": ("DOTALL_DISABLED", "DOTALL_ENABLED"),
}
_REGEXP_FLAG_DEFAULTS = {
    "case_sensitivity": "CASE_SENSITIVE",
    "multiline": "MULTILINE_DISABLED",
    "dotall": "DOTALL_DISABLED",
}
_REGEXP_FLAG_DATA = {
    "case_sensitivity": ({"text": ["Hello"]}, "hello"),
    "multiline": ({"text": ["a\nb"]}, "^b"),
    "dotall": ({"text": ["a\nb"]}, "a.b"),
}
_REGEXP_UNSUPPORTED_OPS = frozenset(
    {
        "regexp_match_substring_all",
        "regexp_strpos",
        "regexp_count_substring",
    }
)


def _regexp_operation_unsupported(op: str, backend: str) -> bool:
    return op in _REGEXP_UNSUPPORTED_OPS and backend != "polars"


def _regexp_flag_disposition(op: str, param: str, value: str, backend: str) -> str:
    if _regexp_operation_unsupported(op, backend):
        return "declared_unsupported"
    if value == _REGEXP_FLAG_DEFAULTS[param]:
        return "probe_exempt"
    return "declared_unsupported"


def _regexp_flag_expr(op: str, param: str, value: str | None = None):
    """Build a regexp flag expression, omitting the flag when value is None."""
    kwargs = {}
    if value is not None:
        kwargs = {
            {
                "case_sensitivity": "case_sensitive",
                "multiline": "multiline",
                "dotall": "dotall",
            }[param]: (
                value == _REGEXP_FLAG_DEFAULTS[param]
                if param == "case_sensitivity"
                else value == _REGEXP_FLAG_VALUES[param][1]
            )
        }
    _, pattern = _REGEXP_FLAG_DATA[param]
    string = ma.col("text").str
    if op == "regexp_match_substring":
        return string.regexp_match_substring(pattern, **kwargs)
    if op == "regexp_match_substring_all":
        return string.regexp_match_substring_all(pattern, **kwargs)
    if op == "regexp_strpos":
        return string.regexp_strpos(pattern, **kwargs)
    if op == "regexp_count_substring":
        return string.regexp_count_substring(pattern, **kwargs)
    if op == "regexp_replace":
        return string.regexp_replace(pattern, "X", **kwargs)
    if op == "regexp_string_split":
        return string.regexp_string_split(pattern, **kwargs)
    raise AssertionError(f"no regexp flag expression for {op}")


def _regexp_flag_probe(op: str, param: str, value: str) -> OptionSpec:
    data, _ = _REGEXP_FLAG_DATA[param]
    return OptionSpec(
        _REGEXP_FLAG_FKEYS[param][op],
        param,
        value,
        "str",
        lambda: _regexp_flag_expr(op, param, value),
        lambda: _regexp_flag_expr(op, param),
        data,
        expected_discriminates=value != _REGEXP_FLAG_DEFAULTS[param],
    )


def _regexp_flag_native_exception(op: str, backend: str):
    if _regexp_operation_unsupported(op, backend):
        return BackendCapabilityError
    if op == "regexp_replace" and backend.startswith("narwhals"):
        return TypeError
    return None


def _registered_regexp_flag_probe(
    op: str, param: str, value: str, backend: str
) -> OptionSpec:
    spec = _regexp_flag_probe(op, param, value)
    native_exception = _regexp_flag_native_exception(op, backend)
    if (
        native_exception is not None
        and value == _REGEXP_FLAG_DEFAULTS[param]
        and not _regexp_operation_unsupported(op, backend)
    ):
        # Narwhals regexp_replace runs on the public gated path, but its raw,
        # gate-bypassing literal path raises identically for explicit-default
        # and omission. Keep that runnable operation probe-exempt; declared
        # probes leave their raw exceptions to the strict xfail registration.
        return spec._replace(expected_native_exception=native_exception)
    return spec


@pytest.mark.parametrize(
    "param,op",
    [
        (param, op)
        for param, operations in _REGEXP_FLAG_FKEYS.items()
        for op in operations
    ],
)
@pytest.mark.parametrize("backend", ALL_BACKENDS)
def test_default_regexp_flag_matches_omission(param, op, backend):
    default = _REGEXP_FLAG_DEFAULTS[param]
    spec = _regexp_flag_probe(op, param, default)
    df = make_df(spec.data, backend)
    if _regexp_operation_unsupported(op, backend):
        # Both builds emit the default enum value, whose dialect-scoped option
        # fact now blocks dispatch before the unavailable backend method runs.
        for expression in (spec.build_expr(), spec.reference_expr()):
            with pytest.raises(BackendCapabilityError) as exc_info:
                option_result(df, expression, backend)
            limitation = exc_info.value.limitation
            assert limitation is not None
            assert limitation.operation_key is spec.fkey
            assert limitation.param in _REGEXP_FLAG_FKEYS
            assert (
                limitation.option_value
                == _REGEXP_FLAG_DEFAULTS[limitation.param]
            )
            assert limitation.level.name == "UNSUPPORTED"
        return

    assert option_result(df, spec.build_expr(), backend) == option_result(
        df, spec.reference_expr(), backend
    )


@pytest.mark.parametrize(
    "param,op",
    [
        (param, op)
        for param, operations in _REGEXP_FLAG_FKEYS.items()
        for op in operations
    ],
)
@pytest.mark.parametrize("backend", ALL_BACKENDS)
def test_enabled_regexp_flag_declared_unsupported(param, op, backend, request):
    enabled = _REGEXP_FLAG_VALUES[param][1]
    spec = _regexp_flag_probe(op, param, enabled)
    request.applymarker(
        xfail_option_unsupported(
            spec.fkey, spec.option_param, spec.option_value, backend
        )
    )
    df = make_df(spec.data, backend)

    assert option_result(df, spec.build_expr(), backend) != option_result(
        df, spec.reference_expr(), backend
    )


def _regexp_flag_invalid_expr(op: str, param: str):
    keyword = {
        "case_sensitivity": "case_sensitive",
        "multiline": "multiline",
        "dotall": "dotall",
    }[param]
    _, pattern = _REGEXP_FLAG_DATA[param]
    string = ma.col("text").str
    kwargs = {keyword: INVALID_OPTION_VALUE}
    if op == "regexp_match_substring":
        return string.regexp_match_substring(pattern, **kwargs)
    if op == "regexp_match_substring_all":
        return string.regexp_match_substring_all(pattern, **kwargs)
    if op == "regexp_strpos":
        return string.regexp_strpos(pattern, **kwargs)
    if op == "regexp_count_substring":
        return string.regexp_count_substring(pattern, **kwargs)
    if op == "regexp_replace":
        return string.regexp_replace(pattern, "X", **kwargs)
    if op == "regexp_string_split":
        return string.regexp_string_split(pattern, **kwargs)
    raise AssertionError(f"no regexp flag expression for {op}")


_INVALID_REGEXP_FLAG_REJECTIONS = [
    InvalidOptionRejection(
        fkey,
        _STRING_PROTOCOL,
        op,
        param,
        INVALID_OPTION_VALUE,
        "str",
        lambda op=op, param=param: _regexp_flag_invalid_expr(op, param),
    )
    for param, operations in _REGEXP_FLAG_FKEYS.items()
    for op, fkey in operations.items()
]
REGISTERED_INVALID_OPTION_REJECTIONS.extend(_INVALID_REGEXP_FLAG_REJECTIONS)
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
    for rejection in _INVALID_REGEXP_FLAG_REJECTIONS
    for backend in ALL_BACKENDS
)


@pytest.mark.parametrize(
    "rejection",
    _INVALID_REGEXP_FLAG_REJECTIONS,
    ids=lambda rejection: f"{rejection.op}-{rejection.param}-{rejection.dtype}",
)
def test_regexp_flag_invalid_option_rejected_at_build_time(
    rejection: InvalidOptionRejection,
) -> None:
    with pytest.raises(InvalidOptionValueError):
        rejection.build_expr()


OPTION_DISPOSITIONS.extend(
    OptionCell(
        fkey,
        _STRING_PROTOCOL,
        op,
        param,
        backend,
        value,
        "str",
        _regexp_flag_disposition(op, param, value, backend),
        (
            "operation is unsupported on this backend; the option cannot be honored"
            if _regexp_operation_unsupported(op, backend)
            else f"builder-default {_REGEXP_FLAG_DEFAULTS[param]} is "
            "indistinguishable from omission"
            if value == _REGEXP_FLAG_DEFAULTS[param]
            else f"native backend does not implement {value} semantics"
        ),
    )
    for param, operations in _REGEXP_FLAG_FKEYS.items()
    for op, fkey in operations.items()
    for backend in ALL_BACKENDS
    for value in _REGEXP_FLAG_VALUES[param]
)

REGISTERED_OPTION_PROBES.extend(
    OptionProbeRegistration(
        _registered_regexp_flag_probe(op, param, value, backend),
        backend,
        _regexp_flag_disposition(op, param, value, backend),
        (
            _regexp_flag_native_exception(op, backend)
            if _regexp_flag_native_exception(op, backend) is not None
            else OptionProbeDidNotDiscriminateError
        )
        if _regexp_flag_disposition(op, param, value, backend)
        == "declared_unsupported"
        else None,
    )
    for param, operations in _REGEXP_FLAG_FKEYS.items()
    for op in operations
    for backend in ALL_BACKENDS
    for value in _REGEXP_FLAG_VALUES[param]
)

OPTION_FAMILY_DEFAULT_FACT_KEYS.update(
    (
        fkey,
        param,
        _REGEXP_FLAG_VALUES[param][1],
        CONST_BACKEND.IBIS,
        None,
    )
    for param, operations in _REGEXP_FLAG_FKEYS.items()
    for fkey in operations.values()
)
OPTION_FAMILY_DEFAULT_FACT_KEYS.update(
    (
        fkey,
        param,
        _REGEXP_FLAG_DEFAULTS[param],
        CONST_BACKEND.IBIS,
        None,
    )
    for param, operations in _REGEXP_FLAG_FKEYS.items()
    for op, fkey in operations.items()
    if op in _REGEXP_UNSUPPORTED_OPS
)

TESTED_OPTION_PARAMS.extend(
    (
        _STRING_PROTOCOL,
        op,
        param,
        param_taxonomy(_STRING_PROTOCOL, op, param),
    )
    for param, operations in _REGEXP_FLAG_FKEYS.items()
    for op in operations
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
    (FK_MA_STR.STRIP_SUFFIX, "x"),
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
    (FK_STR.REGEXP_REPLACE, "pattern"),
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
    # Newly-wired regex + split ops — OP_SPECS exist for all pattern params;
    # concat_ws.string_arguments has TESTED_PARAMS entry but no OP_SPEC (variadic limitation).
    # Note: FKEY enum name != protocol method name for these ops, so string keys are used.
    ("regexp_match_substring_all", "pattern"),
    ("regexp_count_substring", "pattern"),
    ("regexp_match_substring", "pattern"),
    ("regexp_strpos", "pattern"),
    ("regexp_string_split", "pattern"),
    ("string_split", "separator"),
    # concat_ws.string_arguments: variadic param — backend accepts a single col expression
    # but the Polars implementation only supports positional concat (no variadic column arg).
    # Tracked as a known limitation; no OP_SPEC is added.
    (FK_STR.CONCAT_WS, "string_arguments"),
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
        function_key=FK_MA_STR.STRIP_SUFFIX,
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
    # regexp_replace position/occurrence were argument-type OpSpecs here, but the
    # channel-unification moved them to the option channel (Optional[int]) — no
    # backend accepts an expression for them, and the arguments placement silently
    # dropped literals. They are now tracked by the option-surface matrix
    # (_KNOWN_UNTESTED_OPTION_PARAMS → dispositioned in the option task), not the
    # argument-types matrix. See option_disposition.py O-migrate rows.
    # -- Newly-wired regex + split ops --
    OpSpec(
        function_key=FK_STR.REGEXP_MATCH_ALL,
        op_name="regexp_match_substring_all",
        build=lambda col, arg: col.str.regexp_match_substring_all(arg),
        raw_arg=r"\d+",
        arg_col_name="pattern",
        param_name="pattern",
        data={
            "text": ["hello123", "world456", "test"],
            "pattern": [r"\d+", r"\d+", r"\d+"],
        },
    ),
    OpSpec(
        function_key=FK_STR.REGEXP_COUNT,
        op_name="regexp_count_substring",
        build=lambda col, arg: col.str.regexp_count_substring(arg),
        raw_arg=r"\d+",
        arg_col_name="pattern",
        param_name="pattern",
        data={
            "text": ["hello123", "world456", "test"],
            "pattern": [r"\d+", r"\d+", r"\d+"],
        },
    ),
    OpSpec(
        function_key=FK_STR.REGEXP_MATCH,
        op_name="regexp_match_substring",
        build=lambda col, arg: col.str.regexp_match_substring(arg),
        raw_arg=r"\d+",
        arg_col_name="pattern",
        param_name="pattern",
        data={
            "text": ["hello123", "world456", "test"],
            "pattern": [r"\d+", r"\d+", r"\d+"],
        },
    ),
    OpSpec(
        function_key=FK_STR.REGEXP_STRPOS,
        op_name="regexp_strpos",
        build=lambda col, arg: col.str.regexp_strpos(arg),
        raw_arg=r"\d+",
        arg_col_name="pattern",
        param_name="pattern",
        data={
            "text": ["hello123", "world456", "test"],
            "pattern": [r"\d+", r"\d+", r"\d+"],
        },
    ),
    OpSpec(
        function_key=FK_STR.REGEXP_SPLIT,
        op_name="regexp_string_split",
        build=lambda col, arg: col.str.regexp_string_split(arg),
        raw_arg=r"\d+",
        arg_col_name="pattern",
        param_name="pattern",
        data={
            "text": ["hello123world", "foo456bar", "baz"],
            "pattern": [r"\d+", r"\d+", r"\d+"],
        },
    ),
    OpSpec(
        function_key=FK_STR.SPLIT,
        op_name="string_split",
        build=lambda col, arg: col.str.string_split(arg),
        raw_arg=",",
        arg_col_name="sep",
        param_name="separator",
        data={
            "text": ["a,b,c", "d,e", "f"],
            "sep": [",", ",", ","],
        },
    ),
]


# Ops fully unsupported on narwhals (raise BackendCapabilityError for all input types,
# not just col/complex). xfail_if_limited only marks col/complex, so we handle these
# manually to avoid unexplained failures on raw/lit inputs.
_NARWHALS_FULLY_UNSUPPORTED: set[tuple] = {
    # repeat: narwhals has no str.repeat(); raises BackendCapabilityError unconditionally
    (FK_STR.REPEAT, "count"),
    # regex ops: narwhals has no extract_all, count_matches, or regex find
    (FK_STR.REGEXP_MATCH_ALL, "pattern"),
    (FK_STR.REGEXP_COUNT, "pattern"),
    (FK_STR.REGEXP_STRPOS, "pattern"),
    # string extension ops with no narwhals support
    ("to_time", "x"),
    ("encode", "x"),
    ("decode", "x"),
    ("json_path_match", "x"),
    ("extract_groups", "x"),
}

# Ops fully unsupported on ibis (raise BackendCapabilityError for all input types).
_IBIS_FULLY_UNSUPPORTED: set[tuple] = {
    # regex ops: ibis has no re_extract_all, re_count, or re_find
    (FK_STR.REGEXP_MATCH_ALL, "pattern"),
    (FK_STR.REGEXP_COUNT, "pattern"),
    (FK_STR.REGEXP_STRPOS, "pattern"),
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
