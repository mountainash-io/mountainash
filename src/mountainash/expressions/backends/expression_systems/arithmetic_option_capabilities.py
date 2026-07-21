"""Import-safe arithmetic option capability declarations."""

from __future__ import annotations

from mountainash.core.capabilities import (
    CapabilityFact,
    CapabilityLevel,
    CapabilityRegistry,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_ARITHMETIC as FK_ARITH,
)


_SINCE = "2026-07-21"
_UNSUPPORTED_MESSAGE = (
    "The native backend does not implement the requested Substrait integer "
    "overflow mode"
)
_DEFAULT_EQUIVALENT = (
    "The explicit option selects the native backend's existing behavior, so "
    "it is observably equivalent to omission and cannot discriminate"
)
_POWER_UNSUPPORTED_MESSAGE = (
    "The native backend does not implement the requested Substrait i64 power "
    "overflow mode"
)
_POWER_DEFAULT_EQUIVALENT = (
    "Explicit SILENT selects the native backend's i64 power wrapping behavior, "
    "so it is observably equivalent to omission and cannot discriminate"
)
_POWER_WORKAROUND = (
    "Pre-check the i64 base and exponent and handle out-of-range powers before "
    "calling power()"
)
_SEMANTIC_UNSUPPORTED = (
    "The native backend does not implement the requested Substrait arithmetic "
    "option semantics"
)
_SEMANTIC_DEFAULT_EQUIVALENT = (
    "The native omission path already has the requested arithmetic semantics, "
    "so the explicit option cannot discriminate"
)


def _fact(
    operation_key: object,
    backend: CONST_BACKEND,
    dialect: str | None,
    value: str,
    level: CapabilityLevel,
    *,
    probe_exempt: str | None = None,
) -> CapabilityFact:
    is_power = operation_key is FK_ARITH.POWER
    return CapabilityFact(
        operation_key=operation_key,
        param="overflow",
        option_value=value,
        level=level,
        backend=backend,
        dialect=dialect,
        message=(
            _POWER_DEFAULT_EQUIVALENT
            if is_power and level is CapabilityLevel.EXPR_CAPABLE
            else _POWER_UNSUPPORTED_MESSAGE
            if is_power
            else _DEFAULT_EQUIVALENT
            if level is CapabilityLevel.EXPR_CAPABLE
            else _UNSUPPORTED_MESSAGE
        ),
        workaround=(
            _POWER_WORKAROUND
            if is_power
            else "Cast operands to a wider integer dtype before the operation"
        ),
        since=_SINCE,
        probe_exempt=probe_exempt,
    )


_OVERFLOW_KEYS = {
    "abs": FK_ARITH.ABS,
    "add": FK_ARITH.ADD,
    "subtract": FK_ARITH.SUBTRACT,
    "multiply": FK_ARITH.MULTIPLY,
    "divide": FK_ARITH.DIVIDE,
    "modulus": FK_ARITH.MODULO,
    "negate": FK_ARITH.NEGATE,
    "power": FK_ARITH.POWER,
}
_WRAPPING_KEYS = {
    operation_key
    for operation, operation_key in _OVERFLOW_KEYS.items()
    if operation != "divide"
}


def _dialect_facts(
    backend: CONST_BACKEND,
    dialect: str | None,
) -> tuple[CapabilityFact, ...]:
    return tuple(
        _fact(
            operation_key,
            backend,
            dialect,
            value,
            (
                CapabilityLevel.EXPR_CAPABLE
                if operation_key in _WRAPPING_KEYS and value == "SILENT"
                else CapabilityLevel.UNSUPPORTED
            ),
            probe_exempt=(
                _DEFAULT_EQUIVALENT
                if operation_key in _WRAPPING_KEYS and value == "SILENT"
                else None
            ),
        )
        for operation_key in _OVERFLOW_KEYS.values()
        for value in ("ERROR", "SATURATE", "SILENT")
    )


POLARS_ARITHMETIC_OPTION_CAPABILITIES = _dialect_facts(
    CONST_BACKEND.POLARS, "polars"
)

IBIS_ARITHMETIC_OPTION_CAPABILITIES = tuple(
    _fact(
        operation_key,
        CONST_BACKEND.IBIS,
        None,
        value,
        CapabilityLevel.UNSUPPORTED,
    )
    for operation_key in _OVERFLOW_KEYS.values()
    for value in ("ERROR", "SATURATE", "SILENT")
)

NARWHALS_ARITHMETIC_OPTION_CAPABILITIES = tuple(
    fact
    for dialect in ("narwhals-polars", "narwhals-pandas")
    for fact in _dialect_facts(CONST_BACKEND.NARWHALS, dialect)
)


