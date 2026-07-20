"""The CSV dialect routing tables and the declared facts stay in sync."""

from mountainash.core.capabilities import CapabilityRegistry, load_all_capability_declarations
from mountainash.relations.backends.relation_systems.resource_files import (
    _MAPPABLE_DIALECT_FIELDS,
    _NATIVE_SAFE_DIALECT_FIELDS,
)


def test_every_fallback_routed_field_is_declared():
    load_all_capability_declarations()

    fallback_fields = _MAPPABLE_DIALECT_FIELDS - _NATIVE_SAFE_DIALECT_FIELDS
    declared_conditions = {
        fact.condition
        for fact in CapabilityRegistry.facts(conditioned=True)
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
