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


def _fact(
    operation_key: object,
    backend: CONST_BACKEND,
    dialect: str | None,
    value: str,
    level: CapabilityLevel,
    *,
    probe_exempt: str | None = None,
) -> CapabilityFact:
    return CapabilityFact(
        operation_key=operation_key,
        param="overflow",
        option_value=value,
        level=level,
        backend=backend,
        dialect=dialect,
        message=(
            _DEFAULT_EQUIVALENT
            if level is CapabilityLevel.EXPR_CAPABLE
            else _UNSUPPORTED_MESSAGE
        ),
        workaround="Cast operands to a wider integer dtype before the operation",
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


CapabilityRegistry.register_backend(
    CONST_BACKEND.POLARS, POLARS_ARITHMETIC_OPTION_CAPABILITIES
)
CapabilityRegistry.register_backend(
    CONST_BACKEND.IBIS, IBIS_ARITHMETIC_OPTION_CAPABILITIES
)
CapabilityRegistry.register_backend(
    CONST_BACKEND.NARWHALS, NARWHALS_ARITHMETIC_OPTION_CAPABILITIES
)
