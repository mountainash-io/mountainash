"""Import-safe string option capability declarations.

Migrated from mountainash.expressions.backends.expression_systems.string_option_capabilities (2026-08 capability-architecture PR).
"""

from __future__ import annotations

from mountainash.core.capabilities import (
    Boundary,
    CapabilityFact,
    CapabilityLevel,
    Enforcement,
    WILDCARD_PARAM,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
    FKEY_MOUNTAINASH_SCALAR_STRING as FK_MA_STR,
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
# regexp_string_split (backlog item 85, NW-STR-20) is different from the
# 3 ops above: it works on ibis-duckdb and ibis-polars(literal) via
# re_split, and is unsupported ONLY on Narwhals (no regex-split primitive
# at all), not uniformly on every non-Polars backend.
_REGEXP_UNSUPPORTED_OPS_NARWHALS_ONLY = frozenset({"regexp_string_split"})


def _regexp_op_unsupported_for_backend(op: str, backend: CONST_BACKEND) -> bool:
    """True when op's whole capability is unavailable on this backend
    family, uniformly regardless of flag value -- drives regexp flag
    default/enabled fact generation in _dialect_facts()/_positional_facts()/
    _IBIS_FAMILY_DEFAULTS."""
    if op in _REGEXP_UNSUPPORTED_OPS_NARWHALS_ONLY:
        return backend is CONST_BACKEND.NARWHALS
    return op in _REGEXP_UNSUPPORTED_OPS and backend is not CONST_BACKEND.POLARS


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
            op_unavailable = _regexp_op_unsupported_for_backend(op, backend)
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
BROKEN_STRING_OPS_BY_BACKEND: dict[CONST_BACKEND, frozenset[str]] = {
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
    return op in BROKEN_STRING_OPS_BY_BACKEND.get(backend, frozenset())


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
                if _regexp_op_unsupported_for_backend(op, backend)
                else CapabilityLevel.EXPR_CAPABLE
            ),
            backend=backend,
            dialect=dialect,
            message=(
                _REGEXP_OPERATION_UNAVAILABLE
                if _regexp_op_unsupported_for_backend(op, backend)
                else _REGEXP_FLAG_DEFAULT_EQUIVALENT
            ),
            since=_SINCE,
            probe_exempt=(
                None
                if _regexp_op_unsupported_for_backend(op, backend)
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


# ---------------------------------------------------------------------------
# CASE_INSENSITIVE_ASCII (backlog item 75, 2026-08-12) — a distinct probe
# wave from the 2026-07-23 baseline above, so its facts get their own
# CapabilityDeclaration/ProbeEvidence per "one backend's facts, from one
# source, one domain, one probe wave" (declarations.py). Semantics verified
# directly against each engine (Kelvin Sign / Turkish I-with-dot
# discriminator — see the design spec), not inferred from CASE_INSENSITIVE's
# existing facts.
# ---------------------------------------------------------------------------
_SINCE_ASCII_FOLD = "2026-08-12"
_CASE_INSENSITIVE_ASCII_UNSUPPORTED = (
    "The native backend does not implement CASE_INSENSITIVE_ASCII semantics "
    "for this Substrait string operation (same disposition as "
    "CASE_INSENSITIVE — neither case-fold value is wired here)"
)
_CASE_INSENSITIVE_ASCII_WORKAROUND = (
    "Fold the input and search operand to ASCII lowercase explicitly before "
    "applying the case-sensitive operation"
)
_REGEXP_FLAG_ASCII_UNSUPPORTED = (
    "The native backend does not implement this regexp flag's "
    "CASE_INSENSITIVE_ASCII Substrait semantics"
)


def _case_insensitive_ascii_facts(
    backend: CONST_BACKEND, dialect: str | None
) -> tuple[CapabilityFact, ...]:
    """CASE_INSENSITIVE_ASCII facts for the 10 always-unsupported ops (4
    non-regex ops via _CASE_INSENSITIVE_UNSUPPORTED_KEYS + 6 regexp_* ops) —
    mirrors _dialect_facts's case_insensitive/regexp_enabled shape exactly,
    scoped to just the new value. contains/starts_with/ends_with need no
    fact here (real/EXPR_CAPABLE by absence) except on ibis-polars, which
    _IBIS_POLARS_FACTS below covers separately."""
    non_regex = tuple(
        CapabilityFact(
            operation_key=operation_key,
            param="case_sensitivity",
            option_value="CASE_INSENSITIVE_ASCII",
            level=CapabilityLevel.UNSUPPORTED,
            backend=backend,
            dialect=dialect,
            message=_CASE_INSENSITIVE_ASCII_UNSUPPORTED,
            workaround=_CASE_INSENSITIVE_ASCII_WORKAROUND,
            since=_SINCE_ASCII_FOLD,
        )
        for operation_key in _CASE_INSENSITIVE_UNSUPPORTED_KEYS
    )
    regexp = tuple(
        CapabilityFact(
            operation_key=operation_key,
            param="case_sensitivity",
            option_value="CASE_INSENSITIVE_ASCII",
            level=CapabilityLevel.UNSUPPORTED,
            backend=backend,
            dialect=dialect,
            message=_REGEXP_FLAG_ASCII_UNSUPPORTED,
            since=_SINCE_ASCII_FOLD,
        )
        for operation_key in _REGEXP_FLAG_KEYS["case_sensitivity"].values()
    )
    return non_regex + regexp


_POLARS_ASCII_FOLD_FACTS = _case_insensitive_ascii_facts(CONST_BACKEND.POLARS, "polars")
_IBIS_DUCKDB_ASCII_FOLD_FACTS = _case_insensitive_ascii_facts(CONST_BACKEND.IBIS, "ibis-duckdb")
_IBIS_FAMILY_ASCII_FOLD_FACTS = _case_insensitive_ascii_facts(CONST_BACKEND.IBIS, None)
_NARWHALS_ASCII_FOLD_FACTS = tuple(
    fact
    for dialect in ("narwhals-polars", "narwhals-pandas")
    for fact in _case_insensitive_ascii_facts(CONST_BACKEND.NARWHALS, dialect)
)

# Empirical dialect spike (2026-08-12): ibis-polars has no compilation rule
# for StringTranslate (OperationNotDefinedError raised at materialize time);
# ibis-duckdb and ibis-sqlite both compile it via native SQL translate().
# contains/starts_with/ends_with are therefore real everywhere in the Ibis
# family EXCEPT ibis-polars, which needs its own dialect-scoped UNSUPPORTED
# fact overriding the (absent-by-default) family disposition — mirrors the
# ibis-sqlite/strptime precedent's "no family default, dialect-scoped
# refinement only" shape (capabilities/datetime/strptime.py).
_IBIS_POLARS_ASCII_FOLD_UNSUPPORTED = (
    "ibis-polars has no compilation rule for StringTranslate "
    "(OperationNotDefinedError); the ASCII-only fold CASE_INSENSITIVE_ASCII "
    "needs for contains/starts_with/ends_with is unavailable on this "
    "dialect, unlike ibis-duckdb/ibis-sqlite which both support .translate()"
)
_ASCII_FOLD_KEYS = {
    op: fkey
    for op, fkey in _CASE_SENSITIVITY_KEYS.items()
    if fkey not in _CASE_INSENSITIVE_UNSUPPORTED_KEYS
}
_IBIS_POLARS_FACTS = tuple(
    CapabilityFact(
        operation_key=operation_key,
        param="case_sensitivity",
        option_value="CASE_INSENSITIVE_ASCII",
        level=CapabilityLevel.UNSUPPORTED,
        backend=CONST_BACKEND.IBIS,
        dialect="ibis-polars",
        message=_IBIS_POLARS_ASCII_FOLD_UNSUPPORTED,
        since=_SINCE_ASCII_FOLD,
    )
    for operation_key in _ASCII_FOLD_KEYS.values()
)


# ---------------------------------------------------------------------------
# ibis-polars dynamic-pattern gap (backlog item 81, 2026-08-12) — a distinct
# probe wave from both the 2026-07-23 baseline and the 2026-08-12 ASCII-fold
# wave above, so it gets its own CapabilityDeclaration/ProbeEvidence. Ibis's
# `.re_replace()` (replace's/regexp_replace's fallback path) and `.replace()`
# (count_substring's dynamic-branch path) both compile on ibis-polars down to
# Polars' native str.replace()/str.replace_all(), which does not support a
# dynamic (column-valued) pattern argument at all -- a confirmed upstream
# Polars limitation already tracked for the raw polars backend as
# PL-STR-01/PL-STR-02 (POLARS_EXPR_CAPABILITIES in capabilities/polars.py,
# which registers the identical LITERAL_ONLY disposition for the raw
# backend). Empirically confirmed (2026-08-12, ibis 12.0.0) that ONLY these
# three (op, param) pairs are affected -- trim/ltrim/rtrim's `characters`
# param already has its own family-level (dialect=None) LITERAL_ONLY gate
# for the whole Ibis backend (capabilities/ibis.py), confirmed via direct
# probe to already raise a clean BackendCapabilityError pre-fix on
# ibis-polars, so it needed no new fact here. Literal patterns are
# unaffected on every dialect -- LITERAL_ONLY unwraps a LiteralNode to its
# raw Python
# value before replace()/count_substring()/regexp_replace() run, which their
# existing literal-branch code (or, for regexp_replace, Ibis's own
# raw-string coercion) already handles unchanged.
# ---------------------------------------------------------------------------
_SINCE_DYNAMIC_PATTERN = "2026-08-12"
_IBIS_POLARS_DYNAMIC_PATTERN_UNSUPPORTED = (
    "ibis-polars compiles this to Polars' native str.replace()/"
    "str.replace_all(), which does not support a dynamic (column-valued) "
    "pattern argument (tracked upstream as PL-STR-01/PL-STR-02 for the raw "
    "polars backend; see backlog item 81)"
)
_IBIS_POLARS_DYNAMIC_PATTERN_WORKAROUND = (
    "Use a literal string pattern instead of a column reference"
)
# Mapped by native call shape (confirmed via direct probe of the error
# message/expression repr): count_substring's dynamic branch uses Ibis's
# non-regex `.replace()` (same class as PL-STR-01's "str.replace" case);
# replace's and regexp_replace's fallback branches both use `.re_replace()`
# (regex) — same class as PL-STR-02 ("str.replace_all/str.replace with
# regex"), which its own upstream-issues.yaml note already calls "same class
# as PL-STR-01".
_IBIS_POLARS_DYNAMIC_PATTERN_UPSTREAM_REF = {
    (FK_STR.REPLACE, "substring"): "PL-STR-02",
    (FK_STR.COUNT_SUBSTRING, "substring"): "PL-STR-01",
    (FK_STR.REGEXP_REPLACE, "pattern"): "PL-STR-02",
}
_IBIS_POLARS_DYNAMIC_PATTERN_FACTS: tuple[CapabilityFact, ...] = tuple(
    CapabilityFact(
        operation_key=operation_key,
        param=param,
        level=CapabilityLevel.LITERAL_ONLY,
        backend=CONST_BACKEND.IBIS,
        dialect="ibis-polars",
        message=_IBIS_POLARS_DYNAMIC_PATTERN_UNSUPPORTED,
        workaround=_IBIS_POLARS_DYNAMIC_PATTERN_WORKAROUND,
        since=_SINCE_DYNAMIC_PATTERN,
        upstream_ref=_IBIS_POLARS_DYNAMIC_PATTERN_UPSTREAM_REF[(operation_key, param)],
    )
    for operation_key, param in _IBIS_POLARS_DYNAMIC_PATTERN_UPSTREAM_REF
)
# ibis-sqlite / CASE_INSENSITIVE (backlog item 79, 2026-08-12) — ibis-sqlite's
# native LOWER()/UPPER() are ASCII-only (no ICU extension loaded in
# mountainash's Ibis SQLite connection); CASE_INSENSITIVE's Unicode-aware
# lowercasing contract (Kelvin Sign U+212A -> 'k') is unavailable on this one
# dialect; verified on polars/ibis-duckdb/narwhals-polars/narwhals-pandas —
# ibis-polars is untested by the Kelvin Sign discriminator suite (excluded
# there for its own, unrelated StringTranslate reason) and not claimed here.
# CASE_INSENSITIVE was EXPR_CAPABLE-by-absence on ibis-sqlite for
# contains/starts_with/ends_with (the same shape CASE_INSENSITIVE_ASCII had
# on ibis-polars before item 75's _IBIS_POLARS_FACTS) — mirrors that exact
# dialect-scoped-refinement shape, gated instead of silently returning an
# ASCII-only result under a Unicode-aware-lowercasing-claiming option value.
# CASE_INSENSITIVE_ASCII is UNAFFECTED: ibis-sqlite's .translate()-based
# ASCII fold genuinely delivers that exact (narrower) contract.
# ---------------------------------------------------------------------------
_SINCE_IBIS_SQLITE_CASE_INSENSITIVE = "2026-08-12"
_IBIS_SQLITE_CASE_INSENSITIVE_UNSUPPORTED = (
    "ibis-sqlite's native LOWER()/UPPER() are ASCII-only (no ICU extension "
    "loaded); CASE_INSENSITIVE's Unicode-aware-lowercasing contract (e.g. "
    "Kelvin Sign U+212A -> 'k') is unavailable on this dialect alone in the "
    "Ibis family — gated unconditionally for every ibis-sqlite connection "
    "and every input (including purely-ASCII input, which SQLite's native "
    "LOWER() handles correctly, and any caller-supplied connection with a "
    "custom Unicode-aware LOWER()/UPPER() override loaded onto it) because "
    "the capability fact is keyed on (backend, dialect), a static identity, "
    "with no visibility into a specific connection's actual loaded "
    "extensions or a specific call's runtime string content"
)
_IBIS_SQLITE_CASE_INSENSITIVE_WORKAROUND = (
    "Use CASE_INSENSITIVE_ASCII instead if ASCII-only folding is "
    "sufficient (genuinely honored on ibis-sqlite via native translate()); "
    "otherwise Unicode-normalize both operands in Python (e.g. str.lower()) "
    "and reissue the comparison as CASE_SENSITIVE (NOT CASE_INSENSITIVE — "
    "this dialect-scoped gate is unconditional and still rejects "
    "CASE_INSENSITIVE even after preprocessing), or run this expression "
    "against a different Ibis dialect (ibis-duckdb) instead of ibis-sqlite"
)
_IBIS_SQLITE_CASE_INSENSITIVE_FACTS = tuple(
    CapabilityFact(
        operation_key=operation_key,
        param="case_sensitivity",
        option_value="CASE_INSENSITIVE",
        level=CapabilityLevel.UNSUPPORTED,
        backend=CONST_BACKEND.IBIS,
        dialect="ibis-sqlite",
        message=_IBIS_SQLITE_CASE_INSENSITIVE_UNSUPPORTED,
        workaround=_IBIS_SQLITE_CASE_INSENSITIVE_WORKAROUND,
        since=_SINCE_IBIS_SQLITE_CASE_INSENSITIVE,
    )
    for operation_key in _ASCII_FOLD_KEYS.values()  # contains/starts_with/ends_with
)

# ---------------------------------------------------------------------------
# ibis-polars raw native-error leaks on like/regexp_match_substring/
# string_split (backlog item 83, 2026-08-12) — adjacent-but-distinct gaps
# found during item 81's audit, deliberately out of that item's
# re_replace/.replace()-scoped fix. Three genuinely different shapes:
#
# - `like`: ibis-polars has NO compilation rule for StringSQLLike at all
#   (OperationNotDefinedError), for ANY pattern — literal included. Not a
#   literal-vs-dynamic split like item 81's ops; a whole-op gate (mirrors
#   strptime.py's dialect-scoped WILDCARD_PARAM UNSUPPORTED precedent for
#   ibis-sqlite). ibis-duckdb/ibis-sqlite both translate LIKE to native SQL
#   correctly (empirically confirmed) — this is ibis-polars-specific, not
#   family-wide, so it does NOT belong in _op_level_facts()'s backend-wide
#   (dialect=None) BROKEN_STRING_OPS_BY_BACKEND map.
# - `regexp_match_substring`/`string_split`: a DYNAMIC (column-valued)
#   pattern/separator raises Ibis's own `UnsupportedArgumentError: Polars
#   does not support columnar argument ...` — a literal works fine. Same
#   LITERAL_ONLY, dialect-scoped mechanism as item 81's
#   _IBIS_POLARS_DYNAMIC_PATTERN_FACTS (the gate pre-empts Ibis's own
#   .re_extract()/.split() call before it's reached; no MATERIALIZE_RESIDUE
#   catch needed).
#
# `regexp_strpos`/`regexp_count_substring` were re-confirmed (not fixed —
# already correct): both raise BackendCapabilityError unconditionally in
# Python (expsys_ib_scalar_string.py), before any Ibis call, with no
# reachable literal-vs-dynamic branch difference to gate underneath.
# `regexp_string_split` is a SEPARATE, more severe bug (silent no-op
# returning unsplit input, not a raise, on every Ibis dialect) — filed as
# backlog item 85, deliberately not touched here.
# ---------------------------------------------------------------------------
_SINCE_RAW_ERROR_LEAKS = "2026-08-12"
_IBIS_POLARS_LIKE_UNSUPPORTED = (
    "ibis-polars has no compilation rule for StringSQLLike "
    "(OperationNotDefinedError) for any pattern, literal or dynamic; "
    "ibis-duckdb/ibis-sqlite both translate LIKE to native SQL correctly"
)
_LIKE_OP_LEVEL_EXEMPTION = (
    "whole-op gate on a dialect-scoped WILDCARD_PARAM fact; cannot be keyed "
    "on an OpSpec param — verified by the dedicated cross-backend gate test "
    "in test_pattern.py (TestLikeIbisPolarsGate) and the native-bypass "
    "self-healing probe in test_op_level_gate_probes.py "
    "(test_like_ibis_polars_native_still_broken)"
)
_IBIS_POLARS_LIKE_FACTS = (
    CapabilityFact(
        operation_key=FK_STR.LIKE,
        param=WILDCARD_PARAM,
        level=CapabilityLevel.UNSUPPORTED,
        backend=CONST_BACKEND.IBIS,
        dialect="ibis-polars",
        message=_IBIS_POLARS_LIKE_UNSUPPORTED,
        workaround="Use ibis-duckdb/ibis-sqlite or a polars/narwhals backend for LIKE patterns",
        since=_SINCE_RAW_ERROR_LEAKS,
        upstream_ref="IB-STR-06",
        probe_exempt=_LIKE_OP_LEVEL_EXEMPTION,
    ),
)
_IBIS_POLARS_REGEXP_SPLIT_UNSUPPORTED = (
    "ibis-polars compiles this to Polars' native columnar-argument path, "
    "which raises Ibis's own UnsupportedArgumentError for a dynamic "
    "(column-valued) argument; a literal value works fine"
)
_IBIS_POLARS_REGEXP_SPLIT_WORKAROUND = (
    "Use a literal string pattern/separator instead of a column reference"
)
_IBIS_POLARS_REGEXP_SPLIT_UPSTREAM_REF = {
    (FK_STR.REGEXP_MATCH, "pattern"): "IB-STR-09",
    (FK_STR.SPLIT, "separator"): "IB-STR-10",
}
_IBIS_POLARS_REGEXP_SPLIT_FACTS = tuple(
    CapabilityFact(
        operation_key=operation_key,
        param=param,
        level=CapabilityLevel.LITERAL_ONLY,
        backend=CONST_BACKEND.IBIS,
        dialect="ibis-polars",
        message=_IBIS_POLARS_REGEXP_SPLIT_UNSUPPORTED,
        workaround=_IBIS_POLARS_REGEXP_SPLIT_WORKAROUND,
        since=_SINCE_RAW_ERROR_LEAKS,
        upstream_ref=_IBIS_POLARS_REGEXP_SPLIT_UPSTREAM_REF[(operation_key, param)],
    )
    for operation_key, param in _IBIS_POLARS_REGEXP_SPLIT_UPSTREAM_REF
)
_IBIS_POLARS_RAW_ERROR_LEAKS_FACTS = _IBIS_POLARS_LIKE_FACTS + _IBIS_POLARS_REGEXP_SPLIT_FACTS



OP_LEVEL_FKEYS = {**_CHAR_SET_KEYS, "center": FK_STR.CENTER}
_OP_LEVEL_UNSUPPORTED = (
    "This string operation has no correct native implementation on this backend at the "
    "pinned floor; it is gated to fail loudly rather than return wrong data"
)


def _op_level_facts(backend: CONST_BACKEND) -> tuple[CapabilityFact, ...]:
    return tuple(
        CapabilityFact(
            operation_key=OP_LEVEL_FKEYS[op], param=WILDCARD_PARAM,
            level=CapabilityLevel.UNSUPPORTED, backend=backend, dialect=None,
            message=_OP_LEVEL_UNSUPPORTED, since=_SINCE,
            probe_exempt=(
                "whole-op gate; verified by the dedicated op-level probe suite "
                "(test_op_level_gate_probes.py), which cannot be keyed on an OpSpec param"
            ),
        )
        for op in sorted(BROKEN_STRING_OPS_BY_BACKEND.get(backend, frozenset()))
    )


from mountainash.core.capabilities.declarations import (  # noqa: E402
    CapabilityDeclaration,
    Domain,
    FactSource,
    ProbeEvidence,
)

_EVIDENCE = ProbeEvidence(
    probe_date=_SINCE,          # 2026-07-23
    library_versions=(),        # not recorded in the original docstring
    fixtures=(
        "polars", "ibis-duckdb", "narwhals-polars", "narwhals-pandas",
    ),
)

_TEMPORAL_NULL_FACTS = tuple(
    CapabilityFact(
        operation_key=FK_MA_STR.TO_TIME,
        param="failure_behavior",
        option_value="null",
        level=CapabilityLevel.UNSUPPORTED,
        backend=backend,
        message="null-on-invalid custom time parsing is supported only by Polars",
        since="2026-08-21",
    )
    for backend in (CONST_BACKEND.IBIS, CONST_BACKEND.NARWHALS)
)

_EVIDENCE_ASCII_FOLD = ProbeEvidence(
    probe_date=_SINCE_ASCII_FOLD,
    library_versions=(("ibis", "12.0.0"), ("narwhals", "2.24.0")),
    fixtures=(
        "polars", "ibis-duckdb", "ibis-polars", "ibis-sqlite",
        "narwhals-polars", "narwhals-pandas",
    ),
)

_EVIDENCE_DYNAMIC_PATTERN = ProbeEvidence(
    probe_date=_SINCE_DYNAMIC_PATTERN,
    library_versions=(("ibis", "12.0.0"), ("polars", "1.43.2")),
    fixtures=("ibis-polars",),
)
_EVIDENCE_IBIS_SQLITE_CASE_INSENSITIVE = ProbeEvidence(
    probe_date=_SINCE_IBIS_SQLITE_CASE_INSENSITIVE,
    library_versions=(("ibis", "12.0.0"),),
    fixtures=("ibis-sqlite", "ibis-duckdb"),
)
_EVIDENCE_RAW_ERROR_LEAKS = ProbeEvidence(
    probe_date=_SINCE_RAW_ERROR_LEAKS,
    library_versions=(("ibis", "12.0.0"), ("polars", "1.43.2")),
    fixtures=("ibis-polars", "ibis-duckdb", "ibis-sqlite"),
)
# ---------------------------------------------------------------------------
# regexp_string_split silent no-op on every backend + narwhals plain
# string_split silent no-op (backlog items 85/86, 2026-08-13). Distinct
# constant names from the item-83 `_IBIS_POLARS_REGEXP_SPLIT_*` block above
# deliberately -- that block describes REGEXP_MATCH/SPLIT dynamic-pattern
# gates, NOT FK_STR.REGEXP_SPLIT (this function key) -- reusing the name
# would compound an existing naming collision, not resolve it.
# ---------------------------------------------------------------------------
_SINCE_SPLIT_FAMILY = "2026-08-13"
_IBIS_SQLITE_REGEXP_STRING_SPLIT_UNSUPPORTED = (
    "ibis-sqlite has no compilation rule for RegexSplit "
    "(OperationNotDefinedError) for any pattern, literal or dynamic; "
    "ibis-duckdb translates it to native SQL correctly and ibis-polars "
    "supports a literal pattern"
)
_IBIS_SQLITE_REGEXP_STRING_SPLIT_EXEMPTION = (
    "whole-op gate on a dialect-scoped WILDCARD_PARAM fact; cannot be keyed "
    "on an OpSpec param -- verified by a dedicated cross-backend gate test "
    "plus the native-bypass self-healing probe in "
    "test_op_level_gate_probes.py, mirroring item 83's "
    "TestLikeIbisPolarsGate / test_like_ibis_polars_native_still_broken"
)
_IBIS_SQLITE_REGEXP_STRING_SPLIT_FACTS = (
    CapabilityFact(
        operation_key=FK_STR.REGEXP_SPLIT,
        param=WILDCARD_PARAM,
        level=CapabilityLevel.UNSUPPORTED,
        backend=CONST_BACKEND.IBIS,
        dialect="ibis-sqlite",
        message=_IBIS_SQLITE_REGEXP_STRING_SPLIT_UNSUPPORTED,
        workaround="Use ibis-duckdb, ibis-polars with a literal pattern, or "
            "a Polars backend for regex split",
        since=_SINCE_SPLIT_FAMILY,
        upstream_ref="IB-STR-12",
        probe_exempt=_IBIS_SQLITE_REGEXP_STRING_SPLIT_EXEMPTION,
    ),
)
_IBIS_POLARS_REGEXP_STRING_SPLIT_DYNAMIC_FACTS = (
    CapabilityFact(
        operation_key=FK_STR.REGEXP_SPLIT,
        param="pattern",
        level=CapabilityLevel.LITERAL_ONLY,
        backend=CONST_BACKEND.IBIS,
        dialect="ibis-polars",
        message="ibis-polars compiles regexp_string_split to Polars' "
            "native re_split, which raises Ibis's own IbisError for a "
            "dynamic (column-valued) pattern; a literal pattern works fine",
        workaround="Use a literal string pattern instead of a column reference",
        since=_SINCE_SPLIT_FAMILY,
        upstream_ref="IB-STR-13",
    ),
)
_NARWHALS_REGEXP_STRING_SPLIT_FACTS = (
    CapabilityFact(
        operation_key=FK_STR.REGEXP_SPLIT,
        param=WILDCARD_PARAM,
        level=CapabilityLevel.UNSUPPORTED,
        backend=CONST_BACKEND.NARWHALS,
        dialect=None,
        message="Narwhals has no regex-split primitive at the pinned "
            "version -- ExprStringNamespace.split(by) is literal-substring-"
            "only, no other method performs regex splitting on any "
            "narwhals dialect",
        workaround="Use a Polars or ibis-duckdb/ibis-polars(literal) "
            "backend for regex split",
        since=_SINCE_SPLIT_FAMILY,
        upstream_ref="NW-STR-20",
        probe_exempt="whole-op gate on a family-wide WILDCARD_PARAM fact; "
            "no OpSpec exists since narwhals genuinely has no candidate "
            "method to probe -- verified by a dedicated native-API-surface "
            "self-healing probe (not a re-invocation of the mountainash "
            "wrapper's own hard-coded raise)",
    ),
)
_NARWHALS_STRING_SPLIT_DYNAMIC_FACTS = (
    CapabilityFact(
        operation_key=FK_STR.SPLIT, param="separator",
        level=CapabilityLevel.LITERAL_ONLY,
        backend=CONST_BACKEND.NARWHALS,
        dialect=None,
        message="Narwhals str.split() requires a literal separator "
            "string, not an Expr -- raises TypeError even for an "
            "Expr-wrapped literal",
        workaround="Use a literal separator string",
        since=_SINCE_SPLIT_FAMILY,
        upstream_ref="NW-STR-21",
    ),
)
_NARWHALS_PANDAS_STRING_SPLIT_UNSUPPORTED = (
    "narwhals-pandas' str.split() requires a pyarrow-backed pandas series "
    "(raises TypeError: 'This operation requires a pyarrow-backed series') "
    "against the plain numpy-backed storage most pandas DataFrames use; a "
    "pyarrow-backed pandas DataFrame (e.g. via .convert_dtypes(dtype_backend="
    "'pyarrow')) works correctly, as does narwhals-polars for any storage"
)
_NARWHALS_PANDAS_STRING_SPLIT_FACTS = (
    CapabilityFact(
        operation_key=FK_STR.SPLIT,
        param=WILDCARD_PARAM,
        level=CapabilityLevel.UNSUPPORTED,
        backend=CONST_BACKEND.NARWHALS,
        dialect="narwhals-pandas",
        message=_NARWHALS_PANDAS_STRING_SPLIT_UNSUPPORTED,
        workaround="Use a pyarrow-backed pandas DataFrame, narwhals-polars, "
            "Polars, or Ibis for string_split",
        since=_SINCE_SPLIT_FAMILY,
        upstream_ref="NW-STR-22",
        enforcement=Enforcement.MATERIALIZE_RESIDUE,
        boundary=Boundary.MATERIALIZE,
        native_errors=(TypeError,),
        probe_exempt="whole-op materialize-time storage residue "
            "(narwhals-pandas pyarrow-backed-series requirement) -- "
            "storage-dependent, not an intrinsic dialect-wide gap: a "
            "pyarrow-backed pandas DataFrame genuinely works, so this "
            "cannot be a build-time GATE (mirrors NW-LIST-01's identical "
            "pyarrow-storage-dependent CONTAINS/T_CONTAINS pattern)",
    ),
)
_EVIDENCE_SPLIT_FAMILY = ProbeEvidence(
    probe_date=_SINCE_SPLIT_FAMILY,
    library_versions=(("ibis", "12.0.0"), ("polars", "1.43.2"), ("narwhals", "2.24.0")),
    fixtures=("ibis-duckdb", "ibis-polars", "ibis-sqlite", "narwhals-polars", "narwhals-pandas"),
)


DECLARATIONS = (
    CapabilityDeclaration(
        backend=CONST_BACKEND.POLARS, domain=Domain.STRING,
        source=FactSource.SUBSTRAIT, facts=_POLARS_FACTS,
        evidence=_EVIDENCE,
    ),
    CapabilityDeclaration(
        backend=CONST_BACKEND.IBIS, domain=Domain.STRING,
        source=FactSource.SUBSTRAIT,
        facts=tuple(_IBIS_FAMILY_DEFAULTS) + tuple(_IBIS_DUCKDB_FACTS)
        + _op_level_facts(CONST_BACKEND.IBIS),
        evidence=_EVIDENCE,
    ),
    CapabilityDeclaration(
        backend=CONST_BACKEND.NARWHALS, domain=Domain.STRING,
        source=FactSource.SUBSTRAIT,
        facts=tuple(_NARWHALS_FACTS) + _op_level_facts(CONST_BACKEND.NARWHALS),
        evidence=_EVIDENCE,
    ),
    CapabilityDeclaration(
        backend=CONST_BACKEND.POLARS, domain=Domain.STRING,
        source=FactSource.SUBSTRAIT, facts=_POLARS_ASCII_FOLD_FACTS,
        evidence=_EVIDENCE_ASCII_FOLD,
    ),
    CapabilityDeclaration(
        backend=CONST_BACKEND.IBIS, domain=Domain.STRING,
        source=FactSource.SUBSTRAIT,
        facts=_IBIS_FAMILY_ASCII_FOLD_FACTS + _IBIS_DUCKDB_ASCII_FOLD_FACTS
        + _IBIS_POLARS_FACTS,
        evidence=_EVIDENCE_ASCII_FOLD,
    ),
    CapabilityDeclaration(
        backend=CONST_BACKEND.NARWHALS, domain=Domain.STRING,
        source=FactSource.SUBSTRAIT, facts=_NARWHALS_ASCII_FOLD_FACTS,
        evidence=_EVIDENCE_ASCII_FOLD,
    ),
    CapabilityDeclaration(
        backend=CONST_BACKEND.IBIS, domain=Domain.STRING,
        source=FactSource.SUBSTRAIT,
        facts=_IBIS_POLARS_DYNAMIC_PATTERN_FACTS,
        evidence=_EVIDENCE_DYNAMIC_PATTERN,
    ),
    CapabilityDeclaration(
        backend=CONST_BACKEND.IBIS, domain=Domain.STRING,
        source=FactSource.SUBSTRAIT,
        facts=_IBIS_SQLITE_CASE_INSENSITIVE_FACTS,
        evidence=_EVIDENCE_IBIS_SQLITE_CASE_INSENSITIVE,
    ),
    CapabilityDeclaration(
        backend=CONST_BACKEND.IBIS, domain=Domain.STRING,
        source=FactSource.SUBSTRAIT,
        facts=_IBIS_POLARS_RAW_ERROR_LEAKS_FACTS,
        evidence=_EVIDENCE_RAW_ERROR_LEAKS,
    ),
    CapabilityDeclaration(
        backend=CONST_BACKEND.IBIS, domain=Domain.STRING,
        source=FactSource.SUBSTRAIT,
        facts=_IBIS_SQLITE_REGEXP_STRING_SPLIT_FACTS
        + _IBIS_POLARS_REGEXP_STRING_SPLIT_DYNAMIC_FACTS,
        evidence=_EVIDENCE_SPLIT_FAMILY,
    ),
    CapabilityDeclaration(
        backend=CONST_BACKEND.IBIS,
        domain=Domain.STRING,
        source=FactSource.MOUNTAINASH,
        facts=(_TEMPORAL_NULL_FACTS[0],),
        evidence=_EVIDENCE,
    ),
    CapabilityDeclaration(
        backend=CONST_BACKEND.NARWHALS,
        domain=Domain.STRING,
        source=FactSource.MOUNTAINASH,
        facts=(_TEMPORAL_NULL_FACTS[1],),
        evidence=_EVIDENCE,
    ),
    CapabilityDeclaration(
        backend=CONST_BACKEND.NARWHALS, domain=Domain.STRING,
        source=FactSource.SUBSTRAIT,
        facts=_NARWHALS_REGEXP_STRING_SPLIT_FACTS
        + _NARWHALS_STRING_SPLIT_DYNAMIC_FACTS
        + _NARWHALS_PANDAS_STRING_SPLIT_FACTS,
        evidence=_EVIDENCE_SPLIT_FAMILY,
    ),
)
