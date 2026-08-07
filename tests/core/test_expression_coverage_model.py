"""Model-level tests for the coverage module (synthetic + universe identity)."""
from __future__ import annotations

import enum as _enum
import inspect

from mountainash.core.capabilities.coverage import (
    _UNREGISTERED_OPS,
    OpRecord,
    audit_domain_for,
)
from mountainash.core.capabilities.declarations import Domain, FactSource


def _registered_universe() -> list[OpRecord]:
    from mountainash.expressions.core.expression_system.function_mapping.registry import (
        ExpressionFunctionRegistry,
    )
    from mountainash.relations.core.relation_system.relation_mapping.registry import (
        RelationOperationRegistry,
    )

    keys = list(ExpressionFunctionRegistry.list_all()) + list(
        RelationOperationRegistry.list_all()
    )
    return [OpRecord(k, type(k).__name__) for k in keys]


def _all_key_enum_members() -> list[tuple[str, str, object]]:
    """(class_name, member_name, member) for EVERY Enum class in the two key
    modules — module introspection, NOT prefix filtering (spec §3.1)."""
    from mountainash.expressions.core.expression_system.function_keys import enums as fk
    from mountainash.relations.core.relation_system.relation_keys import enums as rk

    out: list[tuple[str, str, object]] = []
    for module in (fk, rk):
        for name, cls in inspect.getmembers(module, inspect.isclass):
            if issubclass(cls, _enum.Enum) and cls.__module__ == module.__name__:
                out.extend((name, m.name, m) for m in cls)
    return out


def test_enum_members_registered_or_excepted():
    universe = {(r.family, r.operation_key.name) for r in _registered_universe()}
    excepted = {(u.family, u.member) for u in _UNREGISTERED_OPS}
    members = {(cls, name) for cls, name, _ in _all_key_enum_members()}

    unaccounted = members - universe - excepted
    assert not unaccounted, (
        f"enum members neither registered nor excepted: {sorted(unaccounted)}; "
        "register them or add a dated UnregisteredOp with a reason"
    )
    stale = excepted & universe
    assert not stale, f"_UNREGISTERED_OPS entries now registered — remove: {sorted(stale)}"
    phantom = excepted - members
    assert not phantom, f"_UNREGISTERED_OPS entries match no enum member: {sorted(phantom)}"


def test_unregistered_ops_governance():
    from datetime import date as _date

    seen: set[tuple[str, str]] = set()
    for u in _UNREGISTERED_OPS:
        assert (u.family, u.member) not in seen, f"duplicate exception {u}"
        seen.add((u.family, u.member))
        assert u.reason.strip(), f"empty reason on {u.family}.{u.member}"
        _date.fromisoformat(u.since)  # raises on impossible dates


def test_audit_domain_mirrors_validators():
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_SUBSTRAIT_SCALAR_SET,
        SUBSTRAIT_ARITHMETIC_WINDOW,
    )
    from mountainash.relations.core.relation_system.relation_keys.enums import (
        RKEY_MOUNTAINASH_REL,
    )

    op = next(iter(FKEY_SUBSTRAIT_SCALAR_SET))
    assert audit_domain_for(op) == (FactSource.SUBSTRAIT, Domain.SET)
    rel = next(iter(RKEY_MOUNTAINASH_REL))
    assert audit_domain_for(rel) == (FactSource.MOUNTAINASH, Domain.RELATION)
    legacy = next(iter(SUBSTRAIT_ARITHMETIC_WINDOW))
    assert audit_domain_for(legacy) is None  # unmapped family, not an error


def test_known_gaps_register_importable_and_typed():
    from mountainash.core.capabilities.gaps import KNOWN_GAPS
    from mountainash.core.capabilities.schema import KnownGap

    assert isinstance(KNOWN_GAPS, tuple)
    assert all(isinstance(g, KnownGap) for g in KNOWN_GAPS)
