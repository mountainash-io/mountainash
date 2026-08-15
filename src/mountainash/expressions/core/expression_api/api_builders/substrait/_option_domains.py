"""Packaged Substrait option domains used for runtime validation."""

from __future__ import annotations

from typing import Any

from mountainash.core.errors import InvalidOptionValueError
from mountainash.expressions.core.datetime_components import (
    BooleanComponent,
    DatetimeComponent,
)


_OVERFLOW = frozenset({"SILENT", "SATURATE", "ERROR"})
_ROUNDING = frozenset(
    {"TIE_TO_EVEN", "TIE_AWAY_FROM_ZERO", "TRUNCATE", "CEILING", "FLOOR"}
)
_NAN_ERROR = frozenset({"NAN", "ERROR"})
_CHAR_SET = frozenset({"UTF8", "ASCII_ONLY"})
_PADDING = frozenset({"RIGHT", "LEFT"})
_NEGATIVE_START = frozenset({"WRAP_FROM_END", "LEFT_OF_BEGINNING", "ERROR"})
_CASE_SENSITIVITY = frozenset(
    {"CASE_SENSITIVE", "CASE_INSENSITIVE", "CASE_INSENSITIVE_ASCII"}
)
_MULTILINE = frozenset({"MULTILINE_DISABLED", "MULTILINE_ENABLED"})
_DOTALL = frozenset({"DOTALL_DISABLED", "DOTALL_ENABLED"})

# Generated from Substrait v0.98.0, commit
# b322d463804660674e43c9d2b659730375e3026e. The pinned-fixture guard owns
# drift detection; runtime code must never read from tests/.
OPTION_DOMAINS: dict[tuple[str, str], frozenset[str]] = {
    ("abs", "overflow"): _OVERFLOW,
    ("acos", "on_domain_error"): _NAN_ERROR,
    ("acos", "rounding"): _ROUNDING,
    ("acosh", "on_domain_error"): _NAN_ERROR,
    ("acosh", "rounding"): _ROUNDING,
    ("add", "overflow"): _OVERFLOW,
    ("add", "rounding"): _ROUNDING,
    ("asin", "on_domain_error"): _NAN_ERROR,
    ("asin", "rounding"): _ROUNDING,
    ("asinh", "rounding"): _ROUNDING,
    ("atan", "rounding"): _ROUNDING,
    ("atan2", "on_domain_error"): _NAN_ERROR,
    ("atan2", "rounding"): _ROUNDING,
    ("atanh", "on_domain_error"): _NAN_ERROR,
    ("atanh", "rounding"): _ROUNDING,
    ("cos", "rounding"): _ROUNDING,
    ("cosh", "rounding"): _ROUNDING,
    ("contains", "case_sensitivity"): _CASE_SENSITIVITY,
    ("count_substring", "case_sensitivity"): _CASE_SENSITIVITY,
    ("degrees", "rounding"): _ROUNDING,
    ("divide", "on_division_by_zero"): frozenset(
        {"IEEE", "LIMIT", "NULL", "ERROR"}
    ),
    ("divide", "on_domain_error"): frozenset({"NAN", "NULL", "ERROR"}),
    ("divide", "overflow"): _OVERFLOW,
    ("divide", "rounding"): _ROUNDING,
    ("exp", "rounding"): _ROUNDING,
    ("ends_with", "case_sensitivity"): _CASE_SENSITIVITY,
    ("factorial", "overflow"): _OVERFLOW,
    ("like", "case_sensitivity"): _CASE_SENSITIVITY,
    ("modulus", "division_type"): frozenset({"TRUNCATE", "FLOOR"}),
    ("modulus", "on_domain_error"): frozenset({"NULL", "ERROR"}),
    ("modulus", "overflow"): _OVERFLOW,
    ("multiply", "overflow"): _OVERFLOW,
    ("multiply", "rounding"): _ROUNDING,
    ("negate", "overflow"): _OVERFLOW,
    ("power", "overflow"): _OVERFLOW,
    ("radians", "rounding"): _ROUNDING,
    ("replace", "case_sensitivity"): _CASE_SENSITIVITY,
    ("regexp_count_substring", "case_sensitivity"): _CASE_SENSITIVITY,
    ("regexp_count_substring", "dotall"): _DOTALL,
    ("regexp_count_substring", "multiline"): _MULTILINE,
    ("regexp_match_substring", "case_sensitivity"): _CASE_SENSITIVITY,
    ("regexp_match_substring", "dotall"): _DOTALL,
    ("regexp_match_substring", "multiline"): _MULTILINE,
    ("regexp_match_substring_all", "case_sensitivity"): _CASE_SENSITIVITY,
    ("regexp_match_substring_all", "dotall"): _DOTALL,
    ("regexp_match_substring_all", "multiline"): _MULTILINE,
    ("regexp_replace", "case_sensitivity"): _CASE_SENSITIVITY,
    ("regexp_replace", "dotall"): _DOTALL,
    ("regexp_replace", "multiline"): _MULTILINE,
    ("regexp_string_split", "case_sensitivity"): _CASE_SENSITIVITY,
    ("regexp_string_split", "dotall"): _DOTALL,
    ("regexp_string_split", "multiline"): _MULTILINE,
    ("regexp_strpos", "case_sensitivity"): _CASE_SENSITIVITY,
    ("regexp_strpos", "dotall"): _DOTALL,
    ("regexp_strpos", "multiline"): _MULTILINE,
    ("sin", "rounding"): _ROUNDING,
    ("sinh", "rounding"): _ROUNDING,
    ("sqrt", "on_domain_error"): _NAN_ERROR,
    ("sqrt", "rounding"): _ROUNDING,
    ("starts_with", "case_sensitivity"): _CASE_SENSITIVITY,
    ("strpos", "case_sensitivity"): _CASE_SENSITIVITY,
    ("subtract", "overflow"): _OVERFLOW,
    ("subtract", "rounding"): _ROUNDING,
    ("tan", "rounding"): _ROUNDING,
    ("tanh", "rounding"): _ROUNDING,
    ("center", "padding"): _PADDING,
    ("concat", "null_handling"): frozenset({"IGNORE_NULLS", "ACCEPT_NULLS"}),
    ("substring", "negative_start"): _NEGATIVE_START,
    ("capitalize", "char_set"): _CHAR_SET,
    ("initcap", "char_set"): _CHAR_SET,
    ("lower", "char_set"): _CHAR_SET,
    ("swapcase", "char_set"): _CHAR_SET,
    ("title", "char_set"): _CHAR_SET,
    ("upper", "char_set"): _CHAR_SET,
    # Datetime extraction closed domains. The enums mirror the upstream
    # overload union (23 datetime + 2 boolean members) — no new members.
    ("extract", "component"): frozenset(c.value for c in DatetimeComponent),
    ("extract", "indexing"): frozenset({"ONE", "ZERO"}),
    ("extract_boolean", "component"): frozenset(c.value for c in BooleanComponent),
}


def validate_option(
    op_name: str, option_name: str, value: Any  # noqa: ANN401
) -> str:
    """Return an option as a string, rejecting illegal known-domain values."""
    legal = OPTION_DOMAINS.get((op_name, option_name))
    normalized = str(value)
    if legal is not None and normalized not in legal:
        raise InvalidOptionValueError(
            f"invalid {option_name}={value!r} for {op_name}; legal: {sorted(legal)}"
        )
    return normalized
