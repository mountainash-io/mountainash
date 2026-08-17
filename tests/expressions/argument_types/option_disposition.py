"""Per-fixture disposition matrix for Substrait literal option values.

This is test infrastructure shared by the arithmetic, string, and datetime
option slices.  Expectations come from protocol introspection and named gaps;
the disposition and probe registries are outputs checked against that scope,
never inputs used to shrink it.

String option-surface classification (PR-B Task 1)
====================================================

This is the authoritative classification of every
``SubstraitScalarStringExpressionSystemProtocol`` entry in
``_KNOWN_UNTESTED_OPTION_PARAMS``. FKEY names were verified against
``function_keys/enums.py``; the channel is the current
``ScalarFunctionNode`` AST channel in ``api_bldr_scalar_string.py``.

| Operation | FKEY | Parameter | Class | Task / reason |
| --- | --- | --- | --- | --- |
| ``capitalize`` | ``CAPITALIZE`` | ``char_set`` | O-absent | Substrait option absent from builder signature and ``node.options``; wire (Task 4). |
| ``center`` | ``CENTER`` | ``padding`` | O-absent | Substrait option absent from builder signature and ``node.options``; wire (Task 4). |
| ``concat`` | ``CONCAT`` | ``null_handling`` | O-live | Emitted in ``node.options``; behaviour-test (backlog item 61). |
| ``contains`` | ``CONTAINS`` | ``case_sensitivity`` | O-live | Emitted in ``node.options``; behaviour-test (Task 3). |
| ``count_substring`` | ``COUNT_SUBSTRING`` | ``case_sensitivity`` | O-live | Emitted in ``node.options``; behaviour-test (Task 3). |
| ``ends_with`` | ``ENDS_WITH`` | ``case_sensitivity`` | O-live | Emitted in ``node.options``; behaviour-test (Task 3). |
| ``initcap`` | ``INITCAP`` | ``char_set`` | O-absent | Substrait option absent from builder signature and ``node.options``; wire (Task 4). |
| ``like`` | ``LIKE`` | ``case_sensitivity`` | O-live | Emitted in ``node.options``; behaviour-test (Task 3). |
| ``lower`` | ``LOWER`` | ``char_set`` | O-absent | Substrait option absent from builder signature and ``node.options``; wire (Task 4). |
| ``regexp_count_substring`` | ``REGEXP_COUNT`` | ``case_sensitivity`` | O-live | Emitted in ``node.options``; behaviour-test (Task 3). |
| ``regexp_count_substring`` | ``REGEXP_COUNT`` | ``dotall`` | O-live | Emitted in ``node.options``; behaviour-test (Task 3). |
| ``regexp_count_substring`` | ``REGEXP_COUNT`` | ``multiline`` | O-live | Emitted in ``node.options``; behaviour-test (Task 3). |
| ``regexp_count_substring`` | ``REGEXP_COUNT`` | ``position`` | O-live | Emitted in ``node.options``; behaviour-test (Task 3). |
| ``regexp_match_substring`` | ``REGEXP_MATCH`` | ``case_sensitivity`` | O-live | Emitted in ``node.options``; behaviour-test (Task 3). |
| ``regexp_match_substring`` | ``REGEXP_MATCH`` | ``dotall`` | O-live | Emitted in ``node.options``; behaviour-test (Task 3). |
| ``regexp_match_substring`` | ``REGEXP_MATCH`` | ``group`` | O-migrate | Currently argument-channel (phantom expr capability: a literal ``group`` is visited to an Expr and silently collapses to 0); migrate arguments→options, retyped ``Optional[int]`` (Task 2 unify), then disposition (Task 3). |
| ``regexp_match_substring`` | ``REGEXP_MATCH`` | ``multiline`` | O-live | Emitted in ``node.options``; behaviour-test (Task 3). |
| ``regexp_match_substring`` | ``REGEXP_MATCH`` | ``occurrence`` | O-migrate | Currently argument-channel (universally literal, honored by no backend); migrate arguments→options, retyped ``Optional[int]`` (Task 2 unify), then disposition (Task 3). |
| ``regexp_match_substring`` | ``REGEXP_MATCH`` | ``position`` | O-migrate | Currently argument-channel (universally literal, honored by no backend); migrate arguments→options, retyped ``Optional[int]`` (Task 2 unify), then disposition (Task 3). |
| ``regexp_match_substring_all`` | ``REGEXP_MATCH_ALL`` | ``case_sensitivity`` | O-live | Emitted in ``node.options``; behaviour-test (Task 3). |
| ``regexp_match_substring_all`` | ``REGEXP_MATCH_ALL`` | ``dotall`` | O-live | Emitted in ``node.options``; behaviour-test (Task 3). |
| ``regexp_match_substring_all`` | ``REGEXP_MATCH_ALL`` | ``group`` | O-live | Currently emitted in ``node.options``; behaviour-test (Task 3). |
| ``regexp_match_substring_all`` | ``REGEXP_MATCH_ALL`` | ``multiline`` | O-live | Emitted in ``node.options``; behaviour-test (Task 3). |
| ``regexp_match_substring_all`` | ``REGEXP_MATCH_ALL`` | ``position`` | O-live | Currently emitted in ``node.options``; behaviour-test (Task 3). |
| ``regexp_replace`` | ``REGEXP_REPLACE`` | ``case_sensitivity`` | O-live | Emitted in ``node.options``; behaviour-test (Task 3). |
| ``regexp_replace`` | ``REGEXP_REPLACE`` | ``dotall`` | O-absent | Substrait option absent from builder signature and ``node.options``; wire (Task 4). |
| ``regexp_replace`` | ``REGEXP_REPLACE`` | ``multiline`` | O-absent | Substrait option absent from builder signature and ``node.options``; wire (Task 4). |
| ``regexp_replace`` | ``REGEXP_REPLACE`` | ``occurrence`` | O-migrate | Currently argument-channel (universally literal; a genuine Expr raises at ``if occurrence == 0``); migrate arguments→options, retyped ``Optional[int]`` (Task 2 unify), then disposition (Task 3). |
| ``regexp_replace`` | ``REGEXP_REPLACE`` | ``position`` | O-migrate | Currently argument-channel (universally literal, honored by no backend); migrate arguments→options, retyped ``Optional[int]`` (Task 2 unify), then disposition (Task 3). |
| ``regexp_string_split`` | ``REGEXP_SPLIT`` | ``case_sensitivity`` | O-live | Emitted in ``node.options``; behaviour-test (Task 3). |
| ``regexp_string_split`` | ``REGEXP_SPLIT`` | ``dotall`` | O-absent | Substrait option absent from builder signature and ``node.options``; wire (Task 4). |
| ``regexp_string_split`` | ``REGEXP_SPLIT`` | ``multiline`` | O-absent | Substrait option absent from builder signature and ``node.options``; wire (Task 4). |
| ``regexp_strpos`` | ``REGEXP_STRPOS`` | ``case_sensitivity`` | O-live | Emitted in ``node.options``; behaviour-test (Task 3). |
| ``regexp_strpos`` | ``REGEXP_STRPOS`` | ``dotall`` | O-live | Emitted in ``node.options``; behaviour-test (Task 3). |
| ``regexp_strpos`` | ``REGEXP_STRPOS`` | ``multiline`` | O-live | Emitted in ``node.options``; behaviour-test (Task 3). |
| ``regexp_strpos`` | ``REGEXP_STRPOS`` | ``occurrence`` | O-live | Currently emitted in ``node.options``; behaviour-test (Task 3). |
| ``regexp_strpos`` | ``REGEXP_STRPOS`` | ``position`` | O-live | Currently emitted in ``node.options``; behaviour-test (Task 3). |
| ``replace`` | ``REPLACE`` | ``case_sensitivity`` | O-live | Emitted in ``node.options``; behaviour-test (Task 3). |
| ``starts_with`` | ``STARTS_WITH`` | ``case_sensitivity`` | O-live | Emitted in ``node.options``; behaviour-test (Task 3). |
| ``strpos`` | ``STRPOS`` | ``case_sensitivity`` | O-live | Emitted in ``node.options``; behaviour-test (Task 3). |
| ``substring`` | ``SUBSTRING`` | ``negative_start`` | O-absent | Substrait option absent from builder signature and ``node.options``; wire (Task 4). |
| ``swapcase`` | ``SWAPCASE`` | ``char_set`` | O-absent | Substrait option absent from builder signature and ``node.options``; wire (Task 4). |
| ``title`` | ``TITLE`` | ``char_set`` | O-absent | Substrait option absent from builder signature and ``node.options``; wire (Task 4). |
| ``upper`` | ``UPPER`` | ``char_set`` | O-absent | Substrait option absent from builder signature and ``node.options``; wire (Task 4). |

There are no N rows: the generated Substrait option source identifies every
registered parameter above as an option for its operation. In particular,
``char_set`` is not a no-op classification: it is a real option on the
case-conversion operations, but those builders do not yet emit it.

Channel unification (regexp ``position``/``occurrence``/``group``):
Empirical backend audit found no backend accepts a column-reference expression
for these knobs — they are universally literal-only, and honored by at most the
literal case (polars/ibis ``group`` via ``str.extract``/``re_extract``). Yet
``REGEXP_MATCH``/``REGEXP_MATCH_ALL``/``REGEXP_STRPOS``/``REGEXP_COUNT``/
``REGEXP_REPLACE`` place them inconsistently: on ``node.options`` for
MATCH_ALL/STRPOS/COUNT (raw ``Optional[int]``) but on ``arguments`` for
MATCH/REPLACE (expression-typed). The arguments placement is a phantom
capability that actively misbehaves: with no ``LITERAL_ONLY`` fact registered,
the visitor visits even a literal (``LiteralNode`` is an ``ExpressionNode``)
into a backend Expr, the backend ``isinstance(x, int)`` guard is then False,
and a user-supplied ``group`` silently collapses to 0. Per
``arguments-vs-options.md`` (universally-literal ⇒ MUST be an option), the five
``O-migrate`` rows above are moved arguments→options and retyped ``Optional[int]``
in Task 2 (a signature/channel change only — no ``CapabilityLevel.LITERAL_ONLY``
fact, which in the options channel would make the value-aware gate raise
unconditionally). After migration every regexp positional param is option-channel
and is dispositioned in Task 3 (honor where the native API takes a literal — e.g.
polars/ibis ``group`` — else a value-scoped ``UNSUPPORTED`` ``CapabilityFact``).
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any, NamedTuple

from expressions.argument_types._introspection import introspect_protocols
from expressions.argument_types._option_helpers import OptionSpec
from expressions.argument_types.conftest import ALL_BACKENDS
from mountainash.core.capabilities import CapabilityFact, CapabilityRegistry, WILDCARD_PARAM
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_api.api_builders.extensions_mountainash._ma_option_domains import (
    MA_OPTION_DOMAINS,
)
from mountainash.expressions.core.expression_api.api_builders.substrait._option_domains import (
    OPTION_DOMAINS,
)
from mountainash.expressions.core.expression_system.function_mapping.registry import (
    ExpressionFunctionRegistry,
)


CellKey = tuple[Any, str, str, str, str]
FactKey = tuple[Any, str, str, CONST_BACKEND, str | None]
InvalidRejectionKey = tuple[Any, str, str, str]


# Invalid strings form an infinite domain.  This one deliberately impossible
# value is the finite guard sentinel used to prove every activated option owner
# rejects invalid input at build time; it is not a claim about all bad strings.
INVALID_OPTION_VALUE = "INVALID"


class OptionCell(NamedTuple):
    fkey: Any
    protocol: str
    op: str
    param: str
    fixture: str
    value: str
    dtype: str
    disposition: str
    reason: str = ""
    backing_mode: str = "absence"



class OptionProbeRegistration(NamedTuple):
    """A role-specific OptionSpec bound to one concrete fixture dialect.

    Declared-unsupported probes describe the bounded exception produced by the
    ungated native path.  Their executor uses that metadata in a strict xfail,
    so native support self-heals as XPASS without accepting unrelated failures.
    """

    spec: OptionSpec
    fixture: str
    disposition: str
    expected_native_failure: (
        type[BaseException] | tuple[type[BaseException], ...] | None
    ) = None


class InvalidOptionRejection(NamedTuple):
    """One build-time invalid sentinel check for an option owner and dtype."""

    fkey: Any
    protocol: str
    op: str
    param: str
    value: str
    dtype: str
    build_expr: Callable[[], Any]


# Category modules append to these in PR-A/B/C.  A probe registration is the
# exact cell key exercised by an OptionSpec-backed discriminator test.
OPTION_DISPOSITIONS: list[OptionCell] = []
REGISTERED_OPTION_PROBES: list[OptionProbeRegistration] = []
REGISTERED_INVALID_OPTION_REJECTIONS: list[InvalidOptionRejection] = []
# Family defaults are real capability facts but have no fifth focused fixture
# cell. Category modules register their exact keys here for a separate guard.
OPTION_FAMILY_DEFAULT_FACT_KEYS: set[FactKey] = set()


# The option matrix uses the focused four-fixture argument-types surface from
# Task 4, not the broader nine-fixture repository execution registry.
_FIXTURE_IDENTITY: dict[str, tuple[CONST_BACKEND, str | None]] = {
    "polars": (CONST_BACKEND.POLARS, "polars"),
    "ibis": (CONST_BACKEND.IBIS, "ibis-duckdb"),
    "narwhals-polars": (CONST_BACKEND.NARWHALS, "narwhals-polars"),
    "narwhals-pandas": (CONST_BACKEND.NARWHALS, "narwhals-pandas"),
}


# Representative dtypes that expose each pinned arithmetic option's behavior.
# Unknown option kinds have no fallback: when a later pinned domain is drained,
# its PR must state applicable dtypes explicitly or expectation generation fails.
OPTION_DTYPES: dict[tuple[str, str], tuple[str, ...]] = {
    ("abs", "overflow"): ("int8",),
    ("acos", "on_domain_error"): ("float64",),
    ("acos", "rounding"): ("float64",),
    ("acosh", "on_domain_error"): ("float64",),
    ("acosh", "rounding"): ("float64",),
    ("add", "overflow"): ("int8",),
    ("add", "rounding"): ("float64",),
    ("asin", "on_domain_error"): ("float64",),
    ("asin", "rounding"): ("float64",),
    ("asinh", "rounding"): ("float64",),
    ("atan", "rounding"): ("float64",),
    ("atan2", "on_domain_error"): ("float64",),
    ("atan2", "rounding"): ("float64",),
    ("atanh", "on_domain_error"): ("float64",),
    ("atanh", "rounding"): ("float64",),
    ("capitalize", "char_set"): ("str",),
    ("center", "padding"): ("str",),
    ("concat", "null_handling"): ("str",),
    ("substring", "negative_start"): ("str",),
    ("initcap", "char_set"): ("str",),
    ("lower", "char_set"): ("str",),
    ("swapcase", "char_set"): ("str",),
    ("title", "char_set"): ("str",),
    ("upper", "char_set"): ("str",),
    ("cos", "rounding"): ("float64",),
    ("cosh", "rounding"): ("float64",),
    ("contains", "case_sensitivity"): ("str",),
    ("count_substring", "case_sensitivity"): ("str",),
    ("degrees", "rounding"): ("float64",),
    ("divide", "on_division_by_zero"): ("float64",),
    ("divide", "on_domain_error"): ("float64",),
    ("divide", "overflow"): ("int8",),
    ("divide", "rounding"): ("float64",),
    ("exp", "rounding"): ("float64",),
    ("ends_with", "case_sensitivity"): ("str",),
    ("factorial", "overflow"): ("int8",),
    ("like", "case_sensitivity"): ("str",),
    ("modulus", "division_type"): ("int64",),
    ("modulus", "on_domain_error"): ("int64",),
    ("modulus", "overflow"): ("int8",),
    ("multiply", "overflow"): ("int8",),
    ("multiply", "rounding"): ("float64",),
    ("negate", "overflow"): ("int8",),
    ("power", "overflow"): ("int64",),
    ("radians", "rounding"): ("float64",),
    ("replace", "case_sensitivity"): ("str",),
    ("regexp_count_substring", "case_sensitivity"): ("str",),
    ("regexp_count_substring", "dotall"): ("str",),
    ("regexp_count_substring", "multiline"): ("str",),
    ("regexp_match_substring", "case_sensitivity"): ("str",),
    ("regexp_match_substring", "dotall"): ("str",),
    ("regexp_match_substring", "multiline"): ("str",),
    ("regexp_match_substring_all", "case_sensitivity"): ("str",),
    ("regexp_match_substring_all", "dotall"): ("str",),
    ("regexp_match_substring_all", "multiline"): ("str",),
    ("regexp_replace", "case_sensitivity"): ("str",),
    ("regexp_replace", "dotall"): ("str",),
    ("regexp_replace", "multiline"): ("str",),
    ("regexp_string_split", "case_sensitivity"): ("str",),
    ("regexp_string_split", "dotall"): ("str",),
    ("regexp_string_split", "multiline"): ("str",),
    ("regexp_strpos", "case_sensitivity"): ("str",),
    ("regexp_strpos", "dotall"): ("str",),
    ("regexp_strpos", "multiline"): ("str",),
    # Regexp positional int options operate on string data columns, so the
    # representative dtype is the operand dtype ("str"), NOT the option's own
    # integer value type. The int value domain lives in OPTION_VALUE_DOMAINS.
    ("regexp_count_substring", "position"): ("str",),
    ("regexp_match_substring", "group"): ("str",),
    ("regexp_match_substring", "occurrence"): ("str",),
    ("regexp_match_substring", "position"): ("str",),
    ("regexp_match_substring_all", "group"): ("str",),
    ("regexp_match_substring_all", "position"): ("str",),
    ("regexp_replace", "occurrence"): ("str",),
    ("regexp_replace", "position"): ("str",),
    ("regexp_strpos", "occurrence"): ("str",),
    ("regexp_strpos", "position"): ("str",),
    ("sin", "rounding"): ("float64",),
    ("sinh", "rounding"): ("float64",),
    ("sqrt", "on_domain_error"): ("float64",),
    ("sqrt", "rounding"): ("float64",),
    ("starts_with", "case_sensitivity"): ("str",),
    ("strpos", "case_sensitivity"): ("str",),
    ("subtract", "overflow"): ("int8",),
    ("subtract", "rounding"): ("float64",),
    ("tan", "rounding"): ("float64",),
    ("tanh", "rounding"): ("float64",),
    # Datetime MA-extension unit options. The operand column dtype is the
    # Frictionless "datetime" string (mapping to MountainashDtype.TIMESTAMP).
    ("truncate", "unit"): ("datetime",),
    ("round_dt", "unit"): ("datetime",),
    ("ceil_dt", "unit"): ("datetime",),
    ("floor_dt", "unit"): ("datetime",),
    # Substrait round_temporal/round_calendar (item 74) — shared 9-unit
    # closed domain lives in OPTION_DOMAINS.
    ("round_temporal", "unit"): ("datetime",),
    ("round_temporal", "rounding"): ("float64",),
    ("round_calendar", "unit"): ("datetime",),
    ("round_calendar", "rounding"): ("float64",),
    # Datetime open-value options.
    ("assume_timezone", "timezone"): ("datetime",),
    ("to_timezone", "timezone"): ("datetime",),
    ("is_dst", "timezone"): ("datetime",),
    ("local_timestamp", "timezone"): ("datetime",),
    ("offset_by", "offset"): ("datetime",),
    ("strftime", "format"): ("datetime",),
    # Strptime format string — open-domain, no INVALID cell.
    # OPTION_DTYPES carries the input column dtype (str), not the option's own type.
    ("strptime_date", "format"): ("str",),
    ("strptime_timestamp", "format"): ("str",),
    ("strptime_timestamp", "timezone"): ("str",),
    # Datetime extraction (item 62): closed component/indexing domains and
    # open IANA-timezone value class operate on the datetime operand column.
    ("extract", "component"): ("datetime",),
    ("extract", "indexing"): ("datetime",),
    ("extract", "timezone"): ("datetime",),
    ("extract_boolean", "component"): ("datetime",),
    ("extract_boolean", "timezone"): ("datetime",),
}

# Representative legal values for open-integer options that have NO finite
# enum domain in the production OPTION_DOMAINS (position/occurrence/group are
# validated by _require_int_option, not validate_option). This is test-only,
# mirroring OPTION_DTYPES: the production domain map must stay truthful (an open
# int has no enumerable legal set), so we supply a single representative value
# for expected-cell expansion here rather than polluting _option_domains.py.
# Value-scoped facts document/gate this representative (mirroring how enum
# options enumerate their full domain); gating every possible integer would
# require value-wildcard facts and is tracked as a backlog enhancement.
OPTION_VALUE_DOMAINS: dict[tuple[str, str], tuple[str, ...]] = {
    ("regexp_count_substring", "position"): ("2",),
    ("regexp_match_substring", "group"): ("2",),
    ("regexp_match_substring", "occurrence"): ("2",),
    ("regexp_match_substring", "position"): ("2",),
    ("regexp_match_substring_all", "group"): ("2",),
    ("regexp_match_substring_all", "position"): ("2",),
    ("regexp_replace", "occurrence"): ("2",),
    ("regexp_replace", "position"): ("2",),
    ("regexp_strpos", "occurrence"): ("2",),
    ("regexp_strpos", "position"): ("2",),
}

# Representative legal values for open-string and value-class option params.
_MA_OPTION_VALUE_DOMAINS: dict[tuple[str, str], tuple[str, ...]] = {
    ("assume_timezone", "timezone"): ("UTC", "Australia/Sydney", "America/New_York"),
    ("to_timezone", "timezone"): ("UTC", "Australia/Sydney", "America/New_York"),
    ("is_dst", "timezone"): ("UTC", "Australia/Sydney", "America/New_York"),
    ("local_timestamp", "timezone"): ("UTC", "Australia/Sydney", "America/New_York"),
    ("offset_by", "offset"): ("1d", "-3mo", "2h30m"),
    ("strftime", "format"): ("%Y-%m-%d", "%H:%M:%S"),
    ("truncate", "unit"): ("2d", "3h"),
    ("round_dt", "unit"): ("2d", "3h"),
    ("ceil_dt", "unit"): ("2d", "3h"),
    ("floor_dt", "unit"): ("2d", "3h"),
    # Strptime format representatives — two that both parse the same input cleanly
    # and disagree on the result, so the probe discriminates without depending on
    # a parse error. %Y-%m-%d orders the date canonically; %Y-%d-%m swaps day/month
    # so the result differs when input has day > 12.
    ("strptime_date", "format"): ("%Y-%m-%d", "%Y-%d-%m"),
    ("strptime_timestamp", "format"): ("%Y-%m-%d %H:%M:%S", "%Y-%d-%m %H:%M:%S"),
    # IANA-timezone value class on extract / extract_boolean (item 62).
    ("extract", "timezone"): ("UTC", "Australia/Sydney", "America/New_York"),
    ("extract_boolean", "timezone"): ("UTC", "Australia/Sydney", "America/New_York"),
    ("strptime_timestamp", "timezone"): ("UTC", "Australia/Sydney", "America/New_York"),
}


class OpenDomainOptionSpec(NamedTuple):
    """An open-domain option param exempt from INVALID sentinel generation."""

    protocol: str
    op: str
    param: str
    since: str
    rationale: str


_OPEN_DOMAIN_OPTIONS: dict[tuple[str, str, str], OpenDomainOptionSpec] = {
    ("SubstraitScalarDatetimeExpressionSystemProtocol", "strftime", "format"): OpenDomainOptionSpec(
        protocol="SubstraitScalarDatetimeExpressionSystemProtocol",
        op="strftime",
        param="format",
        since="2026-07-27",
        rationale=(
            "strftime format string is unvalidated open-domain string; "
            "no invalid cell or build rejection expected"
        ),
    ),
    ("SubstraitScalarDatetimeExpressionSystemProtocol", "strptime_date", "format"): OpenDomainOptionSpec(
        protocol="SubstraitScalarDatetimeExpressionSystemProtocol",
        op="strptime_date",
        param="format",
        since="2026-07-30",
        rationale=(
            "strptime format string is an unvalidated open-domain string; "
            "no invalid cell or build rejection expected"
        ),
    ),
    ("SubstraitScalarDatetimeExpressionSystemProtocol", "strptime_timestamp", "format"): OpenDomainOptionSpec(
        protocol="SubstraitScalarDatetimeExpressionSystemProtocol",
        op="strptime_timestamp",
        param="format",
        since="2026-07-30",
        rationale=(
            "strptime format string is an unvalidated open-domain string; "
            "no invalid cell or build rejection expected"
        ),
    ),
}

# The four sources must be pairwise disjoint, EXCEPT for the unit keys on
# (MA_OPTION_DOMAINS, _MA_OPTION_VALUE_DOMAINS) which legitimately carry both
# finite units and multiplier representatives.
_FOUR_UNIT_KEYS = {
    ("truncate", "unit"),
    ("round_dt", "unit"),
    ("ceil_dt", "unit"),
    ("floor_dt", "unit"),
}

_all_domain_sources = (
    ("OPTION_DOMAINS", OPTION_DOMAINS),
    ("MA_OPTION_DOMAINS", MA_OPTION_DOMAINS),
    ("OPTION_VALUE_DOMAINS", OPTION_VALUE_DOMAINS),
    ("_MA_OPTION_VALUE_DOMAINS", _MA_OPTION_VALUE_DOMAINS),
)

for i in range(len(_all_domain_sources)):
    for j in range(i + 1, len(_all_domain_sources)):
        left_name, left_src = _all_domain_sources[i]
        right_name, right_src = _all_domain_sources[j]
        overlap = set(left_src) & set(right_src)
        if {left_name, right_name} == {"MA_OPTION_DOMAINS", "_MA_OPTION_VALUE_DOMAINS"}:
            overlap = overlap - _FOUR_UNIT_KEYS
        if overlap:
            raise AssertionError(
                f"option params in both {left_name} and {right_name}: {sorted(overlap)}"
            )

from mountainash.core.capabilities.value_classes import matches, ValueClass

for unit_key in _FOUR_UNIT_KEYS:
    finite_vals = MA_OPTION_DOMAINS[unit_key]
    mult_vals = _MA_OPTION_VALUE_DOMAINS[unit_key]
    for v in finite_vals:
        if matches(ValueClass.DURATION_MULTIPLIER, v):
            raise AssertionError(
                f"finite unit value {v!r} unexpectedly matches DURATION_MULTIPLIER"
            )
    for v in mult_vals:
        if v in finite_vals:
            raise AssertionError(
                f"multiplier unit representative {v!r} found in finite domain {finite_vals!r}"
            )



_CELL_DISPOSITIONS = frozenset(
    {"honored", "declared_unsupported", "probe_exempt", "invalid"}
)
_PROBE_DISPOSITIONS = frozenset(
    {"honored", "declared_unsupported", "probe_exempt"}
)


# Lazy to avoid a circular import when Task 6 makes the coverage guard consume
# param_taxonomy().  Tests may replace this dict to exercise expectation logic.
_KNOWN_UNTESTED_OPTION_PARAMS: dict[tuple[str, str, str], Any] | None = None


def _known_untested_option_params() -> dict[tuple[str, str, str], Any]:
    if _KNOWN_UNTESTED_OPTION_PARAMS is not None:
        return _KNOWN_UNTESTED_OPTION_PARAMS
    from expressions.argument_types.test_coverage_guard import (
        _KNOWN_UNTESTED_OPTION_PARAMS as known,
    )

    return known


def canonical_operation_name(fkey: Any) -> str:
    """Return the protocol method name for an actual FKEY enum member."""
    method = ExpressionFunctionRegistry.get(fkey).protocol_method
    if method is None:
        raise AssertionError(f"{fkey!r} has no registered protocol method")
    return method.__name__


def _fkey_index() -> dict[tuple[str, str], Any]:
    index: dict[tuple[str, str], Any] = {}
    for fkey in ExpressionFunctionRegistry.list_all():
        definition = ExpressionFunctionRegistry.get(fkey)
        method = definition.protocol_method
        # OPTION_DOMAINS is pinned from Substrait extension YAML.  Mountainash
        # convenience aliases may intentionally reuse a Substrait method (for
        # example RANK_AVERAGE -> rank) and are not domain owners; their
        # protocol_method lives in a Substrait-named class and is skipped
        # below. Real Mountainash domain owners (for example the datetime
        # ``truncate``/``round_dt``/``ceil_dt``/``floor_dt`` keys wired to
        # ``MountainAshScalarDatetimeExpressionSystemProtocol``) carry a
        # protocol_method in a ``MountainAsh*`` class and ARE included in
        # the index — otherwise the disposition guard cannot resolve their
        # (protocol, op_name) tuple to a fkey.
        if method is None:
            continue
        if definition.is_extension and "MountainAsh" not in method.__qualname__:
            continue
        protocol = method.__qualname__.rsplit(".", 1)[0]
        key = (protocol, method.__name__)
        previous = index.setdefault(key, fkey)
        if previous is not fkey:
            raise AssertionError(
                f"multiple FKEYs resolve to canonical protocol operation {key}: "
                f"{previous!r}, {fkey!r}"
            )
    return index


def cell_key(cell: OptionCell) -> CellKey:
    """Normalize a disposition without collapsing fixture dialects."""
    canonical_op = canonical_operation_name(cell.fkey)
    if cell.op != canonical_op:
        raise AssertionError(
            f"OptionCell op {cell.op!r} does not match {cell.fkey!r} canonical "
            f"protocol method {canonical_op!r}"
        )
    if cell.fixture not in _FIXTURE_IDENTITY:
        raise AssertionError(f"unknown option fixture {cell.fixture!r}")
    return (cell.fkey, cell.param, cell.fixture, cell.value, cell.dtype)


def probe_key(probe: OptionProbeRegistration) -> CellKey:
    """Normalize an actual OptionSpec registration to its disposition cell."""
    if probe.fixture not in _FIXTURE_IDENTITY:
        raise AssertionError(f"unknown option probe fixture {probe.fixture!r}")
    canonical_operation_name(probe.spec.fkey)
    return (
        probe.spec.fkey,
        probe.spec.option_param,
        probe.fixture,
        probe.spec.option_value,
        probe.spec.dtype,
    )


def invalid_rejection_key(rejection: InvalidOptionRejection) -> InvalidRejectionKey:
    """Normalize a pre-backend rejection without inventing a fixture axis."""
    canonical_op = canonical_operation_name(rejection.fkey)
    if rejection.op != canonical_op:
        raise AssertionError(
            f"invalid rejection op {rejection.op!r} does not match "
            f"{rejection.fkey!r} canonical protocol method {canonical_op!r}"
        )
    if rejection.value != INVALID_OPTION_VALUE:
        raise AssertionError(
            f"invalid rejection must use canonical sentinel "
            f"{INVALID_OPTION_VALUE!r}, got {rejection.value!r}"
        )
    return (rejection.fkey, rejection.param, rejection.value, rejection.dtype)


def validate_option_matrix_coverage() -> None:
    """Require exact expected/disposition equality, including invalid cells."""
    expected = expected_option_cells()
    dispositioned = {cell_key(cell) for cell in OPTION_DISPOSITIONS}
    if dispositioned != expected:
        raise AssertionError(
            f"option cell coverage mismatch: missing={expected - dispositioned}; "
            f"extra={dispositioned - expected}"
        )


def validate_option_probe_registration(probe: OptionProbeRegistration) -> None:
    """Reject ambiguous probe roles and unbounded declared native failures."""
    if probe.disposition not in _PROBE_DISPOSITIONS:
        raise AssertionError(
            f"invalid option probe disposition {probe.disposition!r}; "
            f"allowed: {sorted(_PROBE_DISPOSITIONS)}"
        )
    probe_key(probe)
    failure = probe.expected_native_failure
    intended_exception = probe.spec.expected_native_exception
    if intended_exception is not None and (
        not isinstance(intended_exception, type)
        or not issubclass(intended_exception, BaseException)
        or intended_exception in {BaseException, Exception, AssertionError}
    ):
        raise AssertionError(
            "expected_native_exception requires a specific intended exception"
        )
    if probe.disposition in {"honored", "probe_exempt"}:
        if failure is not None:
            raise AssertionError(
                f"{probe.disposition} probe cannot set expected_native_failure"
            )
        if probe.disposition == "honored" and intended_exception is not None:
            raise AssertionError(
                "intended native exceptions must use the probe_exempt role"
            )
        if (
            probe.disposition == "probe_exempt"
            and intended_exception is None
            and probe.spec.expected_discriminates
        ):
            raise AssertionError(
                "result-equivalent probe_exempt requires "
                "expected_discriminates=False"
            )
        return
    if intended_exception is not None:
        raise AssertionError(
            "declared_unsupported probe cannot set expected_native_exception"
        )
    failures = failure if isinstance(failure, tuple) else (failure,)
    if not failures or any(
        item is None or not isinstance(item, type) or not issubclass(item, BaseException)
        for item in failures
    ):
        raise AssertionError(
            "declared_unsupported probe requires a bounded expected_native_failure"
        )
    broad_failures = {BaseException, Exception, AssertionError}
    if any(item in broad_failures for item in failures):
        raise AssertionError(
            "declared_unsupported probe requires a specific native exception, "
            "not BaseException, Exception, or AssertionError"
        )


def validate_option_registries() -> None:
    """Validate labels and uniqueness before integrity guards form sets."""
    invalid_cells = [
        cell for cell in OPTION_DISPOSITIONS if cell.disposition not in _CELL_DISPOSITIONS
    ]
    if invalid_cells:
        raise AssertionError(
            f"invalid option disposition(s): {invalid_cells}; "
            f"allowed: {sorted(_CELL_DISPOSITIONS)}"
        )
    cell_keys = [cell_key(cell) for cell in OPTION_DISPOSITIONS]
    if len(cell_keys) != len(set(cell_keys)):
        raise AssertionError("duplicate option disposition cell key")

    for probe in REGISTERED_OPTION_PROBES:
        validate_option_probe_registration(probe)
    probe_keys = [probe_key(probe) for probe in REGISTERED_OPTION_PROBES]
    if len(probe_keys) != len(set(probe_keys)):
        raise AssertionError("duplicate option probe cell key")

    rejection_keys = [
        invalid_rejection_key(rejection)
        for rejection in REGISTERED_INVALID_OPTION_REJECTIONS
    ]
    if len(rejection_keys) != len(set(rejection_keys)):
        raise AssertionError("duplicate invalid option rejection key")
    invalid_cell_owners = {
        (cell.fkey, cell.param, cell.value, cell.dtype)
        for cell in OPTION_DISPOSITIONS
        if cell.disposition == "invalid"
    }
    rejection_owners = set(rejection_keys)
    if invalid_cell_owners != rejection_owners:
        raise AssertionError(
            "invalid rejection/cell mismatch: "
            f"rejections-only={rejection_owners - invalid_cell_owners}; "
            f"cells-only={invalid_cell_owners - rejection_owners}"
        )

    for role in _PROBE_DISPOSITIONS:
        cells_for_role = {
            cell_key(cell)
            for cell in OPTION_DISPOSITIONS
            if cell.disposition == role
        }
        probes_for_role = {
            probe_key(probe)
            for probe in REGISTERED_OPTION_PROBES
            if probe.disposition == role
        }
        if cells_for_role != probes_for_role:
            raise AssertionError(
                f"{role} probe/cell mismatch: "
                f"probes-only={probes_for_role - cells_for_role}; "
                f"cells-only={cells_for_role - probes_for_role}"
            )

    _ALLOWED_BACKING_MODES = {"class", "exact-fallback", "absence", "op-level"}
    invalid_backing_modes = [
        cell for cell in OPTION_DISPOSITIONS if cell.backing_mode not in _ALLOWED_BACKING_MODES
    ]
    if invalid_backing_modes:
        raise AssertionError(
            f"invalid option cell backing_mode(s): {invalid_backing_modes}; "
            f"allowed: {sorted(_ALLOWED_BACKING_MODES)}"
        )

    # Open-domain options registry validation (design-review round-2 I-4)
    active_identities = {
        (p.protocol_name, p.op_name, p.param_name): (p.op_name, p.param_name)
        for p in introspect_protocols()
        if p.kind == "option"
    }
    for key, spec in _OPEN_DOMAIN_OPTIONS.items():
        if key not in active_identities:
            raise AssertionError(
                f"open-domain option spec {key} is not an active introspected option"
            )
        op_param = active_identities[key]
        if (
            op_param not in OPTION_DOMAINS
            and op_param not in MA_OPTION_DOMAINS
            and op_param not in OPTION_VALUE_DOMAINS
            and op_param not in _MA_OPTION_VALUE_DOMAINS
        ):
            raise AssertionError(
                f"open-domain option spec {key} has no registered value domain"
            )


def cell_fact_key(cell: OptionCell) -> FactKey:
    """Map a per-fixture cell to the five-axis capability fact identity."""
    cell_key(cell)  # validate the FKEY/op and fixture invariants first
    family, dialect = _FIXTURE_IDENTITY[cell.fixture]
    return (cell.fkey, cell.param, cell.value, family, dialect)


def fact_key(fact: CapabilityFact) -> FactKey:
    """Normalize a value-scoped fact in the same order as cell_fact_key."""
    if fact.option_value is None:
        raise AssertionError(f"fact is not option-value scoped: {fact}")
    return (
        fact.operation_key,
        fact.param,
        fact.option_value,
        fact.backend,
        fact.dialect,
    )


def resolve_cell_fact(cell: OptionCell) -> CapabilityFact | None:
    """Resolve only an exact fixture/dialect fact, never a family fallback."""
    key = cell_fact_key(cell)
    return next(
        (
            fact
            for fact in CapabilityRegistry.facts()
            if fact.option_value is not None and fact_key(fact) == key
        ),
        None,
    )


def resolve_cell_class_fact(cell: OptionCell) -> CapabilityFact | None:
    """Resolve a cell's fact via CapabilityRegistry.capability_for matching a value_class."""
    family, dialect = _FIXTURE_IDENTITY[cell.fixture]
    fact = CapabilityRegistry.capability_for(
        cell.fkey,
        cell.param,
        family,
        dialect,
        option_value=cell.value,
    )
    if fact is not None and fact.value_class is not None:
        return fact
    return None


