"""Packaged Substrait option domains used for runtime validation."""

from __future__ import annotations

from typing import Any

from mountainash.core.errors import InvalidOptionValueError


_OVERFLOW = frozenset({"SILENT", "SATURATE", "ERROR"})
_ROUNDING = frozenset(
    {"TIE_TO_EVEN", "TIE_AWAY_FROM_ZERO", "TRUNCATE", "CEILING", "FLOOR"}
)
_NAN_ERROR = frozenset({"NAN", "ERROR"})

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
    ("degrees", "rounding"): _ROUNDING,
    ("divide", "on_division_by_zero"): frozenset(
        {"IEEE", "LIMIT", "NULL", "ERROR"}
    ),
    ("divide", "on_domain_error"): frozenset({"NAN", "NULL", "ERROR"}),
    ("divide", "overflow"): _OVERFLOW,
    ("divide", "rounding"): _ROUNDING,
    ("exp", "rounding"): _ROUNDING,
    ("factorial", "overflow"): _OVERFLOW,
    ("modulus", "division_type"): frozenset({"TRUNCATE", "FLOOR"}),
    ("modulus", "on_domain_error"): frozenset({"NULL", "ERROR"}),
    ("modulus", "overflow"): _OVERFLOW,
    ("multiply", "overflow"): _OVERFLOW,
    ("multiply", "rounding"): _ROUNDING,
    ("negate", "overflow"): _OVERFLOW,
    ("power", "overflow"): _OVERFLOW,
    ("radians", "rounding"): _ROUNDING,
    ("sin", "rounding"): _ROUNDING,
    ("sinh", "rounding"): _ROUNDING,
    ("sqrt", "on_domain_error"): _NAN_ERROR,
    ("sqrt", "rounding"): _ROUNDING,
    ("subtract", "overflow"): _OVERFLOW,
    ("subtract", "rounding"): _ROUNDING,
    ("tan", "rounding"): _ROUNDING,
    ("tanh", "rounding"): _ROUNDING,
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
