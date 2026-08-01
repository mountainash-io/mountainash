"""Explicit enforcement role (backlog 66a, spec 2026-07-28)."""
import polars as pl
import pytest

import mountainash as ma
from mountainash.core.capabilities import (
    Boundary,
    CapabilityFact,
    CapabilityLevel,
    CapabilityRegistry,
    Enforcement,
    WILDCARD_PARAM,
)
from mountainash.core.capabilities.bootstrap import load_all_capability_declarations
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_CAST,
    FKEY_SUBSTRAIT_SCALAR_ARITHMETIC as FK_ARITH,
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)


@pytest.fixture(autouse=True, scope="module")
def _all_declarations_loaded():
    """`import mountainash` alone registers a fraction of the facts; the
    relation/datetime declaration modules load lazily. Querying the registry
    without this silently reads a partial registry and certifies everything."""
    load_all_capability_declarations()


def _fact(**kw):
    base = dict(
        operation_key=FK_STR.CONTAINS,
        param="substring",
        level=CapabilityLevel.UNSUPPORTED,
        backend=CONST_BACKEND.POLARS,
        message="test-fact",
        since="2026-07-28",
    )
    base.update(kw)
    return CapabilityFact(**base)


class TestEnforcementField:
    def test_defaults_to_gate(self):
        assert _fact().enforcement is Enforcement.GATE

    def test_default_is_gate_even_with_a_condition(self):
        """The whole point: prose no longer decides enforcement."""
        assert _fact(condition="only when x").enforcement is Enforcement.GATE


class TestCompatibilityTable:
    """enforcement x boundary: one legal boundary per role (plan decision 1)."""

    def test_gate_requires_build(self):
        with pytest.raises(ValueError, match="BUILD"):
            _fact(boundary=Boundary.MATERIALIZE, native_errors=(ValueError,))

    def test_router_metadata_requires_build(self):
        with pytest.raises(ValueError, match="BUILD"):
            _fact(
                enforcement=Enforcement.ROUTER_METADATA,
                boundary=Boundary.MATERIALIZE,
                native_errors=(ValueError,),
            )

    def test_materialize_residue_requires_materialize(self):
        with pytest.raises(ValueError, match="MATERIALIZE"):
            _fact(enforcement=Enforcement.MATERIALIZE_RESIDUE)

    def test_each_role_accepts_its_legal_boundary(self):
        assert _fact().boundary is Boundary.BUILD
        assert _fact(enforcement=Enforcement.ROUTER_METADATA).boundary is Boundary.BUILD
        assert (
            _fact(
                enforcement=Enforcement.MATERIALIZE_RESIDUE,
                boundary=Boundary.MATERIALIZE,
                native_errors=(ValueError,),
            ).enforcement
            is Enforcement.MATERIALIZE_RESIDUE
        )


EXPECTED_ROLES = {
    ("GET", "index", CONST_BACKEND.NARWHALS): Enforcement.MATERIALIZE_RESIDUE,
    ("JOIN_ASOF", "tolerance", CONST_BACKEND.NARWHALS): Enforcement.GATE,
    ("READ_RESOURCE", "resource", CONST_BACKEND.POLARS): Enforcement.ROUTER_METADATA,
    ("READ_RESOURCE", "resource", CONST_BACKEND.IBIS): Enforcement.ROUTER_METADATA,
    ("READ_RESOURCE", "resource", CONST_BACKEND.NARWHALS): Enforcement.ROUTER_METADATA,
}


class TestTreeFactsDeclareTheirRole:
    """Closed mapping: every fact carrying prose states its role, and no fact
    outside the mapping carries prose. A new conditioned fact fails here."""

    def test_conditioned_facts_match_the_expected_roles_exactly(self):
        actual = {
            (f.operation_key.name, f.param, f.backend): f.enforcement
            for f in CapabilityRegistry.facts(conditioned=True)
        }
        assert actual == EXPECTED_ROLES


GATE_DF = pl.DataFrame({"x": [-1, 2], "text": ["abc", "b"]})