def resolve_cell_op_level_fact(cell: OptionCell) -> CapabilityFact | None:
    """Resolve a cell to the whole-op WILDCARD_PARAM fact that gates it.

    Open-domain options (an unvalidated format string) admit no ValueClass and
    no exhaustive exact-value enumeration, so the only sound declaration for a
    backend that cannot run the op at all is a value-agnostic whole-op fact.

    Delegates to the registry rather than scanning facts(): capability_for
    already walks dialect-scoped before family-default
    (registry.py:295-299), so a family default can never shadow a dialect
    refinement.  A hand-rolled scan resolves in registration order, which is
    the wrong answer the moment PR-C registers both scopes for one op.
    """
    family, dialect = _FIXTURE_IDENTITY[cell.fixture]
    fact = CapabilityRegistry.capability_for(
        cell.fkey, WILDCARD_PARAM, family, dialect
    )
    if fact is None or fact.param != WILDCARD_PARAM:
        return None
    if fact.value_class is not None or fact.option_value is not None:
        return None
    return fact


def param_taxonomy(protocol: str, op: str, param: str) -> str:
    """Derive the six-class parameter summary using the specified precedence."""
    cells = [
        cell
        for cell in OPTION_DISPOSITIONS
        if (cell.protocol, cell.op, cell.param) == (protocol, op, param)
    ]
    if not cells:
        return "no-op"
    legal = [cell for cell in cells if cell.disposition != "invalid"]
    if not legal:
        return "validation-only"
    if all(cell.disposition == "probe_exempt" for cell in legal):
        return "probe-exempt-honor"
    if any(
        cell.disposition in {"honored", "probe_exempt"}
        and cell.reason == "intended-error-path"
        for cell in legal
    ):
        return "error-sensitive"
    if any(cell.disposition in {"honored", "probe_exempt"} for cell in legal):
        return "value-sensitive"
    return "capability-declared"


