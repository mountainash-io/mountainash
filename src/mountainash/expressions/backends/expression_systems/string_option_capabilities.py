"""Import-safe string option capability declarations."""

from __future__ import annotations

from mountainash.core.capabilities import (
    CapabilityFact,
    CapabilityLevel,
    CapabilityRegistry,
    WILDCARD_PARAM,
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
        "regexp_replace": FK_STR.REGEXP_REPLACE,
        "regexp_string_split": FK_STR.REGEXP_SPLIT,
    },
    "dotall": {
        "regexp_match_substring": FK_STR.REGEXP_MATCH,
        "regexp_match_substring_all": FK_STR.REGEXP_MATCH_ALL,
        "regexp_strpos": FK_STR.REGEXP_STRPOS,
        "regexp_count_substring": FK_STR.REGEXP_COUNT,
        "regexp_replace": FK_STR.REGEXP_REPLACE,
        "regexp_string_split": FK_STR.REGEXP_SPLIT,
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
            message = (
                _REGEXP_OPERATION_UNAVAILABLE
                if op_unavailable
                else _POSITIONAL_IGNORED
            )
            # Two facts per declared positional param: the value-scoped fact for
            # the representative value the disposition matrix samples, and a
            # value-agnostic (option_value=None) fact so EVERY unsupported
            # integer is gated, not just the representative. The registry's
            # (op, param, backend, dialect, None) fallback resolves the wildcard
            # for any value; the builder drops omitted (None) positional options
            # so the wildcard never gates the omission path.
            for option_value in (_POSITIONAL_VALUE, None):
                facts.append(
                    CapabilityFact(
                        operation_key=operation_key,
                        param=param,
                        option_value=option_value,
                        level=CapabilityLevel.UNSUPPORTED,
                        backend=backend,
                        dialect=dialect,
                        message=message,
                        since=_SINCE,
                        # The value-agnostic companion is probe-exempt: the
                        # representative value-scoped fact carries the native
                        # self-healing probe (via the registered option probes),
                        # so this fact exists only to gate non-representative
                        # integers and must not demand its own OpSpec.
                        probe_exempt=(
                            None
                            if option_value is not None
                            else "value-agnostic companion to the "
                            "representative-value positional fact; the "
                            "value-scoped disposition probe drives the "
                            "native-path check"
                        ),
                    )
                )
    return tuple(facts)


_CHAR_SET_KEYS = {
    "lower": FK_STR.LOWER, "upper": FK_STR.UPPER, "swapcase": FK_STR.SWAPCASE,
    "capitalize": FK_STR.CAPITALIZE, "title": FK_STR.TITLE, "initcap": FK_STR.INITCAP,
}
_CHAR_SET_VALUES = ("UTF8", "ASCII_ONLY")
_BROKEN_STRING_OPS_BY_BACKEND: dict[CONST_BACKEND, frozenset[str]] = {
    CONST_BACKEND.IBIS: frozenset({"swapcase", "title", "initcap"}),
    CONST_BACKEND.NARWHALS: frozenset({"capitalize", "swapcase", "center"}),
}
_PADDING_VALUES = ("RIGHT", "LEFT")
_PADDING_OP_BROKEN = (
    "center is a no-op on this backend, so padding cannot be honored"
)


def _padding_facts(
    backend: CONST_BACKEND, dialect: str | None
) -> tuple[CapabilityFact, ...]:
    facts = []
    op_broken = _op_broken(backend, "center")
    for value in _PADDING_VALUES:
        if op_broken:
            level, message = CapabilityLevel.UNSUPPORTED, _PADDING_OP_BROKEN
        elif value == "RIGHT":
            level = CapabilityLevel.EXPR_CAPABLE
            message = (
                "RIGHT is the builder default, so the explicit option is "
                "observably equivalent to omission and cannot discriminate"
            )
        else:
            level, message = CapabilityLevel.UNSUPPORTED, (
                "The native backend does not implement LEFT padding semantics "
                "for center"
            )
        if dialect is None and level is CapabilityLevel.EXPR_CAPABLE:
            continue
        facts.append(CapabilityFact(
            operation_key=FK_STR.CENTER, param="padding", option_value=value,
            level=level, backend=backend, dialect=dialect, message=message,
            since=_SINCE,
            probe_exempt=(
                message
                if level is CapabilityLevel.EXPR_CAPABLE
                else None
            ),
        ))
    return tuple(facts)


_CHAR_SET_DEFAULT_EQUIVALENT = (
    "The builder default emits UTF8, so the explicit option is "
    "observably equivalent to omission and cannot discriminate"
)
_CHAR_SET_ASCII_UNSUPPORTED = (
    "The native backend does not implement ASCII_ONLY char_set semantics for "
    "this Substrait case operation"
)
_CHAR_SET_OP_BROKEN = (
    "The underlying case operation is unimplemented/incorrect on this backend "
    "(no-op or missing method), so char_set cannot be honored"
)


def _op_broken(backend: CONST_BACKEND, op: str) -> bool:
    return op in _BROKEN_STRING_OPS_BY_BACKEND.get(backend, frozenset())


def _char_set_facts(
    backend: CONST_BACKEND, dialect: str | None
) -> tuple[CapabilityFact, ...]:
    facts = []
    for op, operation_key in _CHAR_SET_KEYS.items():
        op_broken = _op_broken(backend, op)
        for index, value in enumerate(_CHAR_SET_VALUES):
            is_default = index == 0
            if op_broken:
                level, message, exempt = (
                    CapabilityLevel.UNSUPPORTED, _CHAR_SET_OP_BROKEN, None)
            elif is_default:
                level = CapabilityLevel.EXPR_CAPABLE
                message = _CHAR_SET_DEFAULT_EQUIVALENT
                exempt = _CHAR_SET_DEFAULT_EQUIVALENT
            else:
                level, message, exempt = (
                    CapabilityLevel.UNSUPPORTED, _CHAR_SET_ASCII_UNSUPPORTED, None)
            # EXPR_CAPABLE with dialect=None is illegal; only dialect-scoped
            # refinements carry probed-exempt facts. Family-default calls with
            # dialect=None skip EXPR_CAPABLE rows — the dialect-scoped facts
            # from _dialect_facts cover those for every known dialect.
            if dialect is None and level is CapabilityLevel.EXPR_CAPABLE:
                continue
            facts.append(CapabilityFact(
                operation_key=operation_key, param="char_set", option_value=value,
                level=level, backend=backend, dialect=dialect, message=message,
                since=_SINCE, probe_exempt=exempt,
            ))
    return tuple(facts)


_NEGATIVE_START_VALUES = ("WRAP_FROM_END", "LEFT_OF_BEGINNING", "ERROR")
_NEGATIVE_START_DEFAULT_EQUIVALENT = (
    "The builder default emits WRAP_FROM_END, so the explicit option is "
    "observably equivalent to omission and cannot discriminate"
)
_NEGATIVE_START_UNSUPPORTED = (
    "The native backend does not implement non-default negative_start semantics "
    "for substring"
)


def _negative_start_facts(
    backend: CONST_BACKEND, dialect: str | None
) -> tuple[CapabilityFact, ...]:
    facts = []
    for value in _NEGATIVE_START_VALUES:
        if value == "WRAP_FROM_END":
            level = CapabilityLevel.EXPR_CAPABLE
            message = _NEGATIVE_START_DEFAULT_EQUIVALENT
            exempt = _NEGATIVE_START_DEFAULT_EQUIVALENT
        else:
            level = CapabilityLevel.UNSUPPORTED
            message = _NEGATIVE_START_UNSUPPORTED
            exempt = None
        if dialect is None and level is CapabilityLevel.EXPR_CAPABLE:
            continue
        facts.append(CapabilityFact(
            operation_key=FK_STR.SUBSTRING, param="negative_start",
            option_value=value,
            level=level, backend=backend, dialect=dialect, message=message,
            since=_SINCE, probe_exempt=exempt,
        ))
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
        + _char_set_facts(backend, dialect)
        + _padding_facts(backend, dialect)
        + _negative_start_facts(backend, dialect)
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
) + _positional_facts(CONST_BACKEND.IBIS, None) + _char_set_facts(CONST_BACKEND.IBIS, None) + _padding_facts(CONST_BACKEND.IBIS, None) + _negative_start_facts(CONST_BACKEND.IBIS, None)
_NARWHALS_FACTS = tuple(
    fact
    for dialect in ("narwhals-polars", "narwhals-pandas")
    for fact in _dialect_facts(CONST_BACKEND.NARWHALS, dialect)
)


