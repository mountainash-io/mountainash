"""Per-fixture disposition matrix for Substrait literal option values.

This is test infrastructure shared by the arithmetic, string, and datetime
option slices.  Expectations come from protocol introspection and named gaps;
the disposition and probe registries are outputs checked against that scope,
never inputs used to shrink it.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any, NamedTuple

from expressions.argument_types._introspection import introspect_protocols
from expressions.argument_types._option_helpers import OptionSpec
from expressions.argument_types.conftest import ALL_BACKENDS
from mountainash.core.capabilities import CapabilityFact, CapabilityRegistry
from mountainash.core.constants import CONST_BACKEND
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


# The option matrix uses the focused four-fixture argument-types surface from
# Task 4, not the broader nine-fixture repository execution registry.
_FIXTURE_IDENTITY: dict[str, tuple[CONST_BACKEND, str | None]] = {
    "polars": (CONST_BACKEND.POLARS, "polars"),
    "ibis": (CONST_BACKEND.IBIS, None),
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
    ("cos", "rounding"): ("float64",),
    ("cosh", "rounding"): ("float64",),
    ("degrees", "rounding"): ("float64",),
    ("divide", "on_division_by_zero"): ("float64",),
    ("divide", "on_domain_error"): ("float64",),
    ("divide", "overflow"): ("int8",),
    ("divide", "rounding"): ("float64",),
    ("exp", "rounding"): ("float64",),
    ("factorial", "overflow"): ("int8",),
    ("modulus", "division_type"): ("int64",),
    ("modulus", "on_domain_error"): ("int64",),
    ("modulus", "overflow"): ("int8",),
    ("multiply", "overflow"): ("int8",),
    ("multiply", "rounding"): ("float64",),
    ("negate", "overflow"): ("int8",),
    ("power", "overflow"): ("int64",),
    ("radians", "rounding"): ("float64",),
    ("sin", "rounding"): ("float64",),
    ("sinh", "rounding"): ("float64",),
    ("sqrt", "on_domain_error"): ("float64",),
    ("sqrt", "rounding"): ("float64",),
    ("subtract", "overflow"): ("int8",),
    ("subtract", "rounding"): ("float64",),
    ("tan", "rounding"): ("float64",),
    ("tanh", "rounding"): ("float64",),
}

_CELL_DISPOSITIONS = frozenset(
    {"honored", "declared_unsupported", "probe_exempt", "invalid"}
)
_PROBE_DISPOSITIONS = frozenset({"honored", "declared_unsupported"})


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
        # example RANK_AVERAGE -> rank) and are not domain owners.
        if method is None or definition.is_extension:
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
    if probe.disposition == "honored":
        if failure is not None:
            raise AssertionError("honored probe cannot set expected_native_failure")
        return
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


def param_taxonomy(protocol: str, op: str, param: str) -> str:
    """Derive the six-class parameter summary using the specified precedence."""
    cells = [
        cell
        for cell in OPTION_DISPOSITIONS
        if (cell.protocol, cell.op, cell.param) == (protocol, op, param)
    ]
    if not cells:
        return "no-op"
    dispositions = {cell.disposition for cell in cells}
    if dispositions == {"invalid"}:
        return "validation-only"
    if dispositions == {"declared_unsupported"}:
        return "capability-declared"
    if any(
        cell.disposition == "honored" and cell.reason == "intended-error-path"
        for cell in cells
    ):
        return "error-sensitive"
    if "honored" in dispositions:
        return "value-sensitive"
    if dispositions == {"probe_exempt"}:
        return "probe-exempt-honor"
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
        if operation not in OPTION_DOMAINS:
            raise AssertionError(
                f"unreasoned option param {identity} has no pinned OPTION_DOMAINS entry"
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
            for value in OPTION_DOMAINS[operation]:
                for dtype in OPTION_DTYPES[operation]:
                    expected.add(
                        (fkey, protocol_param.param_name, fixture, value, dtype)
                    )
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