def expected_option_cells() -> set[CellKey]:
    """Expand every activated option into legal values plus one invalid sentinel.

    Scope is introspected-total minus only explicit known-gap reasons.  Neither
    dispositions, registered probes, existing facts, nor tested subsets can
    remove a parameter from this expectation.  ``INVALID`` is added separately
    from the pinned legal domain as a finite build-time guard representative;
    the matrix intentionally does not attempt to enumerate all invalid strings.
    """
    known = _known_untested_option_params()
    fkeys = _fkey_index()
    expected: set[CellKey] = set()
    for protocol_param in introspect_protocols():
        if protocol_param.kind != "option":
            continue
        identity = (
            protocol_param.protocol_name,
            protocol_param.op_name,
            protocol_param.param_name,
        )
        if identity in known:
            continue
        operation = (protocol_param.op_name, protocol_param.param_name)
        if operation in _FOUR_UNIT_KEYS:
            value_domain = (
                tuple(MA_OPTION_DOMAINS[operation])
                + _MA_OPTION_VALUE_DOMAINS[operation]
            )
        else:
            value_domain = (
                OPTION_DOMAINS.get(operation)
                or MA_OPTION_DOMAINS.get(operation)
                or OPTION_VALUE_DOMAINS.get(operation)
                or _MA_OPTION_VALUE_DOMAINS.get(operation)
            )
        if value_domain is None:
            raise AssertionError(
                f"unreasoned option param {identity} has no pinned value domain "
                "(OPTION_DOMAINS or OPTION_VALUE_DOMAINS)"
            )
        if operation not in OPTION_DTYPES:
            raise AssertionError(
                f"unreasoned option param {identity} has no applicable dtype declaration"
            )
        try:
            fkey = fkeys[(protocol_param.protocol_name, protocol_param.op_name)]
        except KeyError as exc:
            raise AssertionError(
                f"unreasoned option param {identity} has no canonical registered FKEY"
            ) from exc
        for fixture in ALL_BACKENDS:
            if fixture not in _FIXTURE_IDENTITY:
                raise AssertionError(f"ALL_BACKENDS contains unknown option fixture {fixture!r}")
            for value in value_domain:
                for dtype in OPTION_DTYPES[operation]:
                    expected.add(
                        (fkey, protocol_param.param_name, fixture, value, dtype)
                    )
            if identity not in _OPEN_DOMAIN_OPTIONS:
                for dtype in OPTION_DTYPES[operation]:
                    expected.add(
                        (
                            fkey,
                            protocol_param.param_name,
                            fixture,
                            INVALID_OPTION_VALUE,
                            dtype,
                        )
                    )
    return expected