_OP_LEVEL_FKEYS = {**_CHAR_SET_KEYS, "center": FK_STR.CENTER}
_OP_LEVEL_UNSUPPORTED = (
    "This string operation has no correct native implementation on this backend at the "
    "pinned floor; it is gated to fail loudly rather than return wrong data"
)


def _op_level_facts(backend: CONST_BACKEND) -> tuple[CapabilityFact, ...]:
    return tuple(
        CapabilityFact(
            operation_key=_OP_LEVEL_FKEYS[op], param=WILDCARD_PARAM,
            level=CapabilityLevel.UNSUPPORTED, backend=backend, dialect=None,
            message=_OP_LEVEL_UNSUPPORTED, since=_SINCE,
            probe_exempt=(
                "whole-op gate; verified by the dedicated op-level probe suite "
                "(test_op_level_gate_probes.py), which cannot be keyed on an OpSpec param"
            ),
        )
        for op in sorted(_BROKEN_STRING_OPS_BY_BACKEND.get(backend, frozenset()))
    )


CapabilityRegistry.register_backend(CONST_BACKEND.POLARS, _POLARS_FACTS)
CapabilityRegistry.register_backend(
    CONST_BACKEND.IBIS,
    _IBIS_FAMILY_DEFAULTS + _IBIS_DUCKDB_FACTS + _op_level_facts(CONST_BACKEND.IBIS),
)
CapabilityRegistry.register_backend(
    CONST_BACKEND.NARWHALS,
    _NARWHALS_FACTS + _op_level_facts(CONST_BACKEND.NARWHALS),
)
