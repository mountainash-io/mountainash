import pytest
from mountainash.core.capabilities.registry import CapabilityRegistry
from mountainash.core.capabilities.schema import CapabilityLevel, Boundary, Enforcement, WILDCARD_PARAM
from mountainash.core.constants import CONST_BACKEND
from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_MOUNTAINASH_REL
from tests.fixtures.capability_gating import identity_for, capability_gate


class TestIdentityFor:
    def test_declared_dialect(self):
        idn = identity_for("ibis-polars")
        assert idn.family is CONST_BACKEND.IBIS and idn.dialect == "ibis-polars"

    def test_unknown_dialect_keeps_family(self):
        idn = identity_for("narwhals-pyarrow")
        assert idn.family is CONST_BACKEND.NARWHALS and idn.dialect is None

    def test_unresolvable_raises(self):
        with pytest.raises(ValueError, match="cannot resolve backend family"):
            identity_for("totally-unknown")


class TestCapabilityGate:
    def test_returns_gate_build_unsupported(self):
        op = RKEY_MOUNTAINASH_REL["WITH_ROW_INDEX"]
        fact = capability_gate(op, CONST_BACKEND.IBIS, dialect="ibis-polars")
        assert fact and fact.level is CapabilityLevel.UNSUPPORTED
        assert fact.enforcement is Enforcement.GATE and fact.boundary is Boundary.BUILD

    def test_ignores_router_metadata(self):
        op = RKEY_MOUNTAINASH_REL["READ_RESOURCE"]  # UNSUPPORTED but ROUTER_METADATA
        assert capability_gate(op, CONST_BACKEND.POLARS) is None

    def test_none_when_no_fact(self):
        op = RKEY_MOUNTAINASH_REL["WITH_ROW_INDEX"]
        assert capability_gate(op, CONST_BACKEND.IBIS, dialect="ibis-duckdb") is None
