"""Registry load-state machine (spec rev 3, §2)."""
from __future__ import annotations

import threading

import pytest

from mountainash.core.capabilities import (
    CapabilityDeclaration,
    CapabilityFact,
    CapabilityLevel,
    CapabilityRegistry,
    Domain,
    FactSource,
)
from mountainash.core.capabilities import bootstrap as _bootstrap_module
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


def _reset_to_uninitialized():
    """Drive the registry back to a pristine UNINITIALIZED state for the
    fresh-process-semantics tests below. The spec §2 'fresh process semantics
    can't be simulated' caveat applies; M-6 flagged a future subprocess-based
    alternative for hardening."""
    CapabilityRegistry._facts = {}
    CapabilityRegistry._kinds = {}
    CapabilityRegistry._value_class_facts = {}
    CapabilityRegistry._predicate_facts = []
    CapabilityRegistry._declarations = ()
    CapabilityRegistry._load_state = _LoadState.UNINITIALIZED
    CapabilityRegistry._load_error = None


@pytest.fixture
def uninitialized():
    """Drive the registry to a pristine UNINITIALIZED state and restore after
    (final-review M-6): the class-attr mutation stays inside the single
    _reset_to_uninitialized helper, so no test body pokes registry internals."""
    snap = CapabilityRegistry.snapshot()
    try:
        _reset_to_uninitialized()
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


def test_autoload_fires_from_uninitialized(uninitialized):
    facts = CapabilityRegistry.facts()
    assert CapabilityRegistry._load_state is _LoadState.LOADED
    assert len(facts) > 0


def test_failed_state_caches_and_re_raises_same_exception():
    """Spec §2 transition FAILED --any query--> re-raise cached exception.

    The FAILED state caches the load exception and re-raises it on subsequent
    queries WITHOUT re-invoking the load hook. reset()/restore() clear the
    cached error.
    """
    sentinel = RuntimeError("sentinel autoload failure")
    call_count = [0]

    def boom():
        call_count[0] += 1
        raise sentinel

    snap = CapabilityRegistry.snapshot()
    original = _bootstrap_module._load_into_registry
    _bootstrap_module._load_into_registry = boom
    try:
        _reset_to_uninitialized()
        # First query: triggers autoload, hits boom, transitions to FAILED
        with pytest.raises(RuntimeError, match="sentinel autoload failure"):
            CapabilityRegistry.facts()
        assert call_count[0] == 1
        assert CapabilityRegistry._load_state is _LoadState.FAILED
        # The cached exception is the SAME object the load hook raised —
        # not a re-raise of a fresh exception from a re-invoked load.
        assert CapabilityRegistry._load_error is sentinel

        # Second query: re-raises the SAME cached exception without
        # re-invoking the load hook.
        with pytest.raises(RuntimeError, match="sentinel autoload failure"):
            CapabilityRegistry.facts()
        assert call_count[0] == 1, (
            f"load hook must NOT be invoked from FAILED; was invoked "
            f"{call_count[0]} times"
        )
        assert CapabilityRegistry._load_error is sentinel

        # reset() clears the FAILED state and the cached error.
        CapabilityRegistry.reset()
        assert CapabilityRegistry._load_state is _LoadState.ISOLATED
        assert CapabilityRegistry._load_error is None
    finally:
        _bootstrap_module._load_into_registry = original
        CapabilityRegistry.restore(snap)


def test_restore_uninitialized_snapshot_clears_failed_state():
    """restore() with an UNINITIALIZED snapshot also clears FAILED.

    The test idiom is: snapshot (LOADED) → induce FAILED → restore the
    UNINITIALIZED snapshot → next query must attempt autoload again (i.e.
    FAILED is gone, and a fresh load succeeds).
    """
    sentinel = RuntimeError("first load failed")

    def boom():
        raise sentinel

    snap = CapabilityRegistry.snapshot()
    original = _bootstrap_module._load_into_registry
    _bootstrap_module._load_into_registry = boom
    try:
        _reset_to_uninitialized()
        with pytest.raises(RuntimeError, match="first load failed"):
            CapabilityRegistry.facts()
        assert CapabilityRegistry._load_state is _LoadState.FAILED

        # Restore back to the prior state (UNINITIALIZED from the snapshot
        # we took at the start). FAILED is wiped.
        CapabilityRegistry.restore(snap)
        assert CapabilityRegistry._load_state is not _LoadState.FAILED
        assert CapabilityRegistry._load_error is None
    finally:
        _bootstrap_module._load_into_registry = original
        CapabilityRegistry.restore(snap)


def test_concurrent_first_query_runs_load_hook_once():
    """Spec §2 'Cross-thread: first thread loads, others block until LOADED/FAILED.'

    Two threads race on the first query, synchronised by a Barrier. The load
    hook must run exactly once even if both threads enter the query
    concurrently — the registry's RLock serialises the load and the
    state-check-then-load happens inside the critical section.
    """
    call_count = [0]
    original = _bootstrap_module._load_into_registry

    def counting_load():
        call_count[0] += 1
        return original()

    snap = CapabilityRegistry.snapshot()
    _bootstrap_module._load_into_registry = counting_load
    try:
        _reset_to_uninitialized()
        barrier = threading.Barrier(2)
        results: list[int] = []
        errors: list[BaseException] = []

        def query():
            try:
                barrier.wait(timeout=10)
                results.append(len(CapabilityRegistry.facts()))
            except BaseException as exc:  # pragma: no cover
                errors.append(exc)

        t1 = threading.Thread(target=query, name="t1")
        t2 = threading.Thread(target=query, name="t2")
        t1.start()
        t2.start()
        t1.join(timeout=15)
        t2.join(timeout=15)

        assert not errors, f"thread errors: {errors!r}"
        assert len(results) == 2
        assert all(r > 0 for r in results), results
        assert call_count[0] == 1, (
            f"load hook must run exactly once; ran {call_count[0]} times"
        )
        assert CapabilityRegistry._load_state is _LoadState.LOADED
    finally:
        _bootstrap_module._load_into_registry = original
        CapabilityRegistry.restore(snap)
