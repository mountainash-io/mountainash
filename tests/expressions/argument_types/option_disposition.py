"""Per-fixture disposition matrix for Substrait literal option values.

This is test infrastructure shared by the arithmetic, string, and datetime
option slices.  Expectations come from protocol introspection and named gaps;
the disposition and probe registries are outputs checked against that scope,
never inputs used to shrink it.
"""
from __future__ import annotations

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
    """An OptionSpec discriminator bound to one concrete fixture dialect."""

    spec: OptionSpec
    fixture: str


# Category modules append to these in PR-A/B/C.  A probe registration is the
# exact cell key exercised by an OptionSpec-backed discriminator test.
OPTION_DISPOSITIONS: list[OptionCell] = []
REGISTERED_OPTION_PROBES: list[OptionProbeRegistration] = []


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
OPTION_DTYPES: dict[tuple[str, str], frozenset[str]] = {
    key: (
        frozenset({"int8"})
        if key[1] == "overflow"
        else frozenset({"int64"})
        if key[1] == "division_type"
        else frozenset({"float64"})
    )
    for key in OPTION_DOMAINS
}


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
    """Expand every unreasoned option param into domain × dtype × fixture.

    Scope is introspected-total minus only explicit known-gap reasons.  Neither
    dispositions, registered probes, existing facts, nor tested subsets can
    remove a parameter from this expectation.
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
    return expected
