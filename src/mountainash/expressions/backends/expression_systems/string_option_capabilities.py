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
_REGEXP_FLAG_DEFAULT_EQUIVALENT = (
    "The builder default emits this regexp flag value, so the explicit option "
    "is observably equivalent to omission and cannot discriminate"
)
_REGEXP_FLAG_UNSUPPORTED = (
    "The native backend does not implement this regexp flag's non-default "
    "Substrait semantics"
)
_REGEXP_OPERATION_UNAVAILABLE = (
    "The underlying regexp operation is unavailable on this dialect, so its "
    "option value cannot be honored"
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
_REGEXP_FLAG_KEYS = {
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
_REGEXP_UNSUPPORTED_OPS = frozenset(
    {
        "regexp_match_substring_all",
        "regexp_strpos",
        "regexp_count_substring",
    }
)
_POSITIONAL_IGNORED = (
    "The native backend does not honor the regexp position/occurrence/group "
    "option; it is silently ignored rather than applied"
)
# Regexp positional int options (arguments-vs-options.md unified these to the
# option channel in the string PR). Keyed by param -> {op: FKEY}.
_POSITIONAL_KEYS = {
    "position": {
        "regexp_match_substring": FK_STR.REGEXP_MATCH,
        "regexp_match_substring_all": FK_STR.REGEXP_MATCH_ALL,
        "regexp_strpos": FK_STR.REGEXP_STRPOS,
        "regexp_count_substring": FK_STR.REGEXP_COUNT,
        "regexp_replace": FK_STR.REGEXP_REPLACE,
    },
    "occurrence": {
        "regexp_match_substring": FK_STR.REGEXP_MATCH,
        "regexp_strpos": FK_STR.REGEXP_STRPOS,
        "regexp_replace": FK_STR.REGEXP_REPLACE,
    },
    "group": {
        "regexp_match_substring": FK_STR.REGEXP_MATCH,
        "regexp_match_substring_all": FK_STR.REGEXP_MATCH_ALL,
    },
}
# Representative int value the disposition matrix gates (value-scoped, mirroring
# how enum options enumerate their finite domain).
_POSITIONAL_VALUE = "2"
# (op, param, backend-family) triples a native backend genuinely honors — these
# get NO gating fact (EXPR_CAPABLE by absence). Everything else is declared
# UNSUPPORTED. Probe-determined empirically: only regexp_match_substring group
# (polars + ibis) and regexp_replace occurrence (polars) discriminate.
_POSITIONAL_HONORED = {
    ("regexp_match_substring", "group", CONST_BACKEND.POLARS),
    ("regexp_match_substring", "group", CONST_BACKEND.IBIS),
    ("regexp_replace", "occurrence", CONST_BACKEND.POLARS),
}


def _positional_facts(
    backend: CONST_BACKEND, dialect: str | None
) -> tuple[CapabilityFact, ...]:
    facts = []
    for param, operations in _POSITIONAL_KEYS.items():
        for op, operation_key in operations.items():
            if (op, param, backend) in _POSITIONAL_HONORED:
                continue
            op_unavailable = (
                op in _REGEXP_UNSUPPORTED_OPS
                and backend is not CONST_BACKEND.POLARS
            )
            facts.append(
                CapabilityFact(
                    operation_key=operation_key,
                    param=param,
                    option_value=_POSITIONAL_VALUE,
                    level=CapabilityLevel.UNSUPPORTED,
                    backend=backend,
                    dialect=dialect,
                    message=(
                        _REGEXP_OPERATION_UNAVAILABLE
                        if op_unavailable
                        else _POSITIONAL_IGNORED
                    ),
                    since=_SINCE,
                )
            )
    return tuple(facts)


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
    regexp_defaults = tuple(
        CapabilityFact(
            operation_key=operation_key,
            param=param,
            option_value=values[0],
            level=(
                CapabilityLevel.UNSUPPORTED
                if op in _REGEXP_UNSUPPORTED_OPS
                and backend is not CONST_BACKEND.POLARS
                else CapabilityLevel.EXPR_CAPABLE
            ),
            backend=backend,
            dialect=dialect,
            message=(
                _REGEXP_OPERATION_UNAVAILABLE
                if op in _REGEXP_UNSUPPORTED_OPS
                and backend is not CONST_BACKEND.POLARS
                else _REGEXP_FLAG_DEFAULT_EQUIVALENT
            ),
            since=_SINCE,
            probe_exempt=(
                None
                if op in _REGEXP_UNSUPPORTED_OPS
                and backend is not CONST_BACKEND.POLARS
                else _REGEXP_FLAG_DEFAULT_EQUIVALENT
            ),
        )
        for param, operations in _REGEXP_FLAG_KEYS.items()
        for op, operation_key in operations.items()
        for values in (_REGEXP_FLAG_VALUES[param],)
    )
    regexp_enabled = tuple(
        CapabilityFact(
            operation_key=operation_key,
            param=param,
            option_value=values[1],
            level=CapabilityLevel.UNSUPPORTED,
            backend=backend,
            dialect=dialect,
            message=_REGEXP_FLAG_UNSUPPORTED,
            since=_SINCE,
        )
        for param, operations in _REGEXP_FLAG_KEYS.items()
        for operation_key in operations.values()
        for values in (_REGEXP_FLAG_VALUES[param],)
    )
    positional = _positional_facts(backend, dialect)
    return (
        case_sensitive
        + case_insensitive
        + regexp_defaults
        + regexp_enabled
        + positional
    )


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
) + tuple(
    CapabilityFact(
        operation_key=operation_key,
        param=param,
        option_value=values[1],
        level=CapabilityLevel.UNSUPPORTED,
        backend=CONST_BACKEND.IBIS,
        dialect=None,
        message=_REGEXP_FLAG_UNSUPPORTED,
        since=_SINCE,
    )
    for param, operations in _REGEXP_FLAG_KEYS.items()
    for operation_key in operations.values()
    for values in (_REGEXP_FLAG_VALUES[param],)
) + tuple(
    CapabilityFact(
        operation_key=operation_key,
        param=param,
        option_value=values[0],
        level=CapabilityLevel.UNSUPPORTED,
        backend=CONST_BACKEND.IBIS,
        dialect=None,
        message=_REGEXP_OPERATION_UNAVAILABLE,
        since=_SINCE,
    )
    for param, operations in _REGEXP_FLAG_KEYS.items()
    for op, operation_key in operations.items()
    for values in (_REGEXP_FLAG_VALUES[param],)
    if op in _REGEXP_UNSUPPORTED_OPS
) + _positional_facts(CONST_BACKEND.IBIS, None)
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
