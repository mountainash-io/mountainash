"""Import-safe string option capability declarations."""

from __future__ import annotations

from mountainash.core.capabilities import (
    CapabilityFact,
    CapabilityLevel,
    CapabilityRegistry,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)


_SINCE = "2026-07-23"
_CASE_SENSITIVE_EQUIVALENT = (
    "The builder default emits CASE_SENSITIVE, so the explicit option is "
    "observably equivalent to omission and cannot discriminate"
)
_CASE_INSENSITIVE_UNSUPPORTED = (
    "The native backend does not implement CASE_INSENSITIVE semantics for "
    "this Substrait string operation"
)
_CASE_INSENSITIVE_WORKAROUND = (
    "Lowercase the input and search operand explicitly before applying the "
    "case-sensitive operation"
)
_CASE_SENSITIVITY_KEYS = {
    "contains": FK_STR.CONTAINS,
    "count_substring": FK_STR.COUNT_SUBSTRING,
    "ends_with": FK_STR.ENDS_WITH,
    "like": FK_STR.LIKE,
    "replace": FK_STR.REPLACE,
    "starts_with": FK_STR.STARTS_WITH,
    "strpos": FK_STR.STRPOS,
}
_CASE_INSENSITIVE_UNSUPPORTED_KEYS = {
    _CASE_SENSITIVITY_KEYS[op]
    for op in ("count_substring", "like", "replace", "strpos")
}


def _dialect_facts(
    backend: CONST_BACKEND, dialect: str
) -> tuple[CapabilityFact, ...]:
    case_sensitive = tuple(
        CapabilityFact(
            operation_key=operation_key,
            param="case_sensitivity",
            option_value="CASE_SENSITIVE",
            level=CapabilityLevel.EXPR_CAPABLE,
            backend=backend,
            dialect=dialect,
            message=_CASE_SENSITIVE_EQUIVALENT,
            since=_SINCE,
            probe_exempt=_CASE_SENSITIVE_EQUIVALENT,
        )
        for operation_key in _CASE_SENSITIVITY_KEYS.values()
    )
    case_insensitive = tuple(
        CapabilityFact(
            operation_key=operation_key,
            param="case_sensitivity",
            option_value="CASE_INSENSITIVE",
            level=CapabilityLevel.UNSUPPORTED,
            backend=backend,
            dialect=dialect,
            message=_CASE_INSENSITIVE_UNSUPPORTED,
            workaround=_CASE_INSENSITIVE_WORKAROUND,
            since=_SINCE,
        )
        for operation_key in _CASE_INSENSITIVE_UNSUPPORTED_KEYS
    )
    return case_sensitive + case_insensitive


_POLARS_FACTS = _dialect_facts(CONST_BACKEND.POLARS, "polars")
_IBIS_DUCKDB_FACTS = _dialect_facts(CONST_BACKEND.IBIS, "ibis-duckdb")
_IBIS_FAMILY_DEFAULTS = tuple(
    CapabilityFact(
        operation_key=operation_key,
        param="case_sensitivity",
        option_value="CASE_INSENSITIVE",
        level=CapabilityLevel.UNSUPPORTED,
        backend=CONST_BACKEND.IBIS,
        dialect=None,
        message=_CASE_INSENSITIVE_UNSUPPORTED,
        workaround=_CASE_INSENSITIVE_WORKAROUND,
        since=_SINCE,
    )
    for operation_key in _CASE_INSENSITIVE_UNSUPPORTED_KEYS
)
_NARWHALS_FACTS = tuple(
    fact
    for dialect in ("narwhals-polars", "narwhals-pandas")
    for fact in _dialect_facts(CONST_BACKEND.NARWHALS, dialect)
)


CapabilityRegistry.register_backend(CONST_BACKEND.POLARS, _POLARS_FACTS)
CapabilityRegistry.register_backend(
    CONST_BACKEND.IBIS,
    _IBIS_FAMILY_DEFAULTS + _IBIS_DUCKDB_FACTS,
)
CapabilityRegistry.register_backend(CONST_BACKEND.NARWHALS, _NARWHALS_FACTS)
