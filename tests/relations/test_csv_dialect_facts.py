"""The CSV dialect routing tables and the declared facts stay in sync."""

from mountainash.core.capabilities import (
    CapabilityRegistry,
    Enforcement,
    load_all_capability_declarations,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.relations.backends.relation_systems.resource_files import (
    _MAPPABLE_DIALECT_FIELDS,
    _NATIVE_SAFE_DIALECT_FIELDS,
)
from mountainash.relations.core.relation_system.relation_keys.enums import (
    RKEY_MOUNTAINASH_REL,
)


def test_every_fallback_routed_field_is_declared():
    load_all_capability_declarations()

    fallback_fields = _MAPPABLE_DIALECT_FIELDS - _NATIVE_SAFE_DIALECT_FIELDS
    declared_conditions = {
        fact.condition
        for fact in CapabilityRegistry.facts(enforcement=Enforcement.ROUTER_METADATA)
        if "dialect." in (fact.condition or "")
    }
    undeclared = {
        field
        for field in fallback_fields
        if not any(field in condition for condition in declared_conditions)
    }

    assert not undeclared, (
        f"CSV dialect fields routed to fallback but not declared as facts: {undeclared}"
    )


def test_escape_char_fact_declared_on_every_backend():
    """Every backend declares the escape-char routing limitation explicitly."""
    load_all_capability_declarations()

    for family in (CONST_BACKEND.POLARS, CONST_BACKEND.NARWHALS, CONST_BACKEND.IBIS):
        assert any(
            fact.operation_key is RKEY_MOUNTAINASH_REL.READ_RESOURCE
            and fact.param == "resource"
            and fact.backend is family
            and "escape_char" in (fact.condition or "")
            for fact in CapabilityRegistry.facts()
        ), f"Missing escape_char CapabilityFact for backend {family.value}"
