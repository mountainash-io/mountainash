"""Registry load-state machine (spec rev 3, §2)."""
from __future__ import annotations

import pytest

from mountainash.core.capabilities import (
    CapabilityDeclaration,
    CapabilityFact,
    CapabilityLevel,
    CapabilityRegistry,
    Domain,
    FactSource,
)
from mountainash.core.capabilities.registry import _LoadState
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)


def _decl():
    return CapabilityDeclaration(
        backend=CONST_BACKEND.IBIS, domain=Domain.STRING,
        source=FactSource.SUBSTRAIT,
        facts=(CapabilityFact(
            operation_key=FK_STR.CENTER, param="length",
            level=CapabilityLevel.LITERAL_ONLY, backend=CONST_BACKEND.IBIS,
            message="t", since="2026-08-07", probe_exempt="test",
        ),),
    )


@pytest.fixture
def isolated():
    snap = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.reset()
        yield
    finally:
        CapabilityRegistry.restore(snap)


def test_reset_enters_isolated_and_disables_autoload(isolated):
    assert CapabilityRegistry._load_state is _LoadState.ISOLATED
    # a query in ISOLATED must NOT repopulate production facts
    assert CapabilityRegistry.facts() == []


def test_register_declaration_retains_declaration(isolated):
    d = _decl()
    CapabilityRegistry.register_declaration(d)
    assert d in CapabilityRegistry.declarations()
    assert len(CapabilityRegistry.facts()) == 1


def test_snapshot_restore_round_trips_state_and_declarations(isolated):
    CapabilityRegistry.register_declaration(_decl())
    snap = CapabilityRegistry.snapshot()
    CapabilityRegistry.reset()
    assert CapabilityRegistry.declarations() == ()
    CapabilityRegistry.restore(snap)
    assert len(CapabilityRegistry.declarations()) == 1
    assert CapabilityRegistry._load_state is _LoadState.ISOLATED


def test_load_all_raises_in_isolated(isolated):
    from mountainash.core.capabilities import load_all_capability_declarations
    with pytest.raises(RuntimeError, match="ISOLATED"):
        load_all_capability_declarations()


def test_autoload_fires_from_uninitialized():
    # Fresh-process semantics can't be simulated after conftest imports, so
    # drive the transition directly: restore a pristine UNINITIALIZED state.
    snap = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry._facts = {}
        CapabilityRegistry._kinds = {}
        CapabilityRegistry._value_class_facts = {}
        CapabilityRegistry._declarations = ()
        CapabilityRegistry._load_state = _LoadState.UNINITIALIZED
        CapabilityRegistry._load_error = None
        facts = CapabilityRegistry.facts()
        assert CapabilityRegistry._load_state is _LoadState.LOADED
        assert len(facts) > 0
    finally:
        CapabilityRegistry.restore(snap)
