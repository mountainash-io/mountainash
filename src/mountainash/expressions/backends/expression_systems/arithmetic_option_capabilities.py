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
    "The native backend accepts the overflow option but does not implement "
    "the requested Substrait abs overflow semantics"
)
_DEFAULT_EQUIVALENT = (
    "The explicit option selects the native backend's existing behavior, so "
    "it is observably equivalent to omission and cannot discriminate"
)


def _fact(
    backend: CONST_BACKEND,
    dialect: str | None,
    value: str,
    level: CapabilityLevel,
    *,
    probe_exempt: str | None = None,
) -> CapabilityFact:
    return CapabilityFact(
        operation_key=FK_ARITH.ABS,
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
        workaround="Use a wider integer dtype before abs()",
        since=_SINCE,
        probe_exempt=probe_exempt,
    )


POLARS_ARITHMETIC_OPTION_CAPABILITIES = (
    *(
        _fact(CONST_BACKEND.POLARS, "polars", value, CapabilityLevel.UNSUPPORTED)
        for value in ("ERROR", "SATURATE")
    ),
    _fact(
        CONST_BACKEND.POLARS,
        "polars",
        "SILENT",
        CapabilityLevel.EXPR_CAPABLE,
        probe_exempt=_DEFAULT_EQUIVALENT,
    ),
)

IBIS_ARITHMETIC_OPTION_CAPABILITIES = tuple(
    _fact(CONST_BACKEND.IBIS, None, value, CapabilityLevel.UNSUPPORTED)
    for value in ("ERROR", "SATURATE", "SILENT")
)

NARWHALS_ARITHMETIC_OPTION_CAPABILITIES = tuple(
    _fact(
        CONST_BACKEND.NARWHALS,
        dialect,
        value,
        (
            CapabilityLevel.EXPR_CAPABLE
            if value == "SILENT"
            else CapabilityLevel.UNSUPPORTED
        ),
        probe_exempt=_DEFAULT_EQUIVALENT if value == "SILENT" else None,
    )
    for dialect in ("narwhals-polars", "narwhals-pandas")
    for value in ("ERROR", "SATURATE", "SILENT")
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