@pytest.fixture
def isolated_registry():
    """Snapshot, RESET, restore — the idiom from test_option_value_facts.py:24.

    The reset is load-bearing, not hygiene. Production facts already declare
    ABS.overflow=ERROR UNSUPPORTED on polars at dialect="polars", which
    out-ranks a throwaway registered at dialect=None. Without the reset,
    test_option_value_gate_ignores_router_metadata still raises (from the
    production fact) after the implementation is correct, and the GATE-direction
    test passes for the wrong reason. Verified: after reset(), a plain
    `ma.col("x").abs()` still compiles, so the reset costs nothing.
    """
    snap = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.reset()
        yield
    finally:
        CapabilityRegistry.restore(snap)


def _register(**kw):
    CapabilityRegistry.register_backend(CONST_BACKEND.POLARS, [CapabilityFact(**kw)])


class TestNonGateFactsAreExcludedFromEveryGate:
    """The option-value gate and validate_plan_capabilities checked NOTHING
    before 66a, and the cast gate checked prose. A role-blind consumer raises
    on a ROUTER_METADATA fact; assert each one no longer does — and still does
    for GATE."""

    OPTION_FACT = dict(
        operation_key=FK_ARITH.ABS, param="overflow", option_value="ERROR",
        level=CapabilityLevel.UNSUPPORTED, backend=CONST_BACKEND.POLARS,
        message="test-fact: option gate", since="2026-07-28",
    )
    CAST_FACT = dict(
        operation_key=FKEY_SUBSTRAIT_CAST.CAST, param=WILDCARD_PARAM,
        level=CapabilityLevel.UNSUPPORTED, backend=CONST_BACKEND.POLARS,
        message="test-fact: cast gate", since="2026-07-28",
    )
    PLAN_FACT = dict(
        operation_key=FK_STR.CONTAINS, param=WILDCARD_PARAM,
        level=CapabilityLevel.UNSUPPORTED, backend=CONST_BACKEND.POLARS,
        message="test-fact: plan gate", since="2026-07-28",
    )

    def test_option_value_gate_ignores_router_metadata(self, isolated_registry):
        _register(**self.OPTION_FACT, enforcement=Enforcement.ROUTER_METADATA)
        assert ma.col("x").abs(overflow="ERROR").compile(GATE_DF) is not None

    def test_option_value_gate_still_raises_for_gate_facts(self, isolated_registry):
        _register(**self.OPTION_FACT)
        with pytest.raises(BackendCapabilityError):
            ma.col("x").abs(overflow="ERROR").compile(GATE_DF)

    def test_cast_gate_ignores_router_metadata(self, isolated_registry):
        _register(**self.CAST_FACT, enforcement=Enforcement.ROUTER_METADATA)
        assert ma.col("x").cast("i64").compile(GATE_DF) is not None

    def test_cast_gate_still_raises_for_gate_facts(self, isolated_registry):
        _register(**self.CAST_FACT)
        with pytest.raises(BackendCapabilityError):
            ma.col("x").cast("i64").compile(GATE_DF)

    def test_cast_gate_is_not_disabled_by_prose(self, isolated_registry):
        """The footgun on the cast path — verified live before this change."""
        _register(**self.CAST_FACT, condition="only sometimes")
        with pytest.raises(BackendCapabilityError):
            ma.col("x").cast("i64").compile(GATE_DF)

    def test_validate_plan_capabilities_ignores_router_metadata(self, isolated_registry):
        _register(**self.PLAN_FACT, enforcement=Enforcement.ROUTER_METADATA)
        assert CapabilityRegistry.validate_plan_capabilities(
            [FK_STR.CONTAINS], CONST_BACKEND.POLARS
        ) == []

    def test_validate_plan_capabilities_still_reports_gate_facts(self, isolated_registry):
        _register(**self.PLAN_FACT)
        assert CapabilityRegistry.validate_plan_capabilities(
            [FK_STR.CONTAINS], CONST_BACKEND.POLARS
        )