_SEMANTIC_KEYS = {
    ("acos", "on_domain_error"): FK_ARITH.ACOS,
    ("acosh", "on_domain_error"): FK_ARITH.ACOSH,
    ("asin", "on_domain_error"): FK_ARITH.ASIN,
    ("atan2", "on_domain_error"): FK_ARITH.ATAN2,
    ("atanh", "on_domain_error"): FK_ARITH.ATANH,
    ("sqrt", "on_domain_error"): FK_ARITH.SQRT,
    ("divide", "on_domain_error"): FK_ARITH.DIVIDE,
    ("divide", "on_division_by_zero"): FK_ARITH.DIVIDE,
    ("modulus", "division_type"): FK_ARITH.MODULO,
    ("modulus", "on_domain_error"): FK_ARITH.MODULO,
}
_SEMANTIC_DOMAINS = {
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
_FIXTURE_IDENTITIES = {
    "polars": (CONST_BACKEND.POLARS, "polars"),
    "ibis": (CONST_BACKEND.IBIS, None),
    "narwhals-polars": (CONST_BACKEND.NARWHALS, "narwhals-polars"),
    "narwhals-pandas": (CONST_BACKEND.NARWHALS, "narwhals-pandas"),
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
}


def _semantic_facts(
    backend: CONST_BACKEND, dialect: str | None, fixture: str
) -> tuple[CapabilityFact, ...]:
    return tuple(
        CapabilityFact(
            operation_key=_SEMANTIC_KEYS[(operation, param)],
            param=param,
            option_value=value,
            level=(
                CapabilityLevel.EXPR_CAPABLE
                if (operation, param, fixture, value) in _SEMANTIC_EXEMPT
                else CapabilityLevel.UNSUPPORTED
            ),
            backend=backend,
            dialect=dialect,
            message=(
                _SEMANTIC_DEFAULT_EQUIVALENT
                if (operation, param, fixture, value) in _SEMANTIC_EXEMPT
                else _SEMANTIC_UNSUPPORTED
            ),
            workaround=(
                "Pre-handle invalid arithmetic inputs and select the requested "
                "result before evaluating the operation"
            ),
            since=_SINCE,
            probe_exempt=(
                _SEMANTIC_DEFAULT_EQUIVALENT
                if (operation, param, fixture, value) in _SEMANTIC_EXEMPT
                else None
            ),
        )
        for operation, param in _SEMANTIC_KEYS
        for value in _SEMANTIC_DOMAINS[(operation, param)]
    )


_SEMANTIC_FACTS = {
    fixture: _semantic_facts(backend, dialect, fixture)
    for fixture, (backend, dialect) in _FIXTURE_IDENTITIES.items()
}


_ROUNDING_KEYS = {
    FK_ARITH.ACOS,
    FK_ARITH.ACOSH,
    FK_ARITH.ADD,
    FK_ARITH.ASIN,
    FK_ARITH.ASINH,
    FK_ARITH.ATAN,
    FK_ARITH.ATAN2,
    FK_ARITH.ATANH,
    FK_ARITH.COS,
    FK_ARITH.COSH,
    FK_ARITH.DEGREES,
    FK_ARITH.DIVIDE,
    FK_ARITH.EXP,
    FK_ARITH.MULTIPLY,
    FK_ARITH.RADIANS,
    FK_ARITH.SIN,
    FK_ARITH.SINH,
    FK_ARITH.SQRT,
    FK_ARITH.SUBTRACT,
    FK_ARITH.TAN,
    FK_ARITH.TANH,
}
_ROUNDING_VALUES = (
    "CEILING",
    "FLOOR",
    "TIE_AWAY_FROM_ZERO",
    "TIE_TO_EVEN",
    "TRUNCATE",
)
_ROUNDING_UNSUPPORTED = (
    "The native backend does not implement the requested Substrait IEEE "
    "rounding mode"
)


def _rounding_facts(
    backend: CONST_BACKEND, dialect: str | None
) -> tuple[CapabilityFact, ...]:
    return tuple(
        CapabilityFact(
            operation_key=operation_key,
            param="rounding",
            option_value=value,
            level=CapabilityLevel.UNSUPPORTED,
            backend=backend,
            dialect=dialect,
            message=_ROUNDING_UNSUPPORTED,
            workaround=(
                "Evaluate with native rounding, then apply an explicit "
                "application-level numeric policy"
            ),
            since=_SINCE,
        )
        for operation_key in _ROUNDING_KEYS
        for value in _ROUNDING_VALUES
    )


_ROUNDING_FACTS = {
    fixture: _rounding_facts(backend, dialect)
    for fixture, (backend, dialect) in _FIXTURE_IDENTITIES.items()
}


CapabilityRegistry.register_backend(
    CONST_BACKEND.POLARS,
    POLARS_ARITHMETIC_OPTION_CAPABILITIES
    + _SEMANTIC_FACTS["polars"]
    + _ROUNDING_FACTS["polars"],
)
CapabilityRegistry.register_backend(
    CONST_BACKEND.IBIS,
    IBIS_ARITHMETIC_OPTION_CAPABILITIES
    + _SEMANTIC_FACTS["ibis"]
    + _ROUNDING_FACTS["ibis"],
)
CapabilityRegistry.register_backend(
    CONST_BACKEND.NARWHALS,
    NARWHALS_ARITHMETIC_OPTION_CAPABILITIES
    + _SEMANTIC_FACTS["narwhals-polars"]
    + _SEMANTIC_FACTS["narwhals-pandas"]
    + _ROUNDING_FACTS["narwhals-polars"]
    + _ROUNDING_FACTS["narwhals-pandas"],
)
