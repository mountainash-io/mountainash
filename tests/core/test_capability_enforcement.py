"""Explicit enforcement role (backlog 66a, spec 2026-07-28)."""
import pytest

from mountainash.core.capabilities import (
    Boundary,
    CapabilityFact,
    CapabilityLevel,
    CapabilityRegistry,
    Enforcement,
)
from mountainash.core.capabilities.bootstrap import load_all_capability_declarations
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
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
    ("JOIN_ASOF", "tolerance", CONST_BACKEND.NARWHALS): Enforcement.GATE,
    ("READ_RESOURCE", "resource", CONST_BACKEND.POLARS): Enforcement.ROUTER_METADATA,
    ("READ_RESOURCE", "resource", CONST_BACKEND.IBIS): Enforcement.ROUTER_METADATA,
    ("READ_RESOURCE", "resource", CONST_BACKEND.NARWHALS): Enforcement.ROUTER_METADATA,
    ("T_IS_IN", "collection", CONST_BACKEND.NARWHALS): Enforcement.MATERIALIZE_RESIDUE,
    ("T_IS_NOT_IN", "collection", CONST_BACKEND.NARWHALS): Enforcement.MATERIALIZE_RESIDUE,
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
